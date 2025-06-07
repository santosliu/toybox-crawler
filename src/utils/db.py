import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv() # 從 .env 文件載入環境變數

def connect_to_db():
    """建立並返回資料庫連線"""
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        print("資料庫連線成功。")
        return mydb
    except mysql.connector.Error as err:
        print(f"資料庫連線失敗：{err}")
        return None

def insert_news(mydb, news_data):
    """將新聞資料插入資料庫"""
    mycursor = None
    inserted_id = None
    try:
        mycursor = mydb.cursor()
        # 檢查 news_data 是否包含 'status'，如果沒有則給予預設值 0
        status = news_data.get("status", 0)
        feature_picture = news_data.get("feature_picture", None) # 取得圖片路徑，預設為 None
        sql = "INSERT INTO news (source, language, url, article_title, article_content, status, feature_picture, links) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (news_data["source"], news_data["language"], news_data["url"], news_data["article_title"], news_data["article_content"], status, feature_picture, news_data["links"])
        mycursor.execute(sql, val)
        mydb.commit()
        inserted_id = mycursor.lastrowid # 取得插入的 ID
        print(f"已插入：{news_data['article_title']} (ID: {inserted_id})")
    except mysql.connector.Error as err:
        print(f"插入失敗 {news_data['article_title']}：{err}")
        mydb.rollback() # 插入失敗時回滾
    except Exception as e:
        print(f"插入新聞時發生未知錯誤：{e}")
        mydb.rollback()
    finally:
        if mycursor:
            mycursor.close() # 確保游標關閉
    return inserted_id # 返回插入的 ID 或 None

def check_url_exists(mydb, url):
    """檢查指定的 URL 是否已存在於資料庫中"""
    mycursor = None
    existing_news = None
    try:
        mycursor = mydb.cursor(dictionary=True) # 使用 dictionary cursor
        sql_check = "SELECT id FROM news WHERE url = %s"
        mycursor.execute(sql_check, (url,))
        existing_news = mycursor.fetchone()
    except mysql.connector.Error as err:
        print(f"檢查 URL {url} 時發生資料庫錯誤：{err}")
    except Exception as e:
        print(f"檢查 URL 時發生未知錯誤：{e}")
    finally:
        if mycursor:
            mycursor.close()
    return existing_news # 返回查詢結果 (字典或 None)

def get_editor_prompt(mydb, language):
    """從 editors 表隨機獲取一個啟用的編輯器設定"""
    mycursor = None
    editor_config = None
    try:
        mycursor = mydb.cursor(dictionary=True) # 使用 dictionary cursor
        # 隨機選取一個 is_deleted = 0 的編輯器
        sql = f"SELECT title_prompt, content_prompt, editor_name FROM editors WHERE language = '{language}' AND is_deleted = 0 ORDER BY RAND() LIMIT 1"
        print(sql) # 打印 SQL 查詢語句以便除錯
        mycursor.execute(sql)
        editor_config = mycursor.fetchone()
        if editor_config:
            print(f"成功從資料庫獲取編輯器設定: {editor_config.get('editor_name', '未知')}")
        else:
            print("在 editors 表中未找到啟用的編輯器設定。")
    except mysql.connector.Error as err:
        print(f"讀取 editors 時發生資料庫錯誤：{err}")
    except Exception as e:
        print(f"讀取 editors 時發生未知錯誤：{e}")
    finally:
        if mycursor:
            mycursor.close()
    return editor_config # 返回字典或 None

def get_news_to_translate(mydb, limit):
    """從 news 表獲取指定數量需要翻譯的文章"""
    mycursor = None
    results = []
    try:
        mycursor = mydb.cursor(dictionary=True) # 使用 dictionary cursor
        sql = """
            SELECT id, source, language, url, article_title, article_content, links
            FROM news
            WHERE status = 0 AND (translated_title IS NULL OR translated_content IS NULL OR translated_title = '' OR translated_content = '')
            ORDER BY id DESC
            LIMIT %s
        """
        mycursor.execute(sql, (limit,))
        results = mycursor.fetchall()
        print(f"找到 {len(results)} 篇待翻譯文章。")
    except mysql.connector.Error as err:
        print(f"讀取待翻譯新聞時發生資料庫錯誤：{err}")
    except Exception as e:
        print(f"讀取待翻譯新聞時發生未知錯誤：{e}")
    finally:
        if mycursor:
            mycursor.close()
    return results # 返回列表，可能為空

def update_translated_news(mydb, article_id, translated_title, translated_content, tags, slug, translator, status):
    """更新 news 表中的翻譯結果、標籤、slug、翻譯者和狀態"""
    mycursor = None
    success = False
    try:
        mycursor = mydb.cursor()
        update_query = """
            UPDATE news
            SET translated_title = %s,
                translated_content = %s,                
                tags = %s,
                slug = %s,
                translator = %s,
                status = %s,  
                updated_at = NOW()
            WHERE id = %s
        """
        # 處理 None 值，轉換為資料庫 NULL
        db_title = translated_title if translated_title and "翻譯失敗" not in translated_title else None
        db_content = translated_content if translated_content and "翻譯失敗" not in translated_content else None
        db_tags = tags if tags else None
        db_slug = slug if slug else None
        db_translator = translator if translator else 'kakasong' # 提供預設翻譯者
        # status 參數直接使用，不需要預設值或檢查

        # 修正：將 news_type 和 status 加入 val 元組，並確保順序正確
        val = (db_title, db_content, db_tags, db_slug, db_translator, status, article_id)
        mycursor.execute(update_query, val)
        mydb.commit()
        print(f"文章 ID: {article_id} 更新成功 (Translator: {db_translator}, Status: {status})。") # 更新 print 訊息以包含 status
        success = True
    except mysql.connector.Error as err:
        print(f"更新文章 ID: {article_id} 時發生資料庫錯誤: {err}")
        mydb.rollback() # 更新失敗時回滾
    except Exception as e:
        print(f"更新文章時發生未知錯誤：{e}")
        mydb.rollback()
    finally:
        if mycursor:
            mycursor.close()
    return success # 返回 True 表示成功，False 表示失敗

def insert_proper_noun(mydb, noun, url):
    """將專有名詞插入 proper_nouns 表的 unknown_noun 欄位"""
    mycursor = None
    success = False
    stripped_noun = noun.strip() # 去除前後空白

    if not stripped_noun: # 如果去除空白後是空字串，則不插入
        print("提供的名詞為空或僅包含空白，不執行插入。")
        return False

    try:
        mycursor = mydb.cursor()
        # 首先檢查該名詞是否已存在，避免重複插入
        check_sql = "SELECT id FROM proper_nouns WHERE unknown_noun = %s"
        mycursor.execute(check_sql, (stripped_noun,))
        existing_noun = mycursor.fetchone()

        if existing_noun:
            print(f"名詞 '{stripped_noun}' 已存在於 proper_nouns 表中，不重複插入。")
            success = True # 視為成功，因為目標狀態已達成
        else:
            # 如果不存在，則執行插入
            sql = "INSERT INTO proper_nouns (unknown_noun,url) VALUES (%s, %s)"
            val = (stripped_noun, url)
            mycursor.execute(sql, val)
            mydb.commit()
            print(f"已將名詞 '{stripped_noun}' 插入 proper_nouns 表。")
            success = True
    except mysql.connector.Error as err:
        print(f"插入名詞 '{stripped_noun}' 到 proper_nouns 表時發生資料庫錯誤: {err}")
        if mydb.is_connected(): # 檢查連線是否仍然有效
             mydb.rollback() # 插入失敗時回滾
    except Exception as e:
        print(f"插入專有名詞時發生未知錯誤：{e}")
        if mydb.is_connected():
            mydb.rollback()
    finally:
        if mycursor:
            mycursor.close() # 確保游標關閉
    return success # 返回 True 表示成功，False 表示失敗

def get_proper_nouns(mydb):
    """從 proper_nouns 表獲取已翻譯的專有名詞對列表"""
    mycursor = None
    proper_noun_pairs = [] # 初始化一個空列表來存放名詞對
    try:
        mycursor = mydb.cursor()
        # 查詢 unknown_noun 和 translated_noun，僅包括 translated_noun 非空且非空字串的記錄
        sql = """
SELECT unknown_noun, translated_noun 
FROM proper_nouns 
WHERE translated_noun IS NOT NULL AND translated_noun != ''
ORDER BY LENGTH(unknown_noun) DESC
"""
        mycursor.execute(sql)
        results = mycursor.fetchall()
        
        for row in results:
            # 將每一對 (unknown_noun, translated_noun) 作為元組添加到列表中
            proper_noun_pairs.append((row[0], row[1])) 
            
        print(f"從 proper_nouns 表成功獲取 {len(results)} 條已翻譯的專有名詞對。") # 更新打印訊息
            
    except mysql.connector.Error as err:
        print(f"讀取 proper_nouns 時發生資料庫錯誤：{err}")
    except Exception as e:
        print(f"讀取 proper_nouns 時發生未知錯誤：{e}")
    finally:
        if mycursor:
            mycursor.close()
            
    return proper_noun_pairs # 返回包含元組的單一列表
