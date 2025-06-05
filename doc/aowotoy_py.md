# `aowotoy.py` 文件

## 描述
此 Python 腳本用於爬取 aowotoys 網站的產品資料。它會從指定類別頁面抓取產品連結，然後逐一訪問每個產品頁面，提取產品 ID、標題、摘要、價格、選項和詳細描述。同時，它會下載產品圖片並儲存到本地目錄中。所有提取的產品資料最終會寫入 MySQL 資料庫。

## 依賴
- `playwright`: 用於瀏覽器自動化，爬取動態網頁內容。
- `aiohttp`: 用於異步 HTTP 請求，特別是用於下載圖片。
- `mysql.connector`: 用於連接和操作 MySQL 資料庫。
- `dotenv`: 用於從 `.env` 文件載入環境變數（例如資料庫憑證）。
- `asyncio`: Python 的異步 I/O 框架。
- `re`: 正則表達式模組，用於從頁面內容中提取資料。
- `os`: 用於文件系統操作，例如建立目錄和處理文件路徑。
- `json`: 用於處理 JSON 資料。
- `urllib.parse.urljoin`: 用於處理 URL。

## 主要功能

### `connect_to_db()`
- **描述**: 建立並返回一個 MySQL 資料庫連線。資料庫憑證從環境變數中載入。
- **返回**: `mysql.connector.connection` 物件（如果連線成功），否則為 `None`。

### `crawl_list(url)`
- **描述**: 從指定的 URL 爬取產品列表頁面，提取所有產品的連結。
- **參數**: `url` (str) - 要爬取的列表頁面 URL。
- **返回**: `list` - 包含產品詳細頁面 URL 的列表。

### `crawl_single(mydb, data)`
- **描述**: 遍歷產品 URL 列表，爬取每個產品的詳細內容和圖片。它會提取產品的各種屬性（ID、標題、摘要、價格、選項、詳細描述），將圖片下載到本地的 `products/[product_id]` 目錄中，並將所有資料寫入 MySQL 資料庫的 `aowotoy_products` 表。
- **參數**:
    - `mydb`: 已建立的 MySQL 資料庫連線物件。
    - `data`: `list` - 包含產品詳細頁面 URL 的列表。

### `main()`
- **描述**: 腳本的入口點。它負責：
    1. 連接到資料庫。
    2. 設定基礎 URL 和最大頁數，然後循環爬取所有列表頁面以收集產品連結。
    3. 調用 `crawl_single` 函數來處理每個產品的詳細資料和圖片下載。
    4. 確保在程式結束時關閉資料庫連線。

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
   pip install playwright aiohttp mysql-connector-python python-dotenv
   playwright install
   ```

3. **執行腳本**:
   ```bash
   python src/aowotoy.py
   ```

腳本將會自動開始爬取 aowotoys 網站，並將資料儲存到資料庫和本地文件系統中。
