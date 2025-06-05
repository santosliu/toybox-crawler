import time
import hmac
import hashlib
import json
import requests
import os
from dotenv import load_dotenv

def upload_product():
    load_dotenv() # Load environment variables from .env file

    api_key = os.getenv('RUTEN_API_KEY')
    secret_key = os.getenv('RUTEN_SECRET_KEY')
    salt_key = os.getenv('RUTEN_SALT_KEY')
    timestamp = int(time.time()) # PHP time() returns Unix timestamp

    url = 'https://partner.ruten.com.tw/api/v1/product/item'
    data = {
        'name': '精品濾掛式咖啡',
        'class_id': '00240029',
        'store_class_id': '0',
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

    post_body = json.dumps(data)

    message = (salt_key + url + post_body + str(timestamp)).encode('utf-8')
    signature = hmac.new(secret_key.encode('utf-8'), message, hashlib.sha256).hexdigest()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-RT-Key': api_key,
        'X-RT-Timestamp': str(timestamp), # Timestamp needs to be string in header
        'X-RT-Authorization': signature,
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                error_response_text = e.response.content.decode('utf-8', errors='ignore')
                error_data = json.loads(error_response_text)
                print(f"Response JSON: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                print(f"Response Text (raw): {e.response.content}")


if __name__ == '__main__':
    upload_product()
