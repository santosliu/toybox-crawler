import sys
import os

# 將專案根目錄添加到 Python 路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
import hmac
import hashlib
import json
import requests
from dotenv import load_dotenv
import logging
from src.utils.db import connect_to_db
import mysql.connector

# 配置日誌記錄
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_product_data():
    mydb = None
    cursor = None
    try:
        mydb = connect_to_db()
        if mydb:
            cursor = mydb.cursor(dictionary=True)
            sql = "SELECT * FROM aowotoy_products WHERE product_id = '655ae4cca6e0d9001dcf8564'"
            cursor.execute(sql)
            product_data = cursor.fetchall()
            if product_data:
                logging.info(f"從資料庫獲取原始產品資料 (列表): {product_data}")
                # product_data 是列表，即使只有一條記錄，也需要取第一個元素
                # 返回所有產品資料列表
                return product_data
            else:
                logging.info("資料庫中沒有待上傳的產品資料。")
                return None
        else:
            logging.error("無法連接到資料庫，無法獲取產品資料。")
            return None
    except mysql.connector.Error as err:
        logging.error(f"從資料庫獲取產品資料失敗: {err}")
        return None
    except Exception as e:
        logging.error(f"獲取產品資料時發生未知錯誤: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()
            logging.info("資料庫連線已關閉。")

def upload_product(product_data: dict):
    load_dotenv() 

    api_key = os.getenv('RUTEN_API_KEY')
    secret_key = os.getenv('RUTEN_SECRET_KEY')
    salt_key = os.getenv('RUTEN_SALT_KEY')
    timestamp = int(time.time()) 
    user_agent = os.getenv('RUTEN_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    url = 'https://partner.ruten.com.tw/api/v1/product/item'
    
    post_body = json.dumps(product_data)

    message = (salt_key + url + post_body + str(timestamp)).encode('utf-8')
    signature = hmac.new(secret_key.encode('utf-8'), message, hashlib.sha256).hexdigest()

    headers = {
        'User-Agent': user_agent,
        'X-RT-Key': api_key,
        'X-RT-Timestamp': str(timestamp), 
        'X-RT-Authorization': signature,
    }

    try:
        response = requests.post(url, json=product_data, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(f"Product upload successful: {response.text}")
        # {"status":"success","data":{"item_id":"22523776659295","custom_no":"64f2172741270d001184247e"},"error_code":null,"error_msg":null}
        # 這段要回寫到資料庫中備存
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Status Code: {e.response.status_code}")
            try:
                error_response_text = e.response.content.decode('utf-8', errors='ignore')
                error_data = json.loads(error_response_text)
                logging.error(f"Response JSON: {json.dumps(error_data, ensure_ascii=False, indent=2)}")


            except (UnicodeDecodeError, json.JSONDecodeError):
                logging.error(f"Response Text (raw): {e.response.content}")

if __name__ == '__main__':
    # 示例產品資料
    # product_data = {
    #     'name': '阿庫力測試泡泡瑪特',
    #     'class_id': '00050008',
    #     'store_class_id': '6529089', # 泡泡瑪特的全丟到泡泡瑪特(6529089)，其他可以全丟到公仔模型(6529088)
    #     'condition': 1,
    #     'stock_status': '21DAY',
    #     'description': '此為測試品項，之後請刪除',
    #     'video_link': '',
    #     'location_type': 1,
    #     'location': '03',
    #     'shipping_setting': 1,
    #     'has_spec': False, 
    #     'price': 99999999,
    #     'qty': 10,
    #     'custom_no': '6594da97bbd776001127a5',
    #     'has_spec': True,
    #     'spec_info':[
    #         {
    #             'spec_name': '互卡拼裝',
    #             'item_name': '背底圖案噴繪',
    #             'status': True,
    #             'price': 99999991,
    #             'qty': 10,
    #             'custom_no': '6594da97b9332a00126b08',
    #         },
    #         {
    #             'spec_name': '互卡拼裝',
    #             'item_name': '簡配透明盒身',
    #             'status': True,
    #             'price': 99999992,
    #             'qty': 10,
    #             'custom_no': '6594da97b9332a00126b09',
    #         },
    #         {
    #             'spec_name': '無需拼裝',
    #             'item_name': '背底圖案噴繪',
    #             'status': True,
    #             'price': 99999993,
    #             'qty': 10,
    #             'custom_no': '6594da97b9332a00126b0a',
    #         },
    #         {
    #             'spec_name': '無需拼裝',
    #             'item_name': '簡配透明盒身',
    #             'status': True,
    #             'price': 99999993,
    #             'qty': 10,
    #             'custom_no': '6594da97b9332a00126b0b',
    #         }
    #     ]
    # }

    products_to_upload = get_product_data()
    store_class_id = '6529089'  # 預設為泡泡瑪特的 store_class_id
    if products_to_upload:
        logging.info("準備上傳以下產品資料:")
        for product in products_to_upload:
            # 根據產品名稱判斷 store_class_id
            store_class_id = '6529089' if '泡泡瑪特' in product['name'] else '6529088'

            # 解析 spec_info 欄位 (如果存在且為字串)
            spec_info_list = []
            # if product.get('option') and isinstance(product['option'], str):
            #     try:
            #         spec_info_data = json.loads(product['option'])
            #         for spec in spec_info_data:
            #             spec_info_list.append({
            #                 'spec_name': spec.get('spec_name', ''),
            #                 'item_name': spec.get('item_name', ''),
            #                 'status': spec.get('status', True), # 預設為 True
            #                 'price': spec.get('price', 0),
            #                 'qty': spec.get('qty', 0),
            #                 'custom_no': spec.get('custom_no', ''),
            #             })
            #     except json.JSONDecodeError as e:
            #         logging.error(f"解析 spec_info 失敗: {e} for product_id: {product.get('product_id')}")
            #         spec_info_list = [] # 解析失敗則清空規格資訊

            
        # 構建上傳的產品資料字典
        formatted_product_data = {
            'name': product.get('name', ''),
            'class_id': '00050008', 
            'store_class_id': store_class_id,
            'condition': 1, 
            'stock_status': '21DAY', 
            'description': product.get('detail', ''),
            'video_link': '',
            'location_type': 1, # 預設為 1 (台灣)
            'location': '03', # 預設為 03 (新北市)
            'shipping_setting': 1, 
            'has_spec': bool(spec_info_list), # 如果 spec_info_list 不為空，則為 True
            'price': product.get('price', 0),
            'qty': 10,
            'custom_no': product.get('product_id', ''),
        }
        
        # 如果有規格，則添加 spec_info
        if spec_info_list:
            formatted_product_data['spec_info'] = spec_info_list
                
        logging.info(f"轉換後的產品資料: {json.dumps(formatted_product_data, ensure_ascii=False, indent=2)}")
        # upload_product(formatted_product_data)
    else:
        logging.info("沒有產品資料可供上傳。")
