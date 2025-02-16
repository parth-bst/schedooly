from pathlib import Path
from pyhocon import ConfigFactory
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.config = {}
    
    def load(self, config_path):
        logger.info(f"Loading configuration from {config_path}")
        self.config = ConfigFactory.parse_file(config_path)

class AppConfig(Config):
    _instance = None
    
    def __new__(self, config_path="/Users/parthgupta/Desktop/code/openAI/schedooly/config/app.conf"):
        if self._instance is None:
            self._instance = super().__new__(self)
            self._instance.__init__(config_path)
        return self._instance
    
    def __init__(self, config_path="/Users/parthgupta/Desktop/code/openAI/schedooly/config/app.conf"):
        if not hasattr(self, 'config'):
            super().__init__()
            config_file = Path(config_path)
            if config_file.exists():
                self.load(config_file)
                logger.info(f"Configuration loaded successfully from {config_path}")
            else:
                logger.error(f"Configuration file not found at {config_path}")
                

def get_config():
    return AppConfig()
