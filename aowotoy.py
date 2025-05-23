"""
描述:
    爬取 aowotoys 網站的產品資料，包括產品 ID、標題、摘要、價格、選項和詳細描述，並將這些資料寫入 MySQL 資料庫。
    下載產品圖片並儲存到本地目錄中。
    
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

        async with aiohttp.ClientSession() as session:
            for url in data:

                # 加入隨機延遲，控制請求速率
                await asyncio.sleep(random.randint(2, 5))

                # 依序處理每篇文章
                try:
                    await page.goto(url, timeout=60000)
                    # 取得頁面內容
                    page_content = await page.content()
                    print(f"頁面內容 for {url}:")

                    # 取得 product_details
                    # 取得 <div class="ProductDetail-description"> 的內容
                    try:
                        product_detail_element = page.locator('div.ProductDetail-description')
                        product_detail_raw = await product_detail_element.inner_text()
                        product_detail = product_detail_raw.replace("商品描述", "").strip() # 排除 "商品描述" 並移除可能的空白字元
                        print(f"產品詳細內容: {product_detail}")
                    except Exception as product_detail_e:
                        print(f"無法取得產品詳細內容 for {url}: {product_detail_e}")

                    # 使用正則表達式尋找內容並轉換為 JSON
                    match = re.search(r"app\.value\('product', JSON\.parse\('(.*?)'\)\);", page_content)
                    if match:
                        extracted_content = match.group(1)
                        extracted_content = extracted_content.replace("\\\"", "\"")
                        try:
                            json_data = json.loads(extracted_content)
                        except json.JSONDecodeError as json_err:
                            print(f"解析 JSON 時發生錯誤: {json_err}")
                            continue                        
                    else:
                        print("未找到匹配的內容。")

                    product_id = json_data.get('_id', '')
                    product_title = json_data.get('title_translations', {}).get('zh-hant', {})
                    product_summary = json_data.get('summary_translations', {}).get('zh-hant', {})
                    
                    variations = json_data.get('variations', [])
                    for variation in variations:
                        option_id = variation.get('key', '')

                        # 檢查並建立目錄
                        product_dir = "products"
                        product_id_dir = os.path.join(product_dir, product_id)
                        if not os.path.exists(product_dir):
                            os.makedirs(product_dir)
                            print(f"已建立目錄: {product_dir}")
                        if not os.path.exists(product_id_dir):
                            os.makedirs(product_id_dir)
                            print(f"已建立目錄: {product_id_dir}")

                        price = variation.get('price', {}).get('dollars', 0)*4
                        print(f"價格: {price}")

                        product_fields = []
                        fields = variation.get('fields', [])
                        for field in fields:
                            name = field.get('name_translations', {}).get('zh-hant', '')
                            product_fields.append(name)

                        product_option = '+ '.join(product_fields) # Convert set to string
                        print(f"產品選項: {product_option}")

                        # 將資料寫入資料庫
                        try:
                            cursor = mydb.cursor()
                            
                            sql = "INSERT INTO aowotoy_products (product_id, option_id, url, name, summary, price, option, detail) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                            val = (product_id, 
                                option_id if 'option_id' in locals() else '',
                                url if 'url' in locals() else '',
                                product_title if 'product_title' in locals() else '',
                                product_summary if 'product_summary' in locals() else '',
                                price if 'price' in locals() else 0,
                                product_option if 'product_option' in locals() else '',
                                product_detail if 'product_detail' in locals() else '')                                
                            
                            cursor.execute(sql, val)
                            mydb.commit()
                            print(f"資料已成功寫入資料庫，ID: {cursor.lastrowid}")
                            cursor.close()
                        except mysql.connector.Error as err:
                            print(f"寫入資料庫時發生錯誤 for {url}: {err}")
                            if mydb.is_connected():
                                mydb.rollback() # 發生錯誤時回滾事務

                    # 下載圖片
                    count = 0
                    medias = json_data.get('media', [])
                    for image in medias:
                    # for image in medias[:2]:
                        image_url = image.get('images', {}).get('original', {}).get('url', '')
                        count += 1
                        image_url = re.sub(r'\?.*$', '', image_url)
                        
                        if image_url:
                            image_name = os.path.basename(image_url)
                            image_ext = os.path.splitext(image_name)[1]
                            saved_name = f"{product_id}_{count}.jpg"
                            image_path = os.path.join(product_id_dir, saved_name)

                            async with session.get(image_url) as img_response:
                                with open(image_path, 'wb') as img_file:
                                    img_file.write(await img_response.read())

                except Exception as e:
                    print(f"爬取單篇文章 {url} 時發生錯誤: {e}")


        await browser.close()

async def main():
    mydb = connect_to_db() 
    if not mydb: 
        print("無法連線到資料庫，程式終止。")
        return 
        
    base_url = "https://www.aowotoys.com/categories/aowobox-displaybox?sort_by=created_at&order_by=desc&limit=72&page="
    max_page = 33 # 設定最大頁數
    data = [] # 初始化資料列表

    try:
        
        for page in range(1, max_page+1):  
            url = f"{base_url}{page}"
            print(f"開始從 {url} 爬取資料...")
            list = await crawl_list(url)
            data = data+list            
        
        # 測試用內容
        # data = []
        # data.append("https://www.aowotoys.com/products/aowobox-pop-mart-dimoo-whisper-of-the-rose-figure-theme-display-box?locale=zh-hant") 

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
