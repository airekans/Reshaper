'''
provide logger
to use:
from reshaper.log import logger
'''
import logging
#import logging.config


try:
    CONFIG_FILE = '~/.reshaper.cfg'
    logging.config.fileConfig(CONFIG_FILE)
except Exception:
    FMT = '%(asctime)s %(filename)s: L%(lineno)d : %(levelname)s: %(message)s'
    DATE_FMT = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level = logging.NOTSET, 
                        format = FMT, 
                        datefmt = DATE_FMT)
    
    
logger = logging.getLogger()