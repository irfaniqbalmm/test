import configparser
import os
from utils.db_util import *
from utils.db2 import *
from utils.postgres import *
from utils.mssql import *
from utils.oracle import *
from utils.logs import *
from utils.common import fetch_host_shortname

class DbOperations:
    def __init__(self, db, tablespace_option):

        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.parser.read(current_dir + '/config/data.config')
        self.deploymentLogs = DeploymentLogs()
        self.tablespace_option = tablespace_option
        self.tablespace_dict = {'tablespace_option': False}

        print(f'DbOperations starting with db: {db} and table space option : {tablespace_option}')

        if db.lower() == 'db2':
            self.db2_server = self.parser.get('DB2', 'DATABASE_SERVERNAME').strip('"')
            self.db2_gcd_db_name = self.parser.get('DB2', 'GCD_DB_NAME').strip('"') + fetch_host_shortname() 
            self.db2_os1_db_name = self.parser.get('DB2', 'OS1_DB_NAME').strip('"') + fetch_host_shortname()
            self.db2_icn_db_name = self.parser.get('DB2', 'ICN_DB_NAME').strip('"') + fetch_host_shortname()
            self.db2_src_path = self.parser.get('DATABASE_CONFIG', 'db2_src_path').strip()
            self.db2_dest_path = self.parser.get('DATABASE_CONFIG', 'db2_dest_path').strip()
            self.db2_user = self.parser.get('DB2', 'GCD_DB_USER_NAME').strip('"')
            self.db2_password = self.parser.get('DATABASE_CONFIG', 'db2_password').strip()
            self.db2_directory_path = self.parser.get('DATABASE_CONFIG', 'db2_directory_path').strip()
            self.db2_force_drop_db_script = self.parser.get('DATABASE_CONFIG', 'db2_force_drop_db_script').strip()
            self.db2_create_db_script = self.parser.get('DATABASE_CONFIG', 'db2_create_db_script').strip()
            self.db2_createICNDB = self.parser.get('DATABASE_CONFIG', 'db2_createICNDB').strip()
            self.db2_createGCDDB = self.parser.get('DATABASE_CONFIG', 'db2_createGCDDB').strip()
            self.db2_createOS1DB = self.parser.get('DATABASE_CONFIG', 'db2_createOS1DB').strip()
            self.db2()
        
        elif db.lower() == 'postgres':
            self.postgres_server = self.parser.get('POSTGRES', 'DATABASE_SERVERNAME').strip('"')
            self.postgres_gcd_db_name = self.parser.get('POSTGRES', 'GCD_DB_NAME').strip('"') + fetch_host_shortname() 
            self.postgres_os1_db_name = self.parser.get('POSTGRES', 'OS1_DB_NAME').strip('"') + fetch_host_shortname() 
            self.postgres_icn_db_name = self.parser.get('POSTGRES', 'ICN_DB_NAME').strip('"') + fetch_host_shortname() 
            self.postgres_src_path = self.parser.get('DATABASE_CONFIG', 'postgres_src_path').strip()
            self.postgres_dest_path = self.parser.get('DATABASE_CONFIG', 'postgres_dest_path').strip()
            self.postgres_user = self.parser.get('DATABASE_CONFIG', 'postgres_user').strip()
            self.postgres_password = self.parser.get('DATABASE_CONFIG', 'postgres_password').strip()
            self.postgres_createICNDB = self.parser.get('DATABASE_CONFIG', 'postgres_createICNDB').strip()
            self.postgres_createGCDDB = self.parser.get('DATABASE_CONFIG', 'postgres_createGCDDB').strip()
            self.postgres_createOS1DB = self.parser.get('DATABASE_CONFIG', 'postgres_createOS1DB').strip()

            if  self.tablespace_option.lower() == 'yes':
                self.tablespace_dict = {'tablespace_option': True,
                                   'tab_index_loc': self.parser.get('POSTGRES', 'OS1_DB_NAME').strip('"').lower() + fetch_host_shortname().lower() + self.parser.get('POSTGRES', 'OS1_DB_INDEX_STORAGE_LOCATION').strip('"') + fetch_host_shortname().lower(),
                                   'tab_table_loc': self.parser.get('POSTGRES', 'OS1_DB_NAME').strip('"').lower() + fetch_host_shortname().lower() + self.parser.get('POSTGRES', 'OS1_DB_TABLE_STORAGE_LOCATION').strip('"') + fetch_host_shortname().lower(),
                                   'tab_lob_loc': self.parser.get('POSTGRES', 'OS1_DB_NAME').strip('"').lower() + fetch_host_shortname().lower() + self.parser.get('POSTGRES', 'OS1_DB_LOB_STORAGE_LOCATION').strip('"') + fetch_host_shortname().lower()}
            self.postgres()
        
        elif db.lower() == 'mssql':
            self.mssql_src_path = self.parser.get('DATABASE_CONFIG', 'mssql_src_path').strip()
            self.mssql_server = self.parser.get('MSSQL', 'DATABASE_SERVERNAME').strip('"')
            self.mssql_port = self.parser.get('MSSQL', 'DATABASE_PORT').strip('"')
            self.mssql_uid = self.parser.get('DATABASE_CONFIG', 'mssql_uid').strip()
            self.mssql_password = self.parser.get('DATABASE_CONFIG', 'mssql_password').strip()
            self.mssql_gcd_db_name = self.parser.get('MSSQL', 'GCD_DB_NAME').strip('"') + fetch_host_shortname() 
            self.mssql_os1_db_name = self.parser.get('MSSQL', 'OS1_DB_NAME').strip('"') + fetch_host_shortname()
            self.mssql_icn_db_name = self.parser.get('MSSQL', 'ICN_DB_NAME').strip('"') + fetch_host_shortname()
            self.mssql_createICNDB = self.parser.get('DATABASE_CONFIG', 'mssql_createICNDB').strip()
            self.mssql_createGCDDB = self.parser.get('DATABASE_CONFIG', 'mssql_createGCDDB').strip()
            self.mssql_createOS1DB = self.parser.get('DATABASE_CONFIG', 'mssql_createOS1DB').strip()
            self.mssql_install_drivers_script_file = self.parser.get('DATABASE_CONFIG', 'mssql_install_drivers_script_file').strip()
            self.mssql()
        
        elif db.lower() == 'oracle':
            self.oracle_src_path = self.parser.get('DATABASE_CONFIG', 'oracle_src_path').strip()
            self.oracle_createICNDB = self.parser.get('DATABASE_CONFIG', 'oracle_createICNDB').strip()
            self.oracle_createGCDDB = self.parser.get('DATABASE_CONFIG', 'oracle_createGCDDB').strip()
            self.oracle_createOS1DB = self.parser.get('DATABASE_CONFIG', 'oracle_createOS1DB').strip()
            self.oracle_server = self.parser.get('DATABASE_CONFIG', 'oracle_server').strip()
            self.oracle_dest_path = self.parser.get('DATABASE_CONFIG', 'oracle_dest_path').strip()
            self.oracle_password = self.parser.get('DATABASE_CONFIG', 'oracle_password').strip()
            self.oracle_login_user = self.parser.get('DATABASE_CONFIG', 'oracle_login_user').strip()
            self.oracle_login_password =  self.parser.get('DATABASE_CONFIG', 'oracle_login_password').strip()
            self.oracle_port = self.parser.get('DATABASE_CONFIG', 'oracle_port').strip()
            self.oracle_service_name = self.parser.get('DATABASE_CONFIG', 'oracle_service_name').strip()
            self.oracle_gcd_db_name = self.parser.get('ORACLE', 'GCD_DB_USER_NAME').strip('"') + fetch_host_shortname() 
            self.oracle_os1_db_name = self.parser.get('ORACLE', 'OS1_DB_USER_NAME').strip('"') + fetch_host_shortname()
            self.oracle_icn_db_name = self.parser.get('ORACLE', 'ICN_DB_USER_NAME').strip('"') + fetch_host_shortname()
            self.oracle_execute_GCDDB = self.parser.get('DATABASE_CONFIG', 'oracle_execute_GCDDB').strip()
            self.oracle_execute_ICNDB = self.parser.get('DATABASE_CONFIG', 'oracle_execute_ICNDB').strip()
            self.oracle_execute_OS1DB = self.parser.get('DATABASE_CONFIG', 'oracle_execute_OS1DB').strip()
            self.tablespace_dict = {'tablespace_option': True,
                                'tab_index_loc': 'INDEX_' + fetch_host_shortname(),
                                'tab_table_loc': 'TABLE_' + fetch_host_shortname(),
                                'tab_lob_loc': 'LOB_' + fetch_host_shortname()}
            if self.tablespace_option.lower() == 'yes':
                self.tablespace_dict = {'tablespace_option': True,
                                    'tab_index_loc': self.parser.get('ORACLE', 'OS1_DB_USER_NAME').strip('"').lower() + fetch_host_shortname().upper() + self.parser.get('ORACLE', 'OS1_DB_INDEX_STORAGE_LOCATION').strip('"').lower() + fetch_host_shortname(),
                                    'tab_table_loc': self.parser.get('ORACLE', 'OS1_DB_USER_NAME').strip('"').lower() + fetch_host_shortname().upper() + self.parser.get('ORACLE', 'OS1_DB_TABLE_STORAGE_LOCATION').strip('"').lower() + fetch_host_shortname(),
                                    'tab_lob_loc': self.parser.get('ORACLE', 'OS1_DB_USER_NAME').strip('"').lower() + fetch_host_shortname().upper() + self.parser.get('ORACLE', 'OS1_DB_LOB_STORAGE_LOCATION').strip('"').lower() + fetch_host_shortname()}
            self.oracle()

        # Checking external db is enabled or not
        elif db.lower() == 'postgres_metastore':
            self.postgres_server = self.parser.get('POSTGRES', 'DATABASE_SERVERNAME').strip('"')
            self.postgres_im_db_name = self.parser.get('CP4BA_MSAD', 'CP4BA.IM_EXTERNAL_POSTGRES_DATABASE_NAME').strip('"') + fetch_host_shortname().lower()
            self.postgres_zen_db_name = self.parser.get('CP4BA_MSAD', 'CP4BA.ZEN_EXTERNAL_POSTGRES_DATABASE_NAME').strip('"') + fetch_host_shortname().lower()
            self.postgres_bts_db_name = self.parser.get('CP4BA_MSAD', 'CP4BA.BTS_EXTERNAL_POSTGRES_DATABASE_NAME').strip('"') + fetch_host_shortname().lower()
            self.postgres_src_path = self.parser.get('DATABASE_CONFIG', 'postgres_src_path').strip()
            self.postgres_dest_path = self.parser.get('DATABASE_CONFIG', 'postgres_dest_path').strip()
            self.postgres_user = self.parser.get('DATABASE_CONFIG', 'postgres_user').strip()
            self.postgres_password = self.parser.get('DATABASE_CONFIG', 'postgres_password').strip()
            self.postgres_createIM = self.parser.get('DATABASE_CONFIG', 'postgres_createIM').strip()
            self.postgres_createZEN = self.parser.get('DATABASE_CONFIG', 'postgres_createZEN').strip()
            self.postgres_createBTS = self.parser.get('DATABASE_CONFIG', 'postgres_createBTS').strip()
            self.tablespace_dict = {'tablespace_option': False}
            self.postgres_metastore()

    def db2(self):
        """
            Name: db2
            Author: Dhanesh
            Desc: To call the respective functions to drop/clean up the existing db2 databases with the same name and create new db2 databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """
        db_names = [self.db2_gcd_db_name, self.db2_os1_db_name, self.db2_icn_db_name]
        db_file_names = {self.db2_gcd_db_name: 'createGCDDB.sql', self.db2_os1_db_name: 'createOS1DB.sql', self.db2_icn_db_name: 'createICNDB.sql'}
        db_files = [self.db2_createICNDB, self.db2_createGCDDB, self.db2_createOS1DB]
        get_db_script_file(db_files, self.db2_src_path, self.deploymentLogs)
        copy_files_to_ssh(self.db2_server, self.db2_src_path, self.db2_dest_path, self.db2_password, self.deploymentLogs)
        drop_db2_database(self.db2_force_drop_db_script, db_names, self.db2_user, self.db2_directory_path, self.db2_server, self.db2_password, self.deploymentLogs)
        create_db2_database(self.db2_create_db_script, db_file_names, self.db2_server, self.db2_password, self.db2_user, self.deploymentLogs)
    
    def postgres(self):
        """
            Name: postgres
            Author: Dhanesh
            Desc: To call the respective functions to drop/clean up the existing postgres databases with the same name and create new postgres databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """
        postgres_db_names = [self.postgres_gcd_db_name, self.postgres_icn_db_name, self.postgres_os1_db_name]
        db_file_names = {self.postgres_gcd_db_name: 'createGCDDB.sql', self.postgres_icn_db_name: 'createICNDB.sql', self.postgres_os1_db_name: 'createOS1DB.sql'}
        db_files = [self.postgres_createICNDB, self.postgres_createGCDDB, self.postgres_createOS1DB]
        get_db_script_file(db_files, self.postgres_src_path,self.deploymentLogs)
        copy_files_to_ssh(self.postgres_server, self.postgres_src_path, self.postgres_dest_path, self.postgres_password, self.deploymentLogs)
        drop_postgres_database(postgres_db_names, self.postgres_user, self.postgres_server, self.postgres_password, self.deploymentLogs, self.tablespace_dict)
        create_postgres_database(db_file_names, self.postgres_server, self.postgres_password, self.postgres_user, self.deploymentLogs, self.tablespace_dict)
    
    def postgres_metastore(self):
        """
        Function name: create_sql
        Desc: Creating the sql statement file
        Params:
            db_name: Name of the database
        Return:
            True/False
        """
        postgres_db_names = [self.postgres_im_db_name, self.postgres_zen_db_name, self.postgres_bts_db_name]
        db_file_names = {self.postgres_im_db_name: 'createIM.sql', self.postgres_zen_db_name: 'createZEN.sql', self.postgres_bts_db_name: 'createBTS.sql'}
        db_files = [self.postgres_createIM, self.postgres_createZEN, self.postgres_createBTS]

        # Running operations ont he postgres db
        get_db_script_file(db_files, self.postgres_src_path,self.deploymentLogs)
        copy_files_to_ssh(self.postgres_server, self.postgres_src_path, self.postgres_dest_path, self.postgres_password, self.deploymentLogs)
        drop_postgres_database(postgres_db_names, self.postgres_user, self.postgres_server, self.postgres_password, self.deploymentLogs, self.tablespace_dict)
        create_postgres_database(db_file_names, self.postgres_server, self.postgres_password, self.postgres_user, self.deploymentLogs, self.tablespace_dict)
    


    def mssql(self):
        """
            Name: mssql
            Author: Dhanesh
            Desc: To call the respective functions to drop/clean up the existing mssql databases with the same name and create new mssql databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """
        createGCDDB = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/utils/db_operations/execute_mssql_scripts/createGCDDB.sql"
        createOS1DB = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/utils/db_operations/execute_mssql_scripts/createOS1DB.sql"
        createICNDB = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/utils/db_operations/execute_mssql_scripts/createICNDB.sql"
        db_names = [self.mssql_gcd_db_name, self.mssql_os1_db_name, self.mssql_icn_db_name]
        db_file_names = {self.mssql_gcd_db_name: createGCDDB, self.mssql_os1_db_name: createOS1DB, self.mssql_icn_db_name: createICNDB}
        db_files = [self.mssql_createICNDB, self.mssql_createGCDDB, self.mssql_createOS1DB]
        get_db_script_file(db_files, self.mssql_src_path,self.deploymentLogs)
        install_odbc_drivers(self.mssql_install_drivers_script_file, self.deploymentLogs)
        drop_mssql_db(db_names, self.mssql_server, self.mssql_port, self.mssql_uid, self.mssql_password, self.deploymentLogs)
        create_mssql_db(db_file_names, self.mssql_server, self.mssql_port, self.mssql_uid, self.mssql_password, self.deploymentLogs)


    def oracle(self):
        """
            Name: oracle
            Author: Dhanesh
            Desc: To call the respective functions to drop/clean up the existing oracle databases with the same name and create new oracle databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """

        db_files = [self.oracle_createICNDB, self.oracle_createGCDDB, self.oracle_createOS1DB]
        oracle_user_names = [self.oracle_gcd_db_name, self.oracle_os1_db_name, self.oracle_icn_db_name]
        oracle_db_file_names = {self.oracle_gcd_db_name: self.oracle_execute_GCDDB, self.oracle_icn_db_name: self.oracle_execute_ICNDB, self.oracle_os1_db_name: self.oracle_execute_OS1DB}
        get_db_script_file(db_files, self.oracle_src_path,self.deploymentLogs)
        copy_files_to_ssh(self.oracle_server, self.oracle_src_path, self.oracle_dest_path, self.oracle_password, self.deploymentLogs)
        drop_oracle_database(oracle_user_names, self.oracle_server, self.oracle_password, self.oracle_login_user, self.oracle_login_password, self.oracle_port, self.oracle_service_name, self.deploymentLogs, self.tablespace_dict)
        create_oracle_database(oracle_db_file_names, self.oracle_server, self.oracle_password, self.oracle_login_user, self.oracle_login_password, self.oracle_port, self.oracle_service_name, self.deploymentLogs)