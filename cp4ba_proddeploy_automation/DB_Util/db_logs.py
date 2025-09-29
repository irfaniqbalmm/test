import logging
import logging.config
from datetime import datetime

class DBOperationLogs:
    def __init__(self):

        #Adding the logging configuration
        file_name = ('database_operation{:%Y-%m-%d}.log'.format(datetime.now()))
        # file_name = ('prod_deployment{:%Y-%m-%d:%H-%M-%S}.log'.format(datetime.now()))
        logging.basicConfig(filename=f'DB_Util/dblogs/{file_name}',
                    filemode='w',  # 'w' for overwrite, 'a' for append
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
        self.logger = logging.getLogger(__name__)
