import sys
import os

from tomlkit import parse
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import component_pages.logs.cp4a_logs as cp4a_logs
import component_pages.logs.content_logs as content_logs
from utils.bvt_status import update_status
from utils.logger import logger

def check_errors(file_path):
    """
    Method name: check_errors
    Description: Check if any errors are present in the operator logs using the keyword "FAILED!"
    Parameters:
        file_path : Path to logs
    Returns:
        True / False
    """
    logger.info("Checking if any errors are present in the operator logs using the keyword 'FAILED!'")
    try:
        logger.info("Opening operator log file.")
        with open(file_path, 'r',encoding="utf-8") as file:
            for line in file:
                if "FAILED!" in line or "fatal" in line:
                    logger.warning("Errors present in operator logs!!")
                    return True
        logger.info("No errors present in operator logs!!")
        return False
    except FileNotFoundError as e:
        logger.debug(f"An exception thrown file checking errors : {e}")
        logger.warning(f"Error: File '{file_path}' not found. Ignoring error.")
        return False

def logs_check():
    """
    Method name: logs_check
    Description: Get the operator logs and check if any errors are present in them
    Parameters:
        None
    Returns:
        logs_status : Status of logs : if any errors present or not
    """
    logger.info("==========================================Starting execution of downloading logs and checking for errors==========================================")
    with open("./inputs/config.toml","r") as file :
        config = parse(file.read())
    download_path = config['paths']['download_path']
    project_name = config['configurations']['project_name']

    LOGS_PATHS = {
        'content_latest': Path(download_path, 'logs' , 'content_operator_log_latest.txt'),
        'cp4a_latest': Path(download_path, 'logs', 'cp4a_operator_log_latest.txt')
    }

    logs_path = LOGS_PATHS['cp4a_latest'].parent
    if os.path.exists(logs_path):
        logger.info("Logs folder already exists.")
    else :
        logger.info("Creating logs folder.")
        os.mkdir(logs_path)
    
    logger.info("Getting the operator logs and check if any errors are present in them ...")
    logger.info("Trying to get CP4A operator logs ...")
    cp4a_logs.get_cp4a_logs(logs_path, project_name)
    logger.info("Trying to get Content operator logs ...")
    content_logs.get_content_logs(logs_path, project_name)

    # Check for errors in logs
    errors_present = any(check_errors(path) for path in LOGS_PATHS.values())
    logs_status = "Errors present in logs!" if errors_present else "No errors present in logs!"
    update_status("Logs",logs_status)
    return logs_status

if __name__ == "__main__":
    logs_status = logs_check()
