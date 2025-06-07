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

    url = 'https://partner.ruten.com.tw/api/v1/product/list'
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
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
        response = requests.get(url, json=product_data, headers=headers)
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
    sample_product_data = {
    }
    upload_product(sample_product_data)
    
