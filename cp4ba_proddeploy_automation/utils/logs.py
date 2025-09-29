import logging
import logging.config
from datetime import datetime
import pytz

class DeploymentLogs:
    def __init__(self, logname='log'):

        # Set timezone to IST (Asia/Kolkata)
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_time = datetime.now(ist_timezone)

        # Creating the file name with date in IST
        file_name = (logname+'deployment-{:%Y-%m-%d}.log'.format(ist_time))

        # Adding the logging configuration
        logging.basicConfig(
            filename=f'logs/{file_name}',
            filemode='a',  # 'w' for overwrite, 'a' for append
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Custom formatter to ensure the log entries use IST time
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        formatter.converter = lambda *args: datetime.now(ist_timezone).timetuple()

        # Apply custom formatter to the logger
        self.logger = logging.getLogger(__name__)
