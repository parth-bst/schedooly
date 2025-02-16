import unittest
from venv import logger
from src.google_docs_reader import GoogleDocManager

TEST_CONFIG = {
    "TEST_DOC_ID": "1FM8ycJpGRsgJPgVI5QuCOZ5XS9v-FnHVNegHXRbCBtE",
    "TEST_SHEET_ID": "14mOP411mlGvEZilz2eHG5Sk1E_lw6kxoTLYgd7NeQok",
    "TEST_SHEET_RANGE": "Sheet1!A1:B2"
}



class TestGoogleDocManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the manager once for all tests
        cls.manager = GoogleDocManager()
        
        # Get config values
        cls.TEST_DOC_ID = TEST_CONFIG["TEST_DOC_ID"]
        cls.TEST_SHEET_ID = TEST_CONFIG["TEST_SHEET_ID"]
        cls.TEST_SHEET_RANGE = TEST_CONFIG["TEST_SHEET_RANGE"]
        
        # Set up test data in the sheet
        cls.TEST_DATA = [
            ["Header1", "Header2"],
            ["Value1", "Value2"]
        ]
        cls.manager.write_to_sheet(cls.TEST_SHEET_ID, cls.TEST_SHEET_RANGE, cls.TEST_DATA)

    def test_write_and_read_sheet(self):
        # Test writing
        new_data = [["Test1", "Test2"], ["Test3", "Test4"]]
        write_result = self.manager.write_to_sheet(
            self.TEST_SHEET_ID,
            self.TEST_SHEET_RANGE,
            new_data
        )
        logger.info(f"Write Result: {write_result}")
        self.assertIsNotNone(write_result)

        # Test reading
        read_result = self.manager.read_sheet(
            self.TEST_SHEET_ID,
            self.TEST_SHEET_RANGE
        )
        logger.info(f"Read Result: {read_result}")
        self.assertEqual(read_result, new_data)

    def test_append_to_sheet(self):
        append_data = [["Append1", "Append2"]]
        append_result = self.manager.append_to_sheet(
            self.TEST_SHEET_ID,
            "Sheet1!A:B",
            append_data
        )
        logger.info(f"Append Result: {append_result}")
        self.assertIsNotNone(append_result)

        # Verify append
        full_data = self.manager.read_sheet(self.TEST_SHEET_ID, "Sheet1!A:B")
        self.assertTrue(any(row == append_data[0] for row in full_data))

    def test_get_base_cv_data(self):
        result = self.manager.get_base_cv_data(self.TEST_DOC_ID)
        logger.info(f"Base CV Data: {result}")
        self.assertIsInstance(result, list)
        # Add specific assertions based on your test document content
        # self.assertIn('Name', result)
        # self.assertIn('Experience', result)
        

if __name__ == '__main__':
    unittest.main()
