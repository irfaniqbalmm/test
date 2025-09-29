import configparser
from db_logs import *
import os
import sys
current_dir = os.getcwd()
print(current_dir)
sys.path.insert(0, current_dir + '/utils')
from oracle import * 
from db_util import *


class DbUtil:
    def __init__(self, db):

        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.parser.read(current_dir + '/DB_Util/db_config/dbdata.config')
        self.db_logs = DBOperationLogs()
        self.dbscript_dir_path = self.parser.get('COMMON_CONFIG', 'dbscript_dir_path').strip()
        self.gcd_db_name = self.parser.get('COMMON_CONFIG', 'GCD_DB_NAME').strip()
        self.os1_db_name = self.parser.get('COMMON_CONFIG', 'OS1_DB_NAME').strip()
        self.icn_db_name = self.parser.get('COMMON_CONFIG', 'ICN_DB_NAME').strip()
    
        if db.lower() == 'db2':
            self.db2_server = self.parser.get('DB2', 'DATABASE_SERVERNAME').strip('"')
            self.db2_gcd_db_name = self.parser.get('DB2', 'GCD_DB_NAME').strip('"')
            self.db2_os1_db_name = self.parser.get('DB2', 'OS1_DB_NAME').strip('"')
            self.db2_icn_db_name = self.parser.get('DB2', 'ICN_DB_NAME').strip('"')
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
            self.postgres_server = self.parser.get('DATABASE_CONFIG', 'postgres_database_server').strip()
            self.postgres_src_path = self.parser.get('DATABASE_CONFIG', 'postgres_src_path').strip()
            self.postgres_dest_path = self.parser.get('DATABASE_CONFIG', 'postgres_dest_path').strip()
            self.postgres_user = self.parser.get('DATABASE_CONFIG', 'postgres_user').strip()
            self.postgres_password = self.parser.get('DATABASE_CONFIG', 'postgres_password').strip()
            self.postgres()
        
        elif db.lower() == 'mssql':
            self.mssql_src_path = self.parser.get('DATABASE_CONFIG', 'mssql_src_path').strip()
            self.mssql_server = self.parser.get('MSSQL', 'DATABASE_SERVERNAME').strip('"')
            self.mssql_port = self.parser.get('MSSQL', 'DATABASE_PORT').strip('"')
            self.mssql_uid = self.parser.get('DATABASE_CONFIG', 'mssql_uid').strip()
            self.mssql_password = self.parser.get('DATABASE_CONFIG', 'mssql_password').strip()
            self.mssql_gcd_db_name = self.parser.get('MSSQL', 'GCD_DB_NAME').strip('"')
            self.mssql_os1_db_name = self.parser.get('MSSQL', 'OS1_DB_NAME').strip('"')
            self.mssql_icn_db_name = self.parser.get('MSSQL', 'ICN_DB_NAME').strip('"') 
            self.mssql_createICNDB = self.parser.get('DATABASE_CONFIG', 'mssql_createICNDB').strip()
            self.mssql_createGCDDB = self.parser.get('DATABASE_CONFIG', 'mssql_createGCDDB').strip()
            self.mssql_createOS1DB = self.parser.get('DATABASE_CONFIG', 'mssql_createOS1DB').strip()
            self.mssql_install_drivers_script_file = self.parser.get('DATABASE_CONFIG', 'mssql_install_drivers_script_file').strip()
            self.mssql()
        
        elif db.lower() == 'oracle':

            #Getting the parameters from the data config file.
            self.oracle_src_path = current_dir + self.parser.get('DATABASE_CONFIG', 'oracle_src_path').strip()
            self.oracle_server = self.parser.get('DATABASE_CONFIG', 'oracle_server').strip()
            self.oracle_dest_path = self.parser.get('DATABASE_CONFIG', 'oracle_dest_path').strip()
            self.oracle_password = self.parser.get('DATABASE_CONFIG', 'oracle_password').strip()
            self.oracle_login_user = self.parser.get('DATABASE_CONFIG', 'oracle_login_user').strip()
            self.oracle_login_password =  self.parser.get('DATABASE_CONFIG', 'oracle_login_password').strip()
            self.oracle_port = self.parser.get('DATABASE_CONFIG', 'oracle_port').strip()
            self.oracle_service_name = self.parser.get('DATABASE_CONFIG', 'oracle_service_name').strip()
            self.oracle_execute_GCDDB = self.parser.get('DATABASE_CONFIG', 'oracle_execute_GCDDB').strip()
            self.oracle_execute_ICNDB = self.parser.get('DATABASE_CONFIG', 'oracle_execute_ICNDB').strip()
            self.oracle_execute_OS1DB = self.parser.get('DATABASE_CONFIG', 'oracle_execute_OS1DB').strip()
            self.oracle()

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
        get_db_script_file(db_files, self.db2_src_path, self.db_logs)
        copy_files_to_ssh(self.db2_server, self.db2_src_path, self.db2_dest_path, self.db2_password, self.db_logs)
        drop_db2_database(self.db2_force_drop_db_script, db_names, self.db2_user, self.db2_directory_path, self.db2_server, self.db2_password, self.db_logs)
        create_db2_database(self.db2_create_db_script, db_file_names, self.db2_server, self.db2_password, self.db2_user, self.db_logs)
    
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
        postgres_db_names = [self.gcd_db_name, self.icn_db_name, self.os1_db_name]
        db_file_names = {self.gcd_db_name: 'createGCDDB.sql', self.icn_db_name: 'createICNDB.sql', self.os1_db_name: 'createOS1DB.sql'}
        get_db_script_file(self.dbscript_dir_path, self.postgres_src_path,self.db_logs)
        copy_files_to_ssh(self.postgres_server, self.postgres_src_path, self.postgres_dest_path, self.postgres_password, self.db_logs)
        drop_postgres_database(postgres_db_names, self.postgres_user, self.postgres_server, self.postgres_password, self.db_logs)
        create_postgres_database(db_file_names, self.postgres_server, self.postgres_password, self.postgres_user, self.db_logs)
    
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
        get_db_script_file(db_files, self.mssql_src_path,self.db_logs)
        install_odbc_drivers(self.mssql_install_drivers_script_file, self.db_logs)
        drop_mssql_db(db_names, self.mssql_server, self.mssql_port, self.mssql_uid, self.mssql_password, self.db_logs)
        create_mssql_db(db_file_names, self.mssql_server, self.mssql_port, self.mssql_uid, self.mssql_password, self.db_logs)


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

        oracle_user_names = [self.gcd_db_name, self.os1_db_name, self.icn_db_name]
        oracle_db_file_names = {self.gcd_db_name: self.oracle_execute_GCDDB, self.icn_db_name: self.oracle_execute_ICNDB, self.os1_db_name: self.oracle_execute_OS1DB}
        get_dbscripts(self.dbscript_dir_path, self.oracle_src_path, self.db_logs)
        copy_files_to_ssh(self.oracle_server, self.oracle_src_path, self.oracle_dest_path, self.oracle_password, self.db_logs)
        drop_oracle_database(oracle_user_names, self.oracle_server, self.oracle_password, self.oracle_login_user, self.oracle_login_password, self.oracle_port, self.oracle_service_name, self.db_logs)
        create_oracle_database(oracle_db_file_names, self.oracle_server, self.oracle_password, self.oracle_login_user, self.oracle_login_password, self.oracle_port, self.oracle_service_name, self.db_logs)

if __name__ == "__main__":
    db = sys.argv[1]
    DbUtil(db)