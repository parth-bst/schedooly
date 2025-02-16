from src.job_applyer.platform_handlers import handle_linkedin_platform, handle_workday_platform, handle_generic_platform, handle_taleo_platform
from src.job_tracker import log_application
from selenium import webdriver
import time
from src.config import AppConfig
import logging
from src.custom_webdriver import CustomWebDriver
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApplicationProcessor:
    def __init__(self):
        self.config = AppConfig()
        self.driver = CustomWebDriver().get_driver()

    def get_platform_handler(self, url):
        domain = urlparse(url).netloc
        if 'linkedin' in domain:
            return handle_linkedin_platform
        elif 'workday' in domain:
            return handle_workday_platform
        elif 'taleo' in domain:
            return handle_taleo_platform
        else:
            return handle_generic_platform

    def process_applications(self, job_artifacts):
        for job_key, job_data in job_artifacts.items():
            application_url = job_data['application_url']
            if not application_url:
                logger.warning(f"No application URL found for job: {job_key}")
                continue

            logger.info(f"Processing application for {job_data['company']} - {job_key}")
            
            platform_handler = self.get_platform_handler(application_url)
            
            try:
                platform_handler(
                    driver=self.driver,
                    url=application_url,
                    job_data=job_data
                )
                
                log_application(
                    company=job_data['company'],
                    job_title=job_data['job_details']['title'],
                    url=application_url,
                    status="success"
                )
                
                logger.info(f"Completed application for {job_data['company']}")
                time.sleep(10)  # Cooldown between applications
                
            except Exception as e:
                logger.error(f"Failed to process application for {job_key}: {str(e)}")
                log_application(
                    company=job_data['company'],
                    job_title=job_data['job_details']['title'],
                    url=application_url,
                    status="failed"
                )

    def cleanup(self):
        CustomWebDriver().quit()