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

class CleanFolder :
    def __init__(self) -> None:
        """
        Method name: __init__
        Author: Anisha Suresh
        Description: Initialises all the folders to be cleaned
        Parameters:
            None
        Returns:
            None
        """
        with open("./inputs/config.toml","r") as file :
            config = parse(file.read())

        self.cluster = config['configurations']['cluster']
        self.project_name = config['configurations']['project_name']
        self.deployment_type = config['configurations']['deployment_type']
        self.screenshots_folder = config['paths']['screenshot_path']
        self.file_path = config['paths']['base_path']
        self.downloads_path = config['paths']['download_path']
        self.gen_report_path = config['paths']['generated_reports_path']
        self.operator_logs_path = Path(self.downloads_path) / "logs"
        self.runtime_logs = Path(self.file_path) / "runtime_logs"
        self.reports_path = config['paths']['reports']
        self.bvt_status_file = Path(self.gen_report_path) / "bvt_status.json"

    def clean_folder(self, folder_path) :
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
                if "gitkeep" in file or ".json" in file:
                    continue
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

    def create_backup(self):
        """
        Method name: create_backup
        Author: Anisha Suresh
        Description: Create backup of the previous run
        Parameters:
            None
        Returns:
            None
        """
        def backup_folder(folder_path,backup_path,delete=False) :
            """
            Method name: backup_folder
            Author: Anisha Suresh
            Description: Create backup of the folder passed
            Parameters:
                folder_path : folder path to be backed up
                backup_path : path of back-up folder
            Returns:
                None
            """
            if os.path.exists(folder_path) :
                shutil.copytree(folder_path,backup_path,dirs_exist_ok=True)
                logger.info(f"Copied folder : {self.screenshots_folder}")
                if delete:
                    logger.info(f"Deleting folder : {self.runtime_logs}")
                    self.clean_folder(self.runtime_logs)
            else :
                logger.info(f"The folder : {folder_path} doean't exists. Skipping back-up.")

        logger.info("==========================================Starting creation of backup==========================================")
        logger.info("Creating back-up...")
        today = date.today()
        backup_folder_path = f"{self.file_path}/backup/{today}/{self.cluster}/{self.project_name}_{self.deployment_type}"
        if not os.path.exists(backup_folder_path) :
            os.makedirs(backup_folder_path)
            logger.info(f"Created folder : {backup_folder_path}")
        logger.info(f"Back-up folder is : {backup_folder_path}")
        backup_folder(self.screenshots_folder,f'{backup_folder_path}/screenshots')
        backup_folder(self.gen_report_path,f'{backup_folder_path}/generated_reports')
        backup_folder(self.operator_logs_path,f'{backup_folder_path}/operator_logs')
        backup_folder(self.runtime_logs,f'{backup_folder_path}/runtime_logs',True)
        shutil.copy('config.ini',backup_folder_path)
        logger.info("Copied file : config.ini")
        logger.info("Backing up completed!")
        logger.info("==========================================Completed creation of backup==========================================\n\n")

    def delete_backup(self) :
        """
        Method name: delete_backup
        Author: Anisha Suresh
        Description: Delete backup of the screenshots folder and the bvt_status.json file which are older than a week
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Proceeding to deletion of backups older than 5 days...")
        backup_folder = f"{self.file_path}/backup"
        files = os.listdir(backup_folder)
        for file in files :
            if not os.path.isdir(f'{backup_folder}/{file}'):
                continue
            timestamp_of_file_modification = os.path.getmtime(f'{backup_folder}/{file}')
            modification_date =  datetime.fromtimestamp(timestamp_of_file_modification)
            number_of_days = (datetime.now() - modification_date).days
            if number_of_days > 5 :
                shutil.rmtree(f'{backup_folder}/{file}')
                logger.warning(f"Deleted folder : {file} created on : {modification_date}")
        logger.info("Back-up deletion completed!")
    
    def clean_status_file(self) :
        """
        Method name: clean_status_file
        Author: Anisha Suresh
        Description: Re-initialises the bvt_status.json file to all the components as "Not executed" before a fresh run.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Re-initialising bvt_status.json file contents to 'Not executed'.")
        STATUS_FILE = f'{self.gen_report_path}/bvt_status.json' 
        bvt_status = {
    "BAI_Content_Dashboard" : "Not executed",
    "BAI_Navigator_Dashboard" : "Not executed",
    "ICCSAP" : "Not executed",
    "CMIS_CP4BA" : "Not executed",
    "CMIS_OCP" : "Not executed",
    "TM" : "Not executed",
    "IER" : "Not executed",
    "IER_Plugin" : "Not executed",
    "OCP_installed_operators": "Not executed",
    "OCP_access_configmaps": "Not executed",
    "OCP_init_configmap": "Not executed",
    "OCP_verify_configmap": "Not executed",
    "CPE_index_area" : "Not executed",
    "CPE_ICN_Object_store" : "Not executed",
    "OS_Tablespaces_Creation" : "Not executed",
    "CSS_search" : "Not executed",
    "CPE_Health_Page" : "Not executed",
    "CPE_Ping_page" : "Not executed",
    "CPE_Stateless_Health_Page" : "Not executed",
    "CPE_Stateless_Ping_Page" : "Not executed",
    "CPE_P8BPMREST": "Not executed",
    "FileNet_Process_Services_ping_page" : "Not executed",
    "FileNet_Process_Services_details_page" : "Not executed",
    "FileNet_P8_Content_Engine_Web_Service_page" : "Not executed",
    "FileNet_Process_Engine_Web_Service_page" : "Not executed",
    "Content_Search_Services_health_check" : "Not executed",
    "Stateless_FileNet_Process_Services_ping_page" : "Not executed",
    "Stateless_FileNet_Process_Services_details_page" : "Not executed",
    "Stateless_FileNet_P8_Content_Engine_Web_Service_page" : "Not executed",
    "Stateless_FileNet_Process_Engine_Web_Service_page" : "Not executed",
    "Stateless_Content_Search_Services_health_check" : "Not executed",
    "Opensearch" : "Not executed",
    "Navigator_desktops" : "Not executed",
    "Navigator_Second" : "Not executed",
    "CMOD" : "Not executed",
    "CM8" : "Not executed",
    "Graphql" : "Not executed",
    "Logs" : "Not executed",
    "liberty_version" : "Not executed",
    "java_version" : "Not executed",
    "java_build" : "Not executed",
    "egress" : "Not executed",
    "fips": "Not executed",
    "OC_Automations" : "Not executed",
    "JVM_Custom_Options" : "Not executed",
    "FISMA" : "Not executed"
}
        try :
            with open(STATUS_FILE, 'w') as file:
                json.dump(bvt_status, file, indent=4)
            logger.info("Re-initialized bvt_status.json file")
        except Exception as e :
            logger.error(f"An exception occured during resetting bvt_status.json file : {e}" )

    def reset_execution_data(self):
        logger.info("==========================================Starting reset of execution data==========================================")
        # Deleting backups older than 5 days
        self.delete_backup()
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
    clean = CleanFolder()
    clean.reset_execution_data()
