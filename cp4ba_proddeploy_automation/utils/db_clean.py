import configparser
import os
from utils.db_util import *
from utils.db2 import *
from utils.postgres import *
from utils.mssql import *
from utils.oracle import *
from utils.logs import *
from utils.common import fetch_host_shortname
import yaml
import base64

class DbCleanup:
    def __init__(self, project, set_delete):

        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.parser.read(current_dir + '/config/data.config')
        self.deploymentLogs = DeploymentLogs()
        self.tablespace_dict = {'tablespace_option': False}
        self.project = project
        self.set_delete = set_delete

        try:
            self.deploymentLogs.logger.info(f'Project name : {project} Setting db data or delete operation : {set_delete}')
            if self.set_delete.strip() == 'delete':
                self.deploymentLogs.logger.info(f'Type of db is {self.parser.get('DATABASE_CONFIG', 'db_type')}')
                db = self.parser.get('DATABASE_CONFIG', 'db_type')
                if db.lower() == 'db2':
                    self.db2()
                elif db.lower() == 'postgresql':
                    self.postgres()
                elif db.lower() == 'sqlserver':
                    self.mssql()
                elif db.lower() == 'oracle':
                    self.oracle()
                elif db.lower() == 'postgres_metastore':
                    self.postgres_metastore()
            if self.set_delete == 'set':
                self.setdb_data()
        except Exception as e:
            self.deploymentLogs.logger.error(f'Error while fetching the data. Error is {e}')

    def base64_decode(self, value):
        """
            Name: base64_decode
            Desc: Decoding of the username and password
            Parameters:
                value : string
            Returns:
                Decoded data 
            Raises:
                none
        """
        try:
            self.deploymentLogs.logger.info(f"Base 64 decode {value}")
            string_bytes = base64.b64decode(value)
            self.deploymentLogs.logger.info(f"{string_bytes}")
            string = string_bytes.decode("ascii")
            self.deploymentLogs.logger.info(f"Decoded value is {string}")
            return string
        except Exception as e:
            self.deploymentLogs.logger.error(f'Decoding of the username and password failed. Error is {e}')
            raise Exception(f'Decoding of the username and password failed. Error is {e}')

    def setdb_data(self):
        """
            Name: setdb_data
            Desc: Set the data into data.config file
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """

        try:
            file_content = subprocess.check_output(["oc","get","Content","-o","yaml", "-n", self.project], universal_newlines=True)
            cr_data = yaml.safe_load(file_content)
            self.deploymentLogs.logger.info("Loaded CR data into cr_data variable.")
            # finding db type
            self.deploymentLogs.logger.info("Fetching Database details used... ")

            #Cheking the content available or not
            items = cr_data.get('items', [])
            if len(items) == 0:
                self.deploymentLogs.logger.info("No content available, indicating a starter deployment. No database cleanup required.")
                return False
            
            for item in items:
                spec = item.get('spec', {})
                db_config = spec.get('datasource_configuration', {})
                dc_gcd_datasource = db_config.get('dc_gcd_datasource', {})
                self.db_type = dc_gcd_datasource.get('dc_database_type', []).lower()
                self.server = db_config.get('dc_gcd_datasource').get('database_servername')
                self.port = db_config.get('dc_gcd_datasource').get('database_port')
                self.deploymentLogs.logger.info(f"Database and server details follows db_type = {self.db_type} \n server = {self.server} \n port = {self.port} \n")

                # # Table space
                self.parser.set('DATABASE_CONFIG', 'db_type', dc_gcd_datasource.get('dc_database_type', []).lower())
                if dc_gcd_datasource.get('dc_database_type', []).lower() != 'oracle':
                    self.deploymentLogs.logger.info(f"If the db type not oracle then setting the db names from the content yaml")
                    self.parser.set('DATABASE_CONFIG', 'gcd_db_name', db_config.get('dc_gcd_datasource').get('database_name'))
                    self.parser.set('DATABASE_CONFIG', 'icn_db_name', db_config.get('dc_icn_datasource').get('database_name'))
                    self.parser.set('DATABASE_CONFIG', 'os1_db_name', db_config.get('dc_os_datasources')[0].get('database_name'))
                    self.deploymentLogs.logger.info(f"DBs are : gcd_db_name: {db_config.get('dc_gcd_datasource').get('database_name')} \n icn_db_name: {db_config.get('dc_icn_datasource').get('database_name')} \n os1_db_name: {db_config.get('dc_os_datasources')[0].get('database_name')}")
                else:
                    file_content = subprocess.check_output(["oc","get","secret", "ibm-ban-secret", "-o","yaml", "-n",  self.project], universal_newlines=True)
                    cr_data = yaml.safe_load(file_content)
                    self.deploymentLogs.logger.info(f"icn_db_name: {self.base64_decode(cr_data.get('data').get('navigatorDBUsername')).upper()} ")
                    self.icn_db_name = self.base64_decode(cr_data.get('data').get('navigatorDBUsername'))

                    file_content = subprocess.check_output(["oc","get","secret", "ibm-fncm-secret", "-o","yaml", "-n",  self.project], universal_newlines=True)
                    cr_data = yaml.safe_load(file_content)
                    self.gcd_db_name = self.base64_decode(cr_data.get('data').get('gcdDBUsername'))
                    self.os1_db_name = self.base64_decode(cr_data.get('data').get('os1DBUsername'))

                    self.deploymentLogs.logger.info(f"gcd_db_name: {self.gcd_db_name.upper()} ")
                    self.deploymentLogs.logger.info(f"os1_db_name: {self.os1_db_name.upper()} ")
                    self.deploymentLogs.logger.info(f"icn_db_name: {self.icn_db_name.upper()} ")
                    self.parser.set('DATABASE_CONFIG', 'gcd_db_name', self.gcd_db_name.upper())
                    self.parser.set('DATABASE_CONFIG', 'icn_db_name', self.icn_db_name.upper())
                    self.parser.set('DATABASE_CONFIG', 'os1_db_name', self.os1_db_name.upper())

                if (spec['initialize_configuration']['ic_obj_store_creation']['object_stores'][0].get('oc_cpe_obj_store_table_storage_location', 'None')) != 'None':
                    self.parser.set('DATABASE_CONFIG', 'tablespaceoption', 'true')

                self.parser.set('DATABASE_CONFIG', 'tablespace', spec['initialize_configuration']['ic_obj_store_creation']['object_stores'][0].get('oc_cpe_obj_store_table_storage_location', 'None'))
                self.parser.set('DATABASE_CONFIG', 'lobspace', spec['initialize_configuration']['ic_obj_store_creation']['object_stores'][0].get('oc_cpe_obj_store_lob_storage_location', 'None'))
                self.parser.set('DATABASE_CONFIG', 'indexspace', spec['initialize_configuration']['ic_obj_store_creation']['object_stores'][0].get('oc_cpe_obj_store_index_storage_location', 'None'))
                
                with open(current_dir + '/config/data.config', 'w') as configfile:
                    self.deploymentLogs.logger.info(f"Writing the db details into the data.config file")
                    self.parser.write(configfile)
        except Exception as e:
            self.deploymentLogs.logger.error(f'Updating the details into data.conf failed. Error is {e}')
            raise Exception(f'Updating the details into data.conf failed. Error is {e}')

    def db2(self):
        """
            Name: db2
            Desc: To call the respective functions to drop/clean up the existing db2 databases with the same name and create new db2 databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """
        try:
            self.db2_server = self.parser.get('DB2', 'DATABASE_SERVERNAME').strip('"')
            self.db2_gcd_db_name = self.parser.get('DATABASE_CONFIG', 'gcd_db_name')
            self.db2_os1_db_name = self.parser.get('DATABASE_CONFIG', 'os1_db_name')
            self.db2_icn_db_name = self.parser.get('DATABASE_CONFIG', 'icn_db_name')
            self.db2_src_path = self.parser.get('DATABASE_CONFIG', 'db2_src_path').strip()
            self.db2_dest_path = self.parser.get('DATABASE_CONFIG', 'db2_dest_path').strip()
            self.db2_user = self.parser.get('DB2', 'GCD_DB_USER_NAME').strip('"')
            self.db2_password = self.parser.get('DATABASE_CONFIG', 'db2_password').strip()
            self.db2_directory_path = self.parser.get('DATABASE_CONFIG', 'db2_directory_path').strip()
            self.db2_force_drop_db_script = self.parser.get('DATABASE_CONFIG', 'db2_force_drop_db_script').strip()
            
            db_names = [self.db2_gcd_db_name, self.db2_os1_db_name, self.db2_icn_db_name]
            self.deploymentLogs.logger.info(f"Data for db2 are self.db2_server: {self.db2_server}\n self.db2_gcd_db_name:{self.db2_gcd_db_name} \n self.db2_os1_db_name:{self.db2_os1_db_name} \n self.db2_icn_db_name;{self.db2_icn_db_name} \n self.db2_src_path: {self.db2_src_path} \n self.db2_dest_path:{self.db2_dest_path} \n self.db2_user:{self.db2_user} \n self.db2_password:{self.db2_password} \n self.db2_directory_path:{self.db2_directory_path} \n self.db2_force_drop_db_script : {self.db2_force_drop_db_script}")
            copy_files_to_ssh(self.db2_server, self.db2_src_path, self.db2_dest_path, self.db2_password, self.deploymentLogs)
            drop_db2_database(self.db2_force_drop_db_script, db_names, self.db2_user, self.db2_directory_path, self.db2_server, self.db2_password, self.deploymentLogs)
            return True
        except Exception as e:
            self.deploymentLogs.logger.error(f'DB2 operatio failed. Error is {e}')
            raise Exception(f'DB2 operatio failed. Error is {e}')

    def postgres(self):
        """
            Name: postgres
            Desc: To call the respective functions to drop/clean up the existing postgres databases with the same name and create new postgres databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """
        try:
            self.postgres_server = self.parser.get('POSTGRES', 'DATABASE_SERVERNAME').strip('"')
            self.postgres_gcd_db_name = self.parser.get('DATABASE_CONFIG', 'gcd_db_name').strip('"')
            self.postgres_os1_db_name = self.parser.get('DATABASE_CONFIG', 'os1_db_name').strip('"')
            self.postgres_icn_db_name = self.parser.get('DATABASE_CONFIG', 'icn_db_name').strip('"')
            self.postgres_user = self.parser.get('DATABASE_CONFIG', 'postgres_user').strip()
            self.postgres_password = self.parser.get('DATABASE_CONFIG', 'postgres_password').strip()

            if self.parser.get('DATABASE_CONFIG', 'tablespaceoption').lower() == 'true':
                self.tablespace_dict = {'tablespace_option': True,
                                    'tab_index_loc': self.parser.get('DATABASE_CONFIG', 'indexspace'), 
                                    'tab_table_loc': self.parser.get('DATABASE_CONFIG', 'tablespace'), 
                                    'tab_lob_loc': self.parser.get('DATABASE_CONFIG', 'lobspace')}
                    
            self.deploymentLogs.logger.info(f"Data for postgres are self.postgres_server:{self.postgres_server} \n self.postgres_gcd_db_name:{self.postgres_gcd_db_name} \n self.postgres_os1_db_name:{self.postgres_os1_db_name} \n self.postgres_icn_db_name:{self.postgres_icn_db_name} \n self.postgres_user:{self.postgres_user} \n self.postgres_password:{self.postgres_password} \n self.tablespace_dict: {self.tablespace_dict}")
            postgres_db_names = [self.postgres_gcd_db_name, self.postgres_icn_db_name, self.postgres_os1_db_name]
            drop_postgres_database(postgres_db_names, self.postgres_user, self.postgres_server, self.postgres_password, self.deploymentLogs, self.tablespace_dict)
            self.postgres_metastore()
            return True
        except Exception as e:
            self.deploymentLogs.logger.error(f'Postgres operatio failed. Error is {e}')
            raise Exception(f'Postgres operatio failed. Error is {e}')
    
    def postgres_metastore(self):
        """
        Function name: create_sql
        Desc: Creating the sql statement file
        Params:
            db_name: Name of the database
        Return:
            True/False
        """

        try:
            self.postgres_server = self.parser.get('POSTGRES', 'DATABASE_SERVERNAME').strip('"')
            self.postgres_im_db_name = self.parser.get('CP4BA_MSAD', 'CP4BA.IM_EXTERNAL_POSTGRES_DATABASE_NAME').strip('"') + fetch_host_shortname().lower()
            self.postgres_zen_db_name = self.parser.get('CP4BA_MSAD', 'CP4BA.ZEN_EXTERNAL_POSTGRES_DATABASE_NAME').strip('"') + fetch_host_shortname().lower()
            self.postgres_bts_db_name = self.parser.get('CP4BA_MSAD', 'CP4BA.BTS_EXTERNAL_POSTGRES_DATABASE_NAME').strip('"') + fetch_host_shortname().lower()
            self.postgres_user = self.parser.get('DATABASE_CONFIG', 'postgres_user').strip()
            self.postgres_password = self.parser.get('DATABASE_CONFIG', 'postgres_password').strip()
            self.tablespace_dict = {'tablespace_option': False}
            self.deploymentLogs.logger.info(f"Data for postgres_metastore self.postgres_server:{self.postgres_server} \n self.postgres_im_db_name: {self.postgres_im_db_name} \n self.postgres_zen_db_name:{self.postgres_zen_db_name} \n self.postgres_bts_db_name:{self.postgres_bts_db_name} \n self.postgres_user:{self.postgres_user} \n self.postgres_password:{self.postgres_password} \n self.tablespace_dict:{self.tablespace_dict}")
            postgres_db_names = [self.postgres_im_db_name, self.postgres_zen_db_name, self.postgres_bts_db_name]
            drop_postgres_database(postgres_db_names, self.postgres_user, self.postgres_server, self.postgres_password, self.deploymentLogs, self.tablespace_dict)
            return True
        except Exception as e:
            self.deploymentLogs.logger.error(f'postgres_metastore operatio failed. Error is {e}')
            raise Exception(f'postgres_metastore operatio failed. Error is {e}')
    
    def mssql(self):
        """
            Name: mssql
            Desc: To call the respective functions to drop/clean up the existing mssql databases with the same name and create new mssql databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """

        try:
            self.mssql_server = self.parser.get('MSSQL', 'DATABASE_SERVERNAME').strip('"')
            self.mssql_port = self.parser.get('MSSQL', 'DATABASE_PORT').strip('"')
            self.mssql_uid = self.parser.get('DATABASE_CONFIG', 'mssql_uid').strip()
            self.mssql_password = self.parser.get('DATABASE_CONFIG', 'mssql_password').strip()
            self.mssql_install_drivers_script_file = self.parser.get('DATABASE_CONFIG', 'mssql_install_drivers_script_file').strip()
            db_names = [self.parser.get('DATABASE_CONFIG', 'gcd_db_name'), self.parser.get('DATABASE_CONFIG', 'os1_db_name'), self.parser.get('DATABASE_CONFIG', 'icn_db_name')]
            self.deploymentLogs.logger.info(f"Data for mssql db_names  : {db_names}, self.mssql_server:{self.mssql_server} \n  self.mssql_port:{self.mssql_port} \n  self.mssql_uid:{self.mssql_uid} \n self.mssql_password:{self.mssql_password} \n  self.mssql_install_drivers_script_file:{self.mssql_install_drivers_script_file}")
            install_odbc_drivers(self.mssql_install_drivers_script_file, self.deploymentLogs)
            drop_mssql_db(db_names, self.mssql_server, self.mssql_port, self.mssql_uid, self.mssql_password, self.deploymentLogs)
            return True
        except Exception as e:
            self.deploymentLogs.logger.error(f'mssql operatio failed. Error is {e}')
            raise Exception(f'mssql operatio failed. Error is {e}')
        
    def oracle(self):
        """
            Name: oracle
            Desc: To call the respective functions to drop/clean up the existing oracle databases with the same name and create new oracle databases accordingly.
            Parameters:
                none
            Returns:
                none
            Raises:
                none
        """

        try:
            self.oracle_server = self.parser.get('DATABASE_CONFIG', 'oracle_server').strip()
            self.oracle_password = self.parser.get('DATABASE_CONFIG', 'oracle_password').strip()
            self.oracle_login_user = self.parser.get('DATABASE_CONFIG', 'oracle_login_user').strip()
            self.oracle_login_password =  self.parser.get('DATABASE_CONFIG', 'oracle_login_password').strip()
            self.oracle_port = self.parser.get('DATABASE_CONFIG', 'oracle_port').strip()
            self.oracle_service_name = self.parser.get('DATABASE_CONFIG', 'oracle_service_name').strip()
            self.oracle_gcd_db_name = self.parser.get('DATABASE_CONFIG', 'gcd_db_name').upper()
            self.oracle_os1_db_name = self.parser.get('DATABASE_CONFIG', 'os1_db_name').upper()
            self.oracle_icn_db_name = self.parser.get('DATABASE_CONFIG', 'icn_db_name').upper()
            if self.parser.get('DATABASE_CONFIG', 'tablespaceoption').lower() == 'true':
                self.tablespace_dict = {'tablespace_option': True,
                                    'tab_index_loc': self.parser.get('DATABASE_CONFIG', 'indexspace').upper(), 
                                    'tab_table_loc': self.parser.get('DATABASE_CONFIG', 'tablespace').upper(), 
                                    'tab_lob_loc': self.parser.get('DATABASE_CONFIG', 'lobspace').upper()}

            self.deploymentLogs.logger.info(f"Data for oracle self.oracle_server:{self.oracle_server} \n self.oracle_password:{self.oracle_password} \n self.oracle_login_user:{self.oracle_login_user} \n self.oracle_login_password:{self.oracle_login_password} \n  self.oracle_port:{self.oracle_port} \n self.oracle_service_name:{self.oracle_service_name} \n self.oracle_gcd_db_name:{self.oracle_gcd_db_name} \n self.oracle_os1_db_name:{self.oracle_os1_db_name} \n  self.oracle_icn_db_name:{self.oracle_icn_db_name} \n self.tablespace_dict:{self.tablespace_dict}")                           
            oracle_user_names = [self.oracle_gcd_db_name, self.oracle_os1_db_name, self.oracle_icn_db_name]
            drop_oracle_database(oracle_user_names, self.oracle_server, self.oracle_password, self.oracle_login_user, self.oracle_login_password, self.oracle_port, self.oracle_service_name, self.deploymentLogs, self.tablespace_dict)
            return True
        except Exception as e:
            self.deploymentLogs.logger.error(f'oracle operatio failed. Error is {e}')
            raise Exception(f'oracle operatio failed. Error is {e}')
