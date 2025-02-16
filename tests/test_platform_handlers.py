import unittest
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from src.job_applyer.platform_handlers import handle_linkedin_platform, handle_generic_platform
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPlatformHandlers(unittest.TestCase):
    def setUp(self):
        self.mock_driver = MagicMock()
        self.test_url = "https://nl.linkedin.com/jobs/view/project-assistant-at-centrient-pharmaceuticals-4145777967"
        self.test_job_data = {
            "document_paths": {
                "cv": f"/Users/parthgupta/Desktop/code/openAI/schedooly/artifacts/samples/base_cv_parth.md", 
                "cover_letter": f"/Users/parthgupta/Desktop/code/openAI/schedooly/artifacts/samples/cover_letter_parth_sample.pdf", 
                "metadata": "../artifacts/samples/metadata.json"
            },
            "user_profile": {
                "name" : "Somya Verma",
                "email" : "somya.verma@gmail.com",
                "phone" : "+1234567890",
                "linkedin" : "linkedin.com/in/somya-verma",
                "portfolio" : "somya-verma.com",
                "location" : "Amsterdam, Netherlands",
                "preferred_work_type" : "hybrid",
                "years_of_experience" : "5",
                "current_title" : "Project Coordinator",
                "education_level" : "Bachelor's Degree",
                "languages" : ["English", "Dutch"],
                "visa" : "partner dependent Work Permit",
            },
            "application_url": self.test_url,
            "company": "Test Company",
            "location": "Remote",
            "timestamp": "2022-01-01T00:00:00"
        }

    def test_linkedin_handler_real_execution(self):
        """Test LinkedIn handler with real execution and minimal mocking"""
        handle_linkedin_platform(self.mock_driver, self.test_job_data["application_url"], self.test_job_data)
        
        # Verify the driver navigated to the correct URL
        self.mock_driver.get.assert_called_with(self.test_job_data["application_url"])

    
    def test_linkedin_easy_apply_flow(self):
        """Test LinkedIn Easy Apply functionality"""
        with patch('src.job_applyer.platform_handlers.check_linkedin_login'):
            with patch('src.job_applyer.platform_handlers.try_linkedin_easy_apply') as mock_easy_apply:
                mock_easy_apply.return_value = True
                
                handle_linkedin_platform(self.mock_driver, self.test_url, self.test_job_data)
                
                self.mock_driver.get.assert_called_with(self.test_url)
                mock_easy_apply.assert_called_once()

    # this saves LLM call
    # for Regular linkedin flow
    def test_linkedin_handler_with_custom_form_data(self):
        """Test LinkedIn handler with custom form analysis data"""
        # TODO: Update these values if required
        custom_form_data = {'email': '.email_input', 'cv': '.resume-upload', 'cover_letter': '.file-upload', 
                            'first_name': '.candidate-first__name', 'last_name': '.candidate-last__name', 
                            'phone': '.candidate-phone', 'address': '.candidate-address', 
                            'required': ['email', 'cv', 'first_name', 'last_name', 'phone']} 
        
        with patch('src.job_applyer.platform_handlers.check_linkedin_login'), \
            patch('src.job_applyer.platform_handlers.try_linkedin_easy_apply') as mock_easy_apply, \
            patch('src.job_applyer.platform_handlers.analyze_form') as mock_analyze_form :
            
            mock_easy_apply.return_value = False
            mock_analyze_form.return_value = custom_form_data
            self.mock_driver.find_element.return_value.get_attribute.return_value = "<form>test form</form>"
            
            handle_linkedin_platform(self.mock_driver, self.test_url, self.test_job_data)
            
            mock_analyze_form.assert_called_once()
            
    def test_linkedin_regular_flow(self):
        """Test LinkedIn regular application flow when Easy Apply is not available"""
        with patch('src.job_applyer.platform_handlers.check_linkedin_login'):
            with patch('src.job_applyer.platform_handlers.try_linkedin_easy_apply') as mock_easy_apply:
                mock_easy_apply.return_value = False
                
                self.mock_driver.find_element.return_value.get_attribute.return_value = "<form></form>"
                
                handle_linkedin_platform(self.mock_driver, self.test_url, self.test_job_data)
                
                self.mock_driver.find_element.assert_any_call(By.TAG_NAME, 'form')

    def test_linkedin_popup_handling(self):
        """Test handling of LinkedIn popups during application"""
        with patch('src.job_applyer.platform_handlers.handle_popups') as mock_handle_popups:
            handle_linkedin_platform(self.mock_driver, self.test_url, self.test_job_data)
            
            mock_handle_popups.assert_called_once_with(self.mock_driver)

    def test_linkedin_form_filling(self):
        """Test form analysis and filling for LinkedIn applications"""
        with patch('src.job_applyer.platform_handlers.analyze_form') as mock_analyze:
            with patch('src.job_applyer.platform_handlers.fill_dynamic_form') as mock_fill:
                mock_analyze.return_value = {
                    "email": ".email_input",
                    "cv": ".resume-upload"
                }
                
                handle_linkedin_platform(self.mock_driver, self.test_url, self.test_job_data)
                
                mock_analyze.assert_called_once()
                mock_fill.assert_called_once()

    def test_generic_platform_form_detection(self):
        """Test form detection on generic platform"""
        self.mock_driver.find_elements.return_value = [MagicMock()]
        
        handle_generic_platform(self.mock_driver, self.test_url, self.test_job_data)
        
        self.mock_driver.find_elements.assert_called_with(By.TAG_NAME, 'form')

    def test_generic_platform_multiple_forms(self):
        """Test handling of multiple forms on generic platform"""
        mock_forms = [MagicMock(), MagicMock()]
        self.mock_driver.find_elements.return_value = mock_forms
        
        with patch('src.job_applyer.platform_handlers.fill_dynamic_form') as mock_fill:
            handle_generic_platform(self.mock_driver, self.test_url, self.test_job_data)
            
            self.assertEqual(mock_fill.call_count, len(mock_forms))

    def test_generic_platform_form_filling(self):
        """Test form filling functionality for generic platform"""
        mock_form = MagicMock()
        self.mock_driver.find_elements.return_value = [mock_form]
        
        with patch('src.job_applyer.platform_handlers.fill_dynamic_form') as mock_fill:
            handle_generic_platform(self.mock_driver, self.test_url, self.test_job_data)
            
            mock_fill.assert_called_once()

    def test_error_handling(self):
        """Test error handling for both platform handlers"""
        self.mock_driver.get.side_effect = TimeoutException()
        
        with self.assertRaises(Exception):
            handle_linkedin_platform(self.mock_driver, self.test_url, self.test_job_data)
            
        with self.assertRaises(Exception):
            handle_generic_platform(self.mock_driver, self.test_url, self.test_job_data)


if __name__ == '__main__':
    unittest.main()
