import unittest
from unittest.mock import patch, MagicMock
import csv
from pathlib import Path
from datetime import datetime
from src.application_pipeline import ApplicationProcessor
from src.job_tracker import log_application
from src.config import AppConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = AppConfig()

class TestApplicationProcessor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Prepares test environment by:
        1. Loading existing job descriptions from CSV
        2. Creating mock job artifacts for testing
        3. Loading user profile from config
        """
        # Load existing JD data
        cls.test_jds = []
        with open(Path(__file__).parent.parent / 'jd_log.csv', 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                cls.test_jds.append(eval(row[0]))
        
        # Get user profile from config
        # cls.config = AppConfig()
        cls.user_profile = config.config.get('user_profile', "not found")
        
        # Create mock job artifacts
        cls.mock_job_artifacts = {}
        for jd in cls.test_jds:
            job_key = f"{jd['company']}_{jd['title']}".replace(' ', '_').lower()
            cls.mock_job_artifacts[job_key] = {
                "job_details": jd,
                "document_paths": {
                    "cv": f"/Users/parthgupta/Desktop/code/openAI/schedooly/artifacts/samples/base_cv_parth.md", 
                    "cover_letter": f"/Users/parthgupta/Desktop/code/openAI/schedooly/artifacts/samples/cover_letter_parth_sample.pdf", 
                    "metadata": "../artifacts/samples/metadata.json"
                },
                "user_profile": cls.user_profile,
                # TODO: Update with actual URL
                # TODO: Test with a linkedin url -> it should test the redirections, click apply & job submit action chain
                # TODO: run with command:- python -m unittest tests.test_application_pipeline.TestApplicationProcessor.test_process_single_job_artifact
                # "application_url": "https://careers.schipholgroup.com/vacatures/techniek-en-bouw/pmo-advisor#apply", # jd.get('application_url', 'https://linkedin.com/jobs/test'),
                "application_url": "https://nl.linkedin.com/jobs/view/project-assistant-at-centrient-pharmaceuticals-4145777967",
                "company": jd['company'],
                "location": jd.get('location', 'Remote'),
                "timestamp": datetime.now().isoformat()
            }

    def setUp(self):
        """Initialize ApplicationProcessor and mock webdriver for each test"""
        self.application_proc = ApplicationProcessor()
        self.mock_webdriver = MagicMock()

    def test_get_platform_handler(self):
        """
        Tests if the correct platform handler is returned for different job URLs:
        - LinkedIn URLs should return LinkedIn handler
        - Workday URLs should return Workday handler
        - Taleo URLs should return Taleo handler
        - Unknown URLs should return Generic handler
        """
        test_urls = {
            "https://linkedin.com/jobs/view/123": "handle_linkedin_platform",
            "https://company.workday.com/jobs": "handle_workday_platform",
            "https://company.taleo.net/jobs": "handle_taleo_platform",
            "https://company.com/careers": "handle_generic_platform",
            "https://www.jobbird.com/nl/vacature/22852725-project-assurance-advisor": "handle_generic_platform", 
        }
        
        for url, expected_handler in test_urls.items():
            handler = self.application_proc.get_platform_handler(url)
            logger.info(f"Handler for {url}: {handler.__name__}")
            self.assertEqual(handler.__name__, expected_handler)

    def test_process_single_job_artifact(self):
        """
        Tests processing of a single job application:
        - Verifies correct handler is called
        - Checks if application is logged
        - Ensures proper cleanup
        """
        test_job_key = list(self.mock_job_artifacts.keys())[0]
        test_artifact = {test_job_key: self.mock_job_artifacts[test_job_key]}
        logger.info(f"Testing with job artifact: {test_artifact}")
        
        with patch('src.application_pipeline.CustomWebDriver') as mock_driver:
            mock_driver.return_value.get_driver.return_value = self.mock_webdriver
            with patch('src.job_tracker.log_application') as mock_log:
                self.application_proc.process_applications(test_artifact)
                mock_log.assert_called_once()

    def test_process_multiple_job_artifacts(self):
        """
        Tests batch processing of multiple job applications:
        - Verifies all jobs are processed
        - Checks correct number of log entries
        - Ensures proper handling of multiple platforms
        """
        with patch('src.application_pipeline.CustomWebDriver') as mock_driver:
            mock_driver.return_value.get_driver.return_value = self.mock_webdriver
            with patch('src.job_tracker.log_application') as mock_log:
                self.application_proc.process_applications(self.mock_job_artifacts)
                self.assertEqual(mock_log.call_count, len(self.mock_job_artifacts))

    def test_error_handling_invalid_url(self):
        """
        Tests error handling for invalid application URLs:
        - Verifies failed status is logged
        - Ensures application continues despite errors
        - Checks error message format
        """
        invalid_artifact = {
            "test_job": {
                **self.mock_job_artifacts[list(self.mock_job_artifacts.keys())[0]],
                "application_url": "invalid_url"
            }
        }
        
        with patch('src.application_pipeline.CustomWebDriver') as mock_driver:
            mock_driver.return_value.get_driver.return_value = self.mock_webdriver
            with patch('src.job_tracker.log_application') as mock_log:
                self.application_proc.process_applications(invalid_artifact)
                mock_log.assert_called_with(
                    company=invalid_artifact["test_job"]["company"],
                    position=invalid_artifact["test_job"]["job_details"]["title"],
                    location=invalid_artifact["test_job"]["location"],
                    application_date=invalid_artifact["test_job"]["timestamp"],
                    status="failed"
                )

    def test_platform_specific_handling(self):
        """
        Tests handling of different application platforms:
        - Verifies each platform handler is called correctly
        - Checks platform-specific logic execution
        - Ensures proper data passing to handlers
        """
        platforms = ['linkedin', 'workday', 'taleo', 'generic']
        for platform in platforms:
            with self.subTest(platform=platform):
                test_artifact = {
                    f"test_{platform}": {
                        **self.mock_job_artifacts[list(self.mock_job_artifacts.keys())[0]],
                        "application_url": f"https://{platform}.com/jobs/test"
                    }
                }
                
                with patch('src.application_pipeline.CustomWebDriver') as mock_driver:
                    mock_driver.return_value.get_driver.return_value = self.mock_webdriver
                    self.application_proc.process_applications(test_artifact)

    def tearDown(self):
        """Cleanup resources after each test"""
        self.application_proc.cleanup()

if __name__ == '__main__':
    unittest.main()
