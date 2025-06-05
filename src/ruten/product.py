import time
import hmac
import hashlib
import json
import requests
import os
from dotenv import load_dotenv
import logging

# 配置日誌記錄
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_product(product_data: dict):
    load_dotenv() 

    api_key = os.getenv('RUTEN_API_KEY')
    secret_key = os.getenv('RUTEN_SECRET_KEY')
    salt_key = os.getenv('RUTEN_SALT_KEY')
    timestamp = int(time.time()) 

    url = os.getenv('RUTEN_PRODUCT_API_URL', 'https://partner.ruten.com.tw/api/v1/product/item')
    user_agent = os.getenv('RUTEN_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    post_body = json.dumps(product_data)

    message = (salt_key + url + post_body + str(timestamp)).encode('utf-8')
    signature = hmac.new(secret_key.encode('utf-8'), message, hashlib.sha256).hexdigest()

    headers = {
        'User-Agent': user_agent,
        'X-RT-Key': api_key,
        'X-RT-Timestamp': str(timestamp), # Timestamp needs to be string in header
        'X-RT-Authorization': signature,
    }

    try:
        response = requests.post(url, json=product_data, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        logging.info(f"Product upload successful: {response.text}")
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
    sample_product_data = {
        'name': '精品濾掛式咖啡',
        'class_id': '00240029',
        'store_class_id': '0', # 根據之前的錯誤，這可能需要是一個有效值
        'condition': 1,
        'stock_status': '3DAY',
        'description': '<dl><dt>特色說明</dt>...</dl>',
        'video_link': 'https://youtu.be/tGy_vN99Xh6',
        'location_type': 1,
        'location': '05',
        'shipping_setting': 1,
        'has_spec': False, 
        'price': 799,
        'qty': 300,
        'custom_no': 'SFH-1005',
    }
    upload_product(sample_product_data)
    
