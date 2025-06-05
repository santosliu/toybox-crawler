# `rename.py` 文件

## 描述
此 Python 腳本用於重新命名 `products` 目錄及其子目錄中的圖片文件。它假設每個子目錄的名稱是產品 ID，並將子目錄中的圖片文件從原始的數字名稱（例如 `1.jpg`）重新命名為包含產品 ID 的格式（例如 `product_id_1.jpg`）。

## 依賴
- `os`: Python 內建模組，用於文件系統操作，例如遍歷目錄和重新命名文件。

## 主要功能

### `rename_images(products_dir="products")`
- **描述**: 遍歷指定目錄（預設為 `products`）下的所有子目錄和文件。對於每個文件，它會嘗試根據其所在的目錄名稱（產品 ID）和原始文件名中的數字索引來構造新的文件名，然後執行重新命名操作。
- **參數**: `products_dir` (str) - 包含產品圖片的根目錄路徑，預設為 `"products"`。

## 使用方法

1. **準備圖片目錄結構**:
   確保您的圖片文件位於類似以下的目錄結構中：
   ```
   products/
   ├── product_id_A/
   │   ├── 1.jpg
   │   ├── 2.png
   │   └── ...
   └── product_id_B/
       ├── 1.jpeg
       └── ...
   ```

2. **執行腳本**:
   ```bash
   python src/rename.py
   ```
   腳本將會自動遍歷 `products` 目錄並重新命名其中的圖片文件。
