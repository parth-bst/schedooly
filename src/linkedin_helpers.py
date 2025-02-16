from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from src.config import AppConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

config = AppConfig()

def linkedin_login(driver):
    """Handle LinkedIn login process"""
    logger.info("Logging into LinkedIn...")
    try:
        driver.get("https://www.linkedin.com/login")
        wait = WebDriverWait(driver, 10)
        
        # Enter credentials
        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        password_field = driver.find_element(By.ID, "password")
        
        email_field.send_keys(config.config['linkedin']['email'])
        password_field.send_keys(config.config['linkedin']['password'])
        
        # Click login button
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise

def check_linkedin_login(driver) -> bool:
    """Check if user is logged into LinkedIn and login if needed"""
    logger.info("Checking LinkedIn login status...")
    try:
        driver.get("https://www.linkedin.com")
        wait = WebDriverWait(driver, 5)
        
        # Try to find elements that indicate logged-in state
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.global-nav__me-photo')))
            logger.info("Already logged into LinkedIn")
            return True
        except:
            logger.info("Not logged in, proceeding with login")
            linkedin_login(driver)
            return True
            
    except Exception as e:
        logger.error(f"Login check failed: {str(e)}")
        return False
