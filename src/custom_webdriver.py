import stat
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.config import get_config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CustomWebDriver:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomWebDriver, cls).__new__(cls)
            config = get_config()
            headless = config.config.get("selenium.headless", True) # ['selenium']['headless']
            cls._instance._init_driver(headless)
        return cls._instance
    
    def _init_driver(self, headless):
        config = get_config()
        selenium_config = config.config.get('selenium', {})
        
        self.options = webdriver.ChromeOptions()
        if selenium_config.get('headless', True):
            self.options.add_argument("--headless=new")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome")
        self.driver = webdriver.Chrome(options=self.options)
     
    def get_driver(self):
        return self.driver
    
    def quit(self):
        if self.driver:
            self.driver.quit()
            CustomWebDriver._instance = None
