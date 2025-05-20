"""
檔案名稱: GameSpot_scrap.py
版本: 1.1 (Refactored DB operations)
建立日期: 2025/04/09
修改日期: 2025/04/17
作者: santosliu

描述:
    從 GameSpot 備份文章和首圖，資料庫操作已移至 db_utils.py
        
備註:
    
"""
import os
import re
import asyncio
from playwright.async_api import async_playwright
import random
import aiohttp 
from dotenv import load_dotenv
import mysql.connector # 保留 mysql.connector 以便處理可能的錯誤類型
import json # 新增導入 json 模組
from urllib.parse import urljoin # 導入 urljoin

# 設定 headers 模擬瀏覽器請求
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

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

async def crawl_list(url):
    """從指定 URL 爬取文章 ID 和連結"""
    async with async_playwright() as p:
        # 確保在無 X11 環境下執行
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        await page.set_extra_http_headers(headers) # 設定 headers
        try:
            await page.goto(url, timeout=60000)

            link_elements = await page.query_selector_all("a.Product-item")
            data = []
            for link_element in link_elements:
                href = await link_element.get_attribute("href")
                data.append(f'{href}?locale=zh-hant')                
        except Exception as e:
            print(f"爬取文章列表 {url} 時發生錯誤: {e}")
            data = [] # 發生錯誤時返回空列表
        finally:
            await browser.close() # 確保瀏覽器關閉
        return data # 返回包含 (文章編號, URL) 元組的列表

async def crawl_single(mydb, data):
    """爬取單篇文章內容、圖片並寫入資料庫 (Refactored to use process_single_article)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        await page.set_extra_http_headers(headers)

        # 取得最新的 id 當作編號
        # try:
        #     cursor = mydb.cursor()
        #     cursor.execute("SELECT MAX(id) FROM boxdata;")
        #     latest_id = cursor.fetchone()[0]
        #     if latest_id is None:
        #         latest_id = 0
        #     latest_id += 1 # 將最新的 id + 1
        #     formatted_id = f"{latest_id:05d}" # 格式化為五位數，不足補零
        #     print(f"最新的 boxdata ID: {formatted_id}")
        #     cursor.close()
        # except mysql.connector.Error as err:
        #     print(f"取得最新 boxdata ID 時發生錯誤: {err}")
        #     formatted_id = "00001" # 發生錯誤時設置為預設值

        latest_id = 0

        async with aiohttp.ClientSession() as session:
            for url in data:
                latest_id += 1
                formatted_id = f"{latest_id:05d}"

                # 加入隨機延遲，控制請求速率
                await asyncio.sleep(random.randint(2, 5))

                # TODO: 檢查資料庫中是否已存在此 URL
                # 假設您有一個函數 check_url_exists(mydb, url) 來執行此檢查
                # 您需要根據您的資料庫存取方式來實現這個函數
                # 例如:
                cursor = mydb.cursor()
                cursor.execute("SELECT COUNT(*) FROM boxdata WHERE url = %s", (url,))
                count = cursor.fetchone()[0]
                cursor.close()
                if count > 0:
                    print(f"URL {url} 已存在於資料庫中，跳過抓取。")
                    continue

                # 檢查並建立目錄
                item_dir = "item"
                item_id_dir = os.path.join(item_dir, formatted_id)
                if not os.path.exists(item_dir):
                    os.makedirs(item_dir)
                    print(f"已建立目錄: {item_dir}")
                if not os.path.exists(item_id_dir):
                    os.makedirs(item_id_dir)
                    print(f"已建立目錄: {item_id_dir}")

                # 依序處理每篇文章
                try:
                    await page.goto(url, timeout=60000)
                    # 取得頁面內容
                    page_content = await page.content()
                    print(f"頁面內容 for {url}:")

                    # 取得圖片容器的 style 內容
                    try:
                        image_container_elements = await page.query_selector_all('div.image-container[data-e2e-id="variant-image_container"]')
                        for i, image_container_element in enumerate(image_container_elements):
                            style_attribute = await image_container_element.get_attribute('style')
                            if style_attribute:
                                # 使用正則表達式提取 URL
                                match = re.search(r'url\("(.+?)"\)', style_attribute)
                                if match:
                                    image_url = match.group(1)
                                    print(f"原始圖片 URL {i+1}: {image_url}")
                                    
                                    # 修改圖片 URL
                                    modified_image_url = image_url.replace("140x.webp", "800x.webp")
                                    print(f"修改後圖片 URL {i+1}: {modified_image_url}")

                                    # 下載圖片
                                    try:
                                        async with session.get(modified_image_url) as response:
                                            if response.status == 200:
                                                image_content = await response.read()
                                                image_filename = os.path.join(item_id_dir, f"{i+1}.jpg")
                                                with open(image_filename, 'wb') as f:
                                                    f.write(image_content)
                                                print(f"已下載圖片: {image_filename}")
                                            else:
                                                print(f"下載圖片失敗，狀態碼: {response.status} for {image_url}")
                                    except Exception as download_e:
                                        print(f"下載圖片時發生錯誤 {image_url}: {download_e}")

                                else:
                                    print(f"圖片容器 Style {i+1} 中找不到 URL 模式")
                            else:
                                print(f"圖片容器 Style {i+1} 屬性為 None")
                    except Exception as style_e:
                        print(f"無法取得圖片容器 Style for {url}: {style_e}")

                    # 取得 <h1 class="Product-title"> 的內容
                    try:
                        item_title_element = page.locator('h1.Product-title')
                        item_title = await item_title_element.inner_text()
                        print(f"產品標題: {item_title}")
                    except Exception as title_e:
                        print(f"無法取得產品標題 for {url}: {title_e}")

                    # 取得價格的內容
                    try:
                        price_text = ''
                        price_element = page.locator('div.global-primary.dark-primary.price-regular.price.price-crossed.ng-binding')
                        price_text = await price_element.inner_text()
                        print(f"產品價格: {price_text.strip()}") # 使用 strip() 移除可能的空白字元
                    except Exception as price_e:
                        print(f"無法取得產品價格 for {url}: {price_e}")

                    # 取得 <p class="Product-summary Product-summary-block"> 的內容
                    try:
                        summary = ''
                        summary_element = page.locator('p.Product-summary.Product-summary-block')
                        summary = await summary_element.inner_text()
                        print(f"產品摘要: {summary.strip()}") # 使用 strip() 移除可能的空白字元
                    except Exception as summary_e:
                        print(f"無法取得產品摘要 for {url}: {summary_e}")

                    # 取得 <div class="ProductDetail-description"> 的內容
                    try:
                        item_detail_element = page.locator('div.ProductDetail-description')
                        item_detail_raw = await item_detail_element.inner_text()
                        item_detail = item_detail_raw.replace("商品描述", "").strip() # 排除 "商品描述" 並移除可能的空白字元
                        print(f"產品詳細內容: {item_detail}")
                    except Exception as item_detail_e:
                        print(f"無法取得產品詳細內容 for {url}: {item_detail_e}")


                except Exception as e:
                    print(f"爬取單篇文章 {url} 時發生錯誤: {e}")

                # 將資料寫入資料庫
                try:
                    cursor = mydb.cursor()
                    # 嘗試將價格轉換為整數，如果失敗則設置為 0
                    try:
                        price_int = int(re.sub(r'[^\d]', '', price_text)) if 'price_text' in locals() and price_text else 0
                    except ValueError:
                        price_int = 0

                    sql = "INSERT INTO boxdata (url, name, price, item_summary, item_detail) VALUES (%s, %s, %s, %s, %s)"
                    val = (url,
                           item_title if 'item_title' in locals() else '',
                           price_int,
                           summary if 'summary' in locals() else '',
                           item_detail if 'item_detail' in locals() else '')
                    
                    cursor.execute(sql, val)
                    mydb.commit()
                    print(f"資料已成功寫入資料庫，ID: {cursor.lastrowid}")
                    cursor.close()
                except mysql.connector.Error as err:
                    print(f"寫入資料庫時發生錯誤 for {url}: {err}")
                    if mydb.is_connected():
                        mydb.rollback() # 發生錯誤時回滾事務


        await browser.close()

async def main():
    mydb = connect_to_db() 
    if not mydb: 
        print("無法連線到資料庫，程式終止。")
        return 
    
    # 第一次為了建立流水號正向建立
    base_url = "https://www.aowotoys.com/categories/aowobox-displaybox?sort_by=created_at&order_by=asc&limit=72&page="
    max_page = 33 # 設定最大頁數
    data = [] # 初始化資料列表

    try:
        for page in range(1, max_page+1):  
            url = f"{base_url}{page}"
            print(f"開始從 {url} 爬取資料...")
            list = await crawl_list(url)
            data = data+list            

        # 測試用內容
        # data.append("https://www.aowotoys.com/products/aowobox-ribose-dlc-teatimecat-cowcat-displaybox?locale=zh-hant") 
        
        if data: # 確保有資料才繼續
            print("開始爬取文章內容、圖片並即時寫入資料庫...")
            await crawl_single(mydb, data) 
        else:
            print("未找到任何文章連結或爬取列表時發生錯誤。")

        # print("爬取與寫入流程完成。") 
    except Exception as e:
        print(f"執行 main 函數時發生未預期錯誤: {e}")
    finally:
        if mydb and mydb.is_connected(): # 確保連線存在且開啟才關閉
            mydb.close()
            print("資料庫連線已關閉。")

if __name__ == "__main__":
    asyncio.run(main())
