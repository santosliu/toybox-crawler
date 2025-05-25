import csv
import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# CSV file name
csv_file = 'ruten_auction_new.csv'

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

def delete_csv():
    """Traverse directories and delete all CSV files."""
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted existing file: {file_path}")
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")

def export_csv_by_product_id(test_flag=False):
    conn = None
    try:
        # Connect to the database
        conn = connect_to_db()
        if not conn:
            print("無法連線到資料庫，匯出失敗。")
            return

        cursor = conn.cursor()

        cursor.execute("SELECT product_id, name, price, option FROM aowotoy_products")

        rows = cursor.fetchall()

        column_names = ['類別(必填)', '物品名稱(必填)', '商品價格(必填)', '數量(必填)', '自訂賣場分類', '物品說明', '物品新舊', '圖片1', '圖片2', '圖片3', '物品所在地', '評價總分需大於', '差勁評價需小於', '棄單不可超過次數', '手工製品', '附禮盒/提袋', '原廠保固', '賣家保固', '到府安裝', 'DIY安裝', '專櫃正品', '公司貨', '平行輸入', '可開發票', '可開收據', '附保證書', '附鑑定書', '有多種尺寸', '有多種顏色', '海外運送', '賣家自用料號', '備貨狀態', '預計出貨年月(若備貨狀態為2，則必填)', '較長備商品出貨天數(若備貨狀態為6，則必填)']

        # Export data for each product to a separate CSV file
        for i, row in enumerate(rows):
            if test_flag and i >= 2:
                print("Test flag is set, processing stopped after 2 rows.")
                break

            product_id, name, price, option = row

            # Create directory for the product if it doesn't exist
            product_dir = os.path.join('products', str(product_id))
            os.makedirs(product_dir, exist_ok=True)

            # Define the CSV file path
            product_csv_file = os.path.join(product_dir, csv_file)

            # 如果不存在就製作
            if not os.path.exists(product_csv_file):
                with open(product_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(column_names)

            # 名稱取代
            name = name.replace('高達', '鋼彈')
            name = name.replace('AOWOBOX', '阿庫力')

            # Transform data row to the new format
            transformed_row = [
                '50008',
                name,
                str(float(price) * 1.6),
                '10',
                '6438417',
                f'專為 {name} 設計的壓克力公仔模型展示盒，附有噴繪背景與底板設計。\n\n商品材質：壓克力\n\n商品規格：{option}\n\n如有其他商品疑問，例如燈款、電源等，歡迎小窗詢問。',
                '',
                f'{product_id}_1.jpg',
                f'{product_id}_2.jpg'
            ]
            # Add 26 empty strings
            transformed_row.extend([''] * 26)

            # Write data to CSV file for the current product
            with open(product_csv_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(transformed_row)

            print(f"Data for product {product_id} exported to {product_csv_file}")

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("資料庫連線已關閉。")

def export_all_csv(output_filename='ruten_auction_new.csv', test_flag=False):
    conn = None
    try:
        # Connect to the database
        conn = connect_to_db()
        if not conn:
            print("無法連線到資料庫，匯出失敗。")
            return

        cursor = conn.cursor()

        cursor.execute("SELECT product_id, name, price, option FROM aowotoy_products")

        rows = cursor.fetchall()

        column_names = ['類別(必填)', '物品名稱(必填)', 'OPTION', '商品價格(必填)', '數量(必填)', '自訂賣場分類', '物品說明', '物品新舊', '圖片1', '圖片2', '圖片3', '物品所在地', '評價總分需大於', '差勁評價需小於', '棄單不可超過次數', '手工製品', '附禮盒/提袋', '原廠保固', '賣家保固', '到府安裝', 'DIY安裝', '專櫃正品', '公司貨', '平行輸入', '可開發票', '可開收據', '附保證書', '附鑑定書', '有多種尺寸', '有多種顏色', '海外運送', '賣家自用料號', '備貨狀態', '預計出貨年月(若備貨狀態為2，則必填)', '較長備商品出貨天數(若備貨狀態為6，則必填)']

        # Define the single CSV file path
        all_csv_file = output_filename

        with open(all_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(column_names)

            # Export data for each product to the single CSV file
            for i, row in enumerate(rows):
                if test_flag and i >= 2:
                    print("Test flag is set, processing stopped after 2 rows.")
                    break

                product_id, name, price, option = row

                # 名稱取代
                name = name.replace('高達', '鋼彈')
                name = name.replace('AOWOBOX', '阿庫力')

                # Transform data row to the new format
                calculated_price = round(float(price) * 1.6)
                final_price = calculated_price - (calculated_price % 10)
                transformed_row = [
                    '50008',
                    name,
                    option,
                    str(final_price),
                    '10',
                    '6438417',
                    f'專為 {name} 設計的壓克力公仔模型展示盒，附有噴繪背景與底板設計。\n\n商品材質：壓克力\n\n商品規格：{option}\n\n如有其他商品疑問，例如燈款、電源等，歡迎小窗詢問。',
                    '',
                    f'{product_id}_1.jpg',
                    f'{product_id}_2.jpg'
                ]
                # Add 26 empty strings
                transformed_row.extend([''] * 26)

                # Write data to the single CSV file
                writer.writerow(transformed_row)

                print(f"Data for product {product_id} exported to {all_csv_file}")

        print(f"All product data exported to {all_csv_file}")

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("資料庫連線已關閉。")

if __name__ == "__main__":
    # delete_csv() # Optional: uncomment if you want to delete existing CSVs before exporting
    
    # test_flag = True  # Set to True for testing, False for full export
    export_all_csv(output_filename='all_products.csv')
