import logging
from logging.handlers import RotatingFileHandler
from typing import Union
from logging import Logger

def create_logger(log_file_path: str = 'app.log', log_level: Union[int, str] = logging.INFO) -> Logger:
    # Create logger
    logger = logging.getLogger('app_logger')
    logger.setLevel(log_level)

    # Create handlers
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=5)
    file_handler.setLevel(log_level)

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatters to handlers
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)

    return logger

# # Usage
# logger = create_logger()

# Example log messages
# logger.debug('This is a debug message')
# logger.info('This is an info message')
# logger.warning('This is a warning message')
# logger.error('This is an error message')
# logger.critical('This is a critical message')
