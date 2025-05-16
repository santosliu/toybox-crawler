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

async def crawl_data(url):
    """從指定 URL 爬取文章 ID 和連結"""
    async with async_playwright() as p:
        # 確保在無 X11 環境下執行
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        await page.set_extra_http_headers(headers) # 設定 headers
        try:
            await page.goto(url, timeout=60000)

            # 選取 <div class="card-item__content"> 內部的 <a class="card-item__link"> 標籤
            link_elements = await page.query_selector_all("div.card-item__content a.card-item__link")
            data = []
            for link_element in link_elements:
                href = await link_element.get_attribute("href")
                if href:
                    # 使用 regex 提取 ID
                    match = re.search(r'/(\d+-\d+)/?$', href)
                    if match:
                        article_id = match.group(1) # 提取匹配到的 ID
                        absolute_url = urljoin(url, href)
                        data.append((article_id, absolute_url)) # 使用提取的 ID
                    else:
                        print(f"警告：無法從 href '{href}' 提取 ID，跳過此連結。")
        except Exception as e:
            print(f"爬取文章列表 {url} 時發生錯誤: {e}")
            data = [] # 發生錯誤時返回空列表
        finally:
            await browser.close() # 確保瀏覽器關閉
        return data # 返回包含 (文章編號, URL) 元組的列表

async def crawl_news(mydb, data):
    """爬取單篇文章內容、圖片並寫入資料庫 (Refactored to use process_single_article)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = await browser.new_page()
        await page.set_extra_http_headers(headers)

        # --- 獲取一次專有名詞列表 ---
        proper_nouns_list = []
        try:
            proper_nouns_list = get_proper_nouns(mydb)
            print(f"成功獲取 {len(proper_nouns_list)} 個專有名詞。")
        except Exception as e:
            print(f"獲取專有名詞列表時發生錯誤: {e}。將繼續執行，但可能影響專有名詞替換。")
        # --- 專有名詞獲取結束 ---

        async with aiohttp.ClientSession() as session:
            for data_id, url in data:
                # 加入隨機延遲，控制請求速率
                await asyncio.sleep(random.randint(2, 5))
                # 依序處理每篇文章
                await process_single_article(mydb, page, session, data_id, url, proper_nouns_list)

        await browser.close()

async def main():
    mydb = connect_to_db() 
    if not mydb: 
        print("無法連線到資料庫，程式終止。")
        return 

    # base_url = "https://www.aowotoys.com/categories/aowobox-displaybox?sort_by=created_at&order_by=desc&limit=72&page="
    base_url = "https://www.aowotoys.com/categories/aowobox-displaybox?sort_by=created_at&order_by=asc&limit=72&page="
    max_page = 2 # 設定最大頁數
    try:
        for page in range(1, max_page+1):  
            url = f"{base_url}{page}"
            print(f"開始從 {url} 爬取資料...")
            # data = await crawl_data(url)

            # 測試用內容
            # data.append(('TEST', 
            #              'https://www.gamespot.com/articles/kingdom-hearts-missing-link-canceled-team-hard-at-work-on-kingdom-hearts-4/1100-6531532/')) 

        # if data: # 確保有資料才繼續
        #     print("開始爬取文章內容、圖片並即時寫入資料庫...")
        #     await crawl_news(mydb, data) 
        # else:
        #     print("未找到任何文章連結或爬取列表時發生錯誤。")

        # print("爬取與寫入流程完成。") 
    except Exception as e:
        print(f"執行 main 函數時發生未預期錯誤: {e}")
    finally:
        if mydb and mydb.is_connected(): # 確保連線存在且開啟才關閉
            mydb.close()
            print("資料庫連線已關閉。")

if __name__ == "__main__":
    asyncio.run(main())
