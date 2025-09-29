import logging
import logging.config
from datetime import datetime
import os

class Logs:
    def __init__(self):

        #Adding the logging configuration
        cur_dir = os.getcwd()
        file_name = ('oc_commands{:%Y-%m-%d}.log'.format(datetime.now()))
        logging.basicConfig(filename=f'{cur_dir}/logs/{file_name}',
                    filemode='w',  # 'w' for overwrite, 'a' for append
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s')
        self.logger = logging.getLogger(__name__)