'''
provide logger
to use:
from reshaper.log import logger
'''
import logging
#import logging.config


try:
    config_file = '~/.reshaper.cfg'
    logging.config.fileConfig(config_file)
except:
    fmt = '%(asctime)s %(filename)s: L%(lineno)d : %(levelname)s: %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(level = logging.NOTSET, format = fmt, datefmt = datefmt)
    
logger = logging.getLogger()