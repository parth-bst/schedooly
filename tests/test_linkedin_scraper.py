import unittest
from unittest.mock import Mock, patch
from venv import logger
from src.linkedin_scraper import LinkedinJobFinder
from src.config import AppConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = AppConfig()


class TestLinkedinJobFinder(unittest.TestCase):
    def setUp(self):
        self.job_finder = LinkedinJobFinder(headless=True)
        
        
    @patch('selenium.webdriver.Chrome')
    def test_jobfinder_start_success(self, mock_webdriver):
        mock_card = Mock()
        mock_card.find_element.side_effect = lambda by, name: Mock(text={
            'job-card-list__title': 'Software Engineer',
            'job-card-container__company-name': 'Tech Corp',
            'job-card-container__metadata-item': 'New York, NY',
            'jobs-description-content__text': 'Job description here'
        }[name])
        
        mock_driver = mock_webdriver.return_value
        mock_driver.find_elements.return_value = [mock_card]
        
        results = self.job_finder.start("https://linkedin.com/jobs", limit=1)
        print(f"Results from Linkedin (Mocked): {results}")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Software Engineer')
        self.assertEqual(results[0]['company'], 'Tech Corp')
        self.assertEqual(results[0]['location'], 'New York, NY')
        #self.assertEqual(results[0]['description'], 'Job description here')

    class TestIntegration(unittest.TestCase):
        def setUp(self):
            self.linkedin_url = config.config['linkedin']['search-url']
            self.job_finder = LinkedinJobFinder()

        def test_real_job_search(self):
            results = self.job_finder.start(self.linkedin_url, limit=2)
            logger.info(f"\nResults from Linkedin (Real): {results}")
            
            self.assertTrue(len(results) > 0)
            for job in results:
                self.assertIn('title', job)
                self.assertIn('company', job)
                self.assertIn('location', job)
                self.assertIn('description', job)
                self.assertTrue(all(isinstance(value, str) for value in job.values()))

if __name__ == '__main__':
    unittest.main()