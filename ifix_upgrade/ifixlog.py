import logging
import logging.config
from datetime import datetime

class IfixLogs:
    def __init__(self, logfile):

        #Adding the logging configuration
        file_name = (logfile+'{:%Y-%m-%d}.log'.format(datetime.now()))
        logging.basicConfig(filename=f'{file_name}',
                    filemode='a',  # 'w' for overwrite, 'a' for append
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s')
        self.logger = logging.getLogger(__name__)