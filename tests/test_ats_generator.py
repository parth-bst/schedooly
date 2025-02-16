import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
from src.ats_generator import GenerateCoverLetterCV

class TestGenerateCoverLetterCV(unittest.TestCase):
    def setUp(self):
        self.generator = GenerateCoverLetterCV()
        self.test_job = {
            "title": "Software Engineer",
            "description": "Looking for a Python developer with 5+ years experience in web development"
        }
        self.test_cv = {
            "experience": "7 years Python development, Django, Flask, API development"
        }

    @patch('lib.ats_generator.ChatOpenAI')
    def test_generate_documents_success(self, mock_chat):
        mock_response = MagicMock()
        mock_response.content = "Generated test content"
        mock_chat.return_value.invoke.return_value = mock_response

        result = self.generator.generate_documents(self.test_job, self.test_cv)
        self.assertIsInstance(result, str)

    def test_create_prompt_format(self):
        prompt = self.generator._create_prompt(self.test_job, self.test_cv)
        self.assertIn(self.test_job['description'], prompt)
        self.assertIn(str(self.test_cv), prompt)

class TestGenerateCoverLetterCVIntegration(unittest.TestCase):
    def setUp(self):
        self.generator = GenerateCoverLetterCV()
        self.test_job = {
            "title": "Senior Software Engineer",
            "description": "Looking for a Python expert with experience in AI/ML"
        }
        self.test_cv = {
            "experience": "8 years software development, Python, TensorFlow, PyTorch"
        }

    def test_real_openai_generation(self):
        result = self.generator.generate_documents(self.test_job, self.test_cv)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        
        # Verify file creation
        expected_file = Path(f"output/{self.test_job['title']}_Cover_Letter.docx")
        self.assertTrue(expected_file.exists())
        
        # Cleanup
        if expected_file.exists():
            os.remove(expected_file)

if __name__ == '__main__':
    unittest.main()
