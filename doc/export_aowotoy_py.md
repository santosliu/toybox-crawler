# `export_aowotoy.py` 文件

## 描述
此 Python 腳本用於從 MySQL 資料庫中匯出 aowotoys 產品資料到 CSV 文件，這些 CSV 文件格式符合露天拍賣的上傳要求。它提供了兩種匯出模式：為每個產品建立單獨的 CSV 文件，或將所有產品資料匯出到一個單一的 CSV 文件。

## 依賴
- `csv`: Python 內建模組，用於讀寫 CSV 文件。
- `os`: Python 內建模組，用於文件系統操作。
- `mysql.connector`: 用於連接和操作 MySQL 資料庫。
- `dotenv`: 用於從 `.env` 文件載入環境變數（例如資料庫憑證）。

## 主要功能

### `connect_to_db()`
- **描述**: 建立並返回一個 MySQL 資料庫連線。資料庫憑證從環境變數中載入。
- **返回**: `mysql.connector.connection` 物件（如果連線成功），否則為 `None`。

### `delete_csv()`
- **描述**: 遍歷當前目錄及其子目錄，刪除所有找到的 `.csv` 文件。
- **注意**: 此函數在 `main` 函數中被註釋掉，如果需要使用，請取消註釋。

### `export_csv_by_product_id(test_flag=False)`
- **描述**: 從資料庫中查詢產品資料，並為每個產品在 `products/[product_id]` 目錄下建立一個單獨的 CSV 文件。它會將產品名稱中的特定詞語進行替換（例如「高達」替換為「鋼彈」，「AOWOBOX」替換為「阿庫力」），並計算價格。
- **參數**: `test_flag` (bool) - 如果設定為 `True`，則只處理前兩行資料用於測試。

### `export_all_csv(output_filename='ruten_auction_new.csv', test_flag=False)`
- **描述**: 從資料庫中查詢所有產品資料，並將其匯出到一個單一的 CSV 文件中。此函數也會對產品名稱進行替換，並計算價格（價格會向下取整到最接近的 10 的倍數）。
- **參數**:
    - `output_filename` (str) - 匯出 CSV 文件的名稱，預設為 `ruten_auction_new.csv`。
    - `test_flag` (bool) - 如果設定為 `True`，則只處理前兩行資料用於測試。

## 使用方法

1. **環境變數設定**:
   在腳本的根目錄下建立一個 `.env` 文件，並設定以下資料庫連線資訊：
   ```
   DB_HOST=your_db_host
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   ```

2. **安裝依賴**:
   ```bash
   pip install mysql-connector-python python-dotenv
   ```

3. **執行腳本**:
   ```bash
   python src/export_aowotoy.py
   ```
   預設情況下，腳本會執行 `export_all_csv` 函數，將所有產品資料匯出到 `all_products.csv` 文件中。

   如果您想使用 `export_csv_by_product_id` 函數或在匯出前刪除現有 CSV 文件，您需要修改 `if __name__ == "__main__":` 區塊的程式碼。
