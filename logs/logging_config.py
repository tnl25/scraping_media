# logging_config.py
import logging
import os
from utils.tools import read_settings

def setup_logger(name: str) -> logging.Logger:
    SETTINGS = read_settings()
    
    logger = logging.getLogger(name)
    
    if not logger.hasHandlers():
        
        log_level_str = SETTINGS.get('gral', {}).get('log_level', 'DEBUG')
        
        log_level = getattr(logging, log_level_str.upper(), logging.DEBUG)
        
        log_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(log_dir, 'app.log')

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.setLevel(log_level)

    return logger
