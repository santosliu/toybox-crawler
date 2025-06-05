import os

def rename_images(products_dir="products"):
    for root, dirs, files in os.walk(products_dir):
        for file in files:
            # Assuming files are named like 1.jpg, 2.png, etc.
            # and the directory name is the product ID
            try:
                index = file.split('.')[0]
                ext = os.path.splitext(file)[1]
                product_id = os.path.basename(root)
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, f"{product_id}_{index}{ext}")
                os.rename(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")
            except Exception as e:
                print(f"Error renaming {file} in {root}: {e}")

if __name__ == "__main__":
    rename_images()
