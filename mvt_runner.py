import sys

from utils.clean_data import CleanFolder
from utils.logger import logger
import utils.login as login
import inputs.input_data as input_data
import mvt.contentMVT as contentMVT
import utils.endpoints as endpoints

class MvtRunner():
    def __init__(self):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the class
        Parameters:
            None
        """
        self.clean = CleanFolder()

    def setup(self):
        """
        Method name: setup
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: The function performs the initial setup for running MVT
        Parameters:
            None
        """
        try: 
            login.ocp_login()
            input_data.initialize_input_data()
            endpoints.fetch_endpoints()
            self.clean.reset_execution_data()
        except Exception as e:
            logger.info(f"An exception occured during executing the prerequisite setups: {e}")

    def execute_mvt(self, product):
        """
        Method name: execute_mvt
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: The function executes the MVT
        Parameters:
            product: Name of the product for which MVT is executed
        """
        try: 
            contentMVT.mvt_runner(product, True)
        except Exception as e:
            logger.exception(f"An exception occured while executing MVT: {e}")

    def clean_up(self):
        """
        Method name: clean_up
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: The fucntion performs the final clean up after running MVT
        Parameters:
            None
        """
        try:
            self.clean.create_backup()
        except Exception as e:
            logger.info(f"An exception occured during creating the backup: {e}")
    
    def run_mvt(self, product):
        """
        Method name: run_mvt
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: The function sets up the env and executes the MVT
        Parameters:
            product: Name of the product for which MVT is executed
        """
        self.setup()
        self.execute_mvt(product)
        self.clean_up()

if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "CP4BA"
    mvt_runner = MvtRunner()
    mvt_runner.run_mvt(product=product)