import configparser
import sys
import os
import subprocess
import yaml
from tomlkit import parse
import pexpect

# Base directory for bvt script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, BASE_DIR)

from inputs import input_data

# Adding the path to cp4ba_proddeploy_automation/utils dynamically
PROD_DEPLOY_UTILS_PATH = os.path.abspath(os.path.join(BASE_DIR, "../cp4ba_proddeploy_automation/utils"))
sys.path.append(PROD_DEPLOY_UTILS_PATH)

import db_util
import oracle

# Adding the path to utils where logger.py exists (inside CP4BA_Package)
UTILS_PATH = os.path.join(BASE_DIR, "utils")
sys.path.append(UTILS_PATH)

from logger import logger
CONFIG_FILE = "./component_sanity_tests/config/config.toml"

class SanityDbConfigs:
    """
    This class has methods to provide the necessary permissions to required database users 
    and to delete any existing schema from the database tables.
    """
    def __init__(self):
        """
        Method name: __init__
        Author: Nusaiba K K (nusaiba.noushad@ibm.com)
        Description: Initialize the SANITY_DB_CONFIGS class.
        Parameters:
            None
        Returns:
            None
        """
        self.db_name = self.get_db_name_from_cr()
        with open(CONFIG_FILE, "r") as file :
            config = parse(file.read())
        build = config.get('configurations', 'build')
        deployment_type = config.get('configurations', 'deployment_type')
        self.DB = input_data.get_db_ldap(deployment_type, build)[0]
        
        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.path.abspath(os.path.join(BASE_DIR, "../cp4ba_proddeploy_automation"))
        self.parser.read(current_dir + '/config/data.config')
        
        if self.DB.lower() == "oracle":
            self.ssh_host = "oracle19svl1.fyre.ibm.com"
            self.password = "Admin@123123123"
            self.oracle_login_user = self.parser.get('DATABASE_CONFIG', 'oracle_login_user').strip()
            self.oracle_login_password =  self.parser.get('DATABASE_CONFIG', 'oracle_login_password').strip()
            self.oracle_port = self.parser.get('DATABASE_CONFIG', 'oracle_port').strip()
            self.oracle_service_name = self.parser.get('DATABASE_CONFIG', 'oracle_service_name').strip()
        
    def get_db_name_from_cr(self):
        """
        Method name: get_db_name_from_cr
        Author: Nusaiba K K (nusaiba.noushad@ibm.com)
        Description: Fetch the OS Database Name from the CR from OCP
        Parameters:
            None
        Returns:
            os database name
        """
        cr_content = subprocess.check_output(["oc", "get", "Content", "-o", "yaml"], universal_newlines=True)
        cr_content = yaml.safe_load(cr_content)
        try:
            components = cr_content.get('items', [])
            os_db = None
            for component in components:
                spec = component.get('spec', {})
                datasource_config = spec.get('datasource_configuration', {})
                os_dbs = [os_ds.get('database_name') for os_ds in datasource_config.get('dc_os_datasources', [])]
                if os_dbs:  # Ensure it's not empty
                    os_db = os_dbs[0]  # Take the first one
                    logger.info(f"DB name is : {os_db}")
                    break  # Exit loop after finding the first DB
        except Exception as e:
            logger.error("Couldn't find DB Name")
            logger.error(f"An exception occurred during fetch DB Name : {e}")
            os_db = None
        return os_db

    def replace_placeholder_in_sql(self,file_path,old_value,new_value):
        """
        Method name: replace_placeholder_in_sql
        Author: Nusaiba K K (nusaiba.noushad@ibm.com)
        Description: Replace the old value in the sql file provided with the new value
        Parameters:
            None
        Returns:
            None
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()            
            content = content.replace(old_value, new_value)
            with open(file_path, 'w') as file:
                file.write(content)            
            logger.info(f"Replaced placeholders in {file_path} with  {new_value}")
            
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error replacing placeholders in {file_path}: {str(e)}")
    
    def oracle_execute_sql_script(self, process, sql_file_path, log):
        """
        Method name: oracle_execute_sql_script
        Author: Nusaiba K K (nusaiba.noushad@ibm.com)
        Description: Execute the sql files in the oracle databse server
        Parameters:
            None
        Returns:
            None
        """
        try:
            oracle.login_to_oracle(process,self.ssh_host,self.oracle_login_user,self.oracle_login_password,self.oracle_port,self.oracle_service_name,logger)
            process.sendline(f"@{sql_file_path}")
            process.expect('UNLIMITED', timeout=60)
            log.info(f"SQL script execution output:\n{process.before.decode(errors='ignore')}")
        except Exception as e:
            log.error(f"Script execution failed: {str(e)}")
    
    def call_oracle_sql_script_execution_steps(self,sql_file_path,dest_path):
        
        
        san_db_config.replace_placeholder_in_sql(sql_file_path,"{DB_NAME}",self.db_name)
        dir_path = os.path.dirname(dest_path)
        process1 = db_util.connect_to_ssh(self.ssh_host, self.password, logger)
        process2 = db_util.copy_files_to_ssh(self.ssh_host,sql_file_path, dest_path, self.password, logger)
        process3 = db_util.grant_file_permission(dir_path, self.ssh_host, self.password,logger)
        process5 = san_db_config.oracle_execute_sql_script(process1,dest_path,logger )
    
    def db_config_main(self):
        """
        Method name: db_config_main
        Author: Nusaiba K K (nusaiba.noushad@ibm.com)
        Description: initialise the paths to the source file in the current directory and destination file in the oracle server 
        and perform the required operations to execute the file in the oracle server.
        Parameters:
            None
        Returns:
            None
        """
        if self.DB.lower() == "oracle":
            src_path = os.path.abspath(os.path.join(BASE_DIR, "../CP4BA_Package/component_sanity_tests/resources/ier/oracle_permission.sql"))
            dest_path = "/home/oracle/oracle_permissions.sql"
            san_db_config.call_oracle_sql_script_execution_steps(src_path,dest_path)


if __name__ == "__main__":
    san_db_config = SanityDbConfigs()
    san_db_config.db_config_main()
