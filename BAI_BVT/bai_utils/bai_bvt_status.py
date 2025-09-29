import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from threading import Lock
from utils.logger import logger
from tomlkit import parse
from pathlib import Path
from utils.bvt_status import read_status, write_status
from bai_exception import BAIBVTException

def update_bai_status(component_name, status):
    """
        Method name: update_bai_status
        Author: Dhanesh
        Description: Update the bvt execution status in the json file
        Parameters:
            None
        Returns:
            None
    """
    try:
        with open("./BAI_BVT/resources/config.toml","r") as file :
            config = parse(file.read())
        generated_reports_path = config['paths']['generated_reports_path']
        logger.info("Acquired lock for updating status.")
        status_file = Path(generated_reports_path) / 'bvt_status.json'
        logger.info(f'bvt_status.json file path: {status_file}')
        status_data = read_status(status_file)
        # Update or add the component status
        status_data[component_name] = status
        logger.info(f"{component_name} status is : {status}.")
        write_status(status_data, status_file)
        logger.info(f"Status for component '{component_name}' updated successfully.")
        
    except Exception as e:
        raise BAIBVTException(f'Error while updating status for component {component_name}', e)