import unittest
import os
import shutil
import tempfile
from src.rename import rename_images

class TestRenameImages(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.products_dir = os.path.join(self.test_dir, "products")
        os.makedirs(self.products_dir)

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def test_rename_images_basic(self):
        # Create a product directory and dummy files
        product_id = "product123"
        product_path = os.path.join(self.products_dir, product_id)
        os.makedirs(product_path)

        # Create dummy files with simple names
        files_to_create = ["1.jpg", "2.png", "3.jpeg"]
        for file_name in files_to_create:
            with open(os.path.join(product_path, file_name), 'w') as f:
                f.write("dummy content")

        # Run the rename function
        rename_images(self.products_dir)

        # Check if files are renamed correctly
        expected_files = [f"{product_id}_1.jpg", f"{product_id}_2.png", f"{product_id}_3.jpeg"]
        actual_files = os.listdir(product_path)

        self.assertEqual(sorted(actual_files), sorted(expected_files))

    def test_rename_images_empty_directory(self):
        # Test with an empty products directory
        rename_images(self.products_dir)
        self.assertEqual(os.listdir(self.products_dir), [])

    def test_rename_images_no_products_dir(self):
        # Test when the products directory does not exist
        # The function should handle this gracefully without error
        non_existent_dir = os.path.join(self.test_dir, "non_existent_products")
        rename_images(non_existent_dir)
        self.assertFalse(os.path.exists(non_existent_dir))


if __name__ == '__main__':
    unittest.main()
