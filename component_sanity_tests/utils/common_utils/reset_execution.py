import json
import os
import sys

from tomlkit import parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from component_sanity_tests.exceptions.sanity_exception import SanityTestException
from utils.clean_data import CleanFolder
from utils.logger import logger

class ResetExecutionData():
    """
    This class provides methods to reset various data folders and files
    related to the execution of sanity tests for a specific product.
    """
    def __init__(self, product):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initialize the ResetExecutionData class.
        Parameters:
            product (str): The name of the product for which execution data is to be reset.
        Returns:
            None
        """
        self.product = product.lower()
        self.clean_folder = CleanFolder()

    def reset_status_file(self, status_file):
        """
        Method name: reset_status_file
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Reset status file for the specified product by cleaning folders and resetting status file.
        Parameters:
            status_file (str): The path to the reset file.
        Returns:
            None
        """
        # Reading status data
        with open(status_file, "r") as file:
            status_data = json.load(file)

        for key in status_data:
            status_data[key] = "Not executed"

        # Save the modified data
        with open(status_file, "w") as file:
            json.dump(status_data, file, indent=4)

    def reset_execution_data(self, config_file):
        """
        Method name: reset_execution_data
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Reset execution data for the specified product by cleaning folders and resetting status file.
        Parameters: None
        Returns: None
        Raises:
            SanityTestException: If there is an error in reading the config file or resetting execution data.
        """
        try:
            logger.info("==========================================Starting reset of execution data==========================================")
            # Getting config data
            try : 
                with open(config_file, "r") as file : 
                    input_data = parse(file.read())
            except Exception as e :
                raise SanityTestException(f"Failed to read the toml file") from e 

            # clean downloads folder
            downloads_folder =  input_data[self.product]['download_path']
            logger.info(f"Cleaning downloads folder")
            self.clean_folder.clean_folder(downloads_folder)

            # clean screenshots folder
            screenshots_folder =  input_data[self.product]['screenshot_path']
            logger.info(f"Cleaning screenshots folder")
            self.clean_folder.clean_folder(screenshots_folder)

            # reset status json file
            generated_reports_folder = input_data[self.product]['generated_reports_path']
            status_file =  os.path.join(generated_reports_folder, f"{self.product}_status.json")
            logger.info(f"Resetting status file: {status_file}")
            self.reset_status_file(status_file)

            logger.info(f"Cleaning reports folder")
            self.clean_folder.clean_folder(generated_reports_folder)

            logger.info("==========================================Completed reset of execution data==========================================\n\n")

        except Exception as e:
            raise SanityTestException(f"Failed to reset execution data") from e 

if __name__ == "__main__":
    # TESTER CODE
    reset_execution = ResetExecutionData("ICCSAP")
    reset_execution.reset_execution_data()