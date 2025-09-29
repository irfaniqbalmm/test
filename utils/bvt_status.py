import json
import os
import sys
from pathlib import Path

from tomlkit import parse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import logger

def read_status(status_file):
    """
    Method name: read_status
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Read the bvt execution status from the json file
    Parameters:
        None
    Returns:
        json data from file or empty dict
    """
    logger.info(f"Reading status from {status_file}...")
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as file:
                logger.info("Returning the contents of status file.")
                return json.load(file)
        except json.JSONDecodeError:
            # If the file is empty or corrupted, return an empty list
            logger.warning(f"The {status_file} file is empty/corrupted, returning an empty list.")
            return {}
        except Exception as e :
            logger.error(f"An exception occured during reading the {status_file} file : {e}")
    logger.info("The status file doesn't exists. Returning an empty list.")
    return {}

def write_status(status_data, status_file):
    """
        Method name: write_status
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Write the bvt execution status to the json file
        Parameters:
            None
        Returns:
            None
    """
    logger.info(f"Writing status to {status_file}...")
    try : 
        with open(status_file, 'w') as file:
            json.dump(status_data, file, indent=4)
    except Exception as e :
        logger.error(f"An exception occured during writing the status to file : {e}")

def update_status(testcase, status, product=None):
    """
        Method name: update_status
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Uodate the bvt execution status in the json file
        Parameters:
            testcase: The test case for which status has to be updated
            status: Status of the testcase
            product: Product for which the testcase is executed, (default=None)
        Returns:
            None
    """

    if product:
        with open("./component_sanity_tests/config/config.toml", "r") as file :
            config = parse(file.read())
        product = product.lower()
        generated_reports_path = config[product]['generated_reports_path']
        status_file = Path(generated_reports_path) / f'{product}_status.json'
    else:
        with open("./inputs/config.toml", "r") as file :
            config = parse(file.read())
        generated_reports_path = config['paths']['generated_reports_path']
        status_file = Path(generated_reports_path) / 'bvt_status.json'

    # Reading current status data
    status_data = read_status(status_file)

    # Update or add the testcase status
    status_data[testcase] = status
    logger.info(f"{testcase} status is : {status}.")

    write_status(status_data, status_file)
    logger.info(f"Status for '{testcase}' updated successfully.")
