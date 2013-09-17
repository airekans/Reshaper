'''
provide logger
to use:
from reshaper.log import logger
'''
import logging
import logging.config
import os


try:
    config_file = '~/.reshaper.cfg'
    logging.config.fileConfig(config_file)
except:
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sample_logging.conf')
    logging.config.fileConfig(config_file)
    
logger = logging.getLogger()