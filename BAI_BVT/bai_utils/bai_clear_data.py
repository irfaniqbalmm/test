import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json 
import shutil
from datetime import date
from datetime import datetime
from tomlkit import parse
from pathlib import Path
from utils.logger import logger

class DeleteData :
    def __init__(self) -> None:
        """
        Method name: __init__
        Author: Dhanesh
        Description: Initialises all the folders to be cleaned
        Parameters:
            None
        Returns:
            None
        """
        with open("./BAI_BVT/resources/config.toml","r") as file :
            config = parse(file.read())

        self.cluster = config['configurations']['cluster']
        self.project_name = config['configurations']['project_name']
        self.deployment_type = config['configurations']['deployment_type']
        self.screenshots_folder = config['paths']['screenshot_path']
        self.file_path = config['paths']['base_path']
        self.downloads_path = config['paths']['download_path']
        self.gen_report_path = config['paths']['generated_reports_path']
        self.operator_logs_path = Path(self.downloads_path) / "logs"
        self.reports_path = config['paths']['reports']
        self.bvt_status_file = Path(self.gen_report_path) / "bvt_status.json"

    def clean_folder(self,folder_path) :
        """
        Method name: clean_folder
        Author: Anisha Suresh
        Description: Clean the folder where previous run's datas are saved.
                     If the folder is not present create it.
        Parameters:
            folder_path : path to folder
        Returns:
            None
        """
        logger.info(f"Deleting the previous contents of {folder_path}...")
        # Check if the folder exists
        if os.path.exists(folder_path):
            # Get the list of files in the folder
            files = os.listdir(folder_path)

            # Iterate over the files and delete each one
            for file in files:
                file_path = os.path.join(folder_path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        os.rmdir(file_path)
                except Exception as e:
                    logger.error(f"Error deleting {file_path}. An exception occured during deletion : {e}")
            logger.info(f"All files inside {folder_path} have been deleted.")
        else:
            logger.info(f"{folder_path} folder doesn't exists. Creating it...")
            os.makedirs(folder_path)
            logger.info(f"{folder_path} folder created !")
    
    def clean_status_file(self) :
        """
        Method name: clean_status_file
        Author: Dhanesh
        Description: Re-initialises the bvt_status.json file to all the components as "Not executed" before a fresh run.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Re-initialising bvt_status.json file contents to 'Not executed'.")
        status_file = f'{self.gen_report_path}/bvt_status.json' 
        bvt_status = {
    "BAI_Content_Dashboard": "Not executed",
    "BAI_Navigator_Dashboard": "Not executed",
    "OCP_installed_operators": "Not executed",
    "OCP_access_configmaps": "Not executed",
    "access_info_contents": "Not executed",
    "bai_bpc_dashboard_login": "Not executed",
    "bai_bpc_dashboard_count": "Not executed",
    "Opensearch": "Not executed",
    "Logs": "Not executed",
    "liberty_version": "Not executed",
    "java_version": "Not executed",
    "java_build": "Not executed",
    "egress": "Not executed"
}
        try :
            with open(status_file, 'w') as file:
                json.dump(bvt_status, file, indent=4)
            logger.info("Re-initialized bvt_status.json file")
        except Exception as e :
            logger.error(f"An exception occured during resetting bvt_status.json file : {e}" )

    def reset_execution_data(self):
        logger.info("==========================================Starting reset of execution data==========================================")
        # Cleaning all previous logs
        self.clean_folder(self.operator_logs_path)
        # Cleaning all previous downloads
        self.clean_folder(self.downloads_path)
        # Cleaning all previous screenshots
        self.clean_folder(self.screenshots_folder)
        # Cleaning all previous reports
        self.clean_folder(self.gen_report_path)
        # Resetting bvt status file
        self.clean_status_file()
        logger.info("==========================================Completed reset of execution data==========================================\n\n")
        

if __name__=="__main__" :
    clean = DeleteData()
    clean.reset_execution_data()
