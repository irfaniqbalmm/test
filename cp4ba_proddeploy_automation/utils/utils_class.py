from configobj import ConfigObj
import configparser
from pathlib import Path
import subprocess
import pexpect
import time
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from utils.logs import * 
from utils.common import fetch_host_shortname, url_check, svl_machine, branch_check, tablespae_branch_check, vault_instana_branch_check
import os
import re
import sys
import git  #
from git import RemoteProgress
import shutil
import json

class CloneProgress(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        if message:
            print(message)

class CustomConfigObj(ConfigObj):
    """Custom configuration.

    This class used to update the _write_line method.
    While using this class we were getting the file o/p with space between the equal (=) sign
    and adding extra single quote around that
    """


    def __init__(self, *args, **kwargs):
        ConfigObj.__init__(self, *args, **kwargs)

    def _write_line(self, indent_string, entry, this_entry, comment):
        """
        Function name: _write_line
        Params:
            indent_string: property file details
            entry: Configuration file which saves all the data. dta.config in our case
            this_entry: By which we are splitting and creating the key
            comment: LDAP values we are passing as a parameter
        Return:
            String: String value without singlequote and space
        """

        """Write an individual line, for the write method"""
            # NOTE: the calls to self._quote here handles non-StringType values.
        if not self.unrepr:
            val = this_entry
        else:
            val = repr(this_entry)

        return '%s%s%s%s%s' % (indent_string,
                           self._decode_element(self._quote(entry, multiline=False)),
                           self._a_to_u('='),
                           val,
                           self._decode_element(comment))

class Utils:

    def __init__(self, config_dict):
        """
        Moving all the parameters to the dictionary
        """
        self.db = config_dict.get('db', '')
        self.ldap = config_dict.get('ldap', '')
        self.project_name = config_dict.get('project', 'cp')
        self.branch = config_dict.get('branch', 'CP4BA-24.0.1-IF001')
        stage_prod = config_dict.get('stage_prod', 'dev')
        self.cluster_name = config_dict.get('cluster_name', 'india')
        self.cluster_pass = config_dict.get('cluster_pass', '')
        self.separation_duty_on = config_dict.get('separation_duty_on', 'no').lower()
        self.fips = config_dict.get('fips', 'no').lower()
        self.external_db = config_dict.get('external_db', 'no').lower()
        self.extcrt = config_dict.get('extcrt', 'no').lower()
        self.git_branch = config_dict.get('git_branch', 'master')
        self.egress = config_dict.get('egress', 'No')
        self.multildap = config_dict.get('multildap', 'False')
        self.second_ldap_ssl_enabled = config_dict.get('second_ldap_ssl_enabled', 'False')
        self.multildap_post_init = config_dict.get('multildap_post_init', 'False')
        self.tablespaceoption = config_dict.get('tablespace_option', 'no')
        self.fisma = config_dict.get('fisma', 'NO')
        self.vault = config_dict.get('vault', 'NO')
        self.instana = config_dict.get('instana', 'NO')

        #Getting and setting the configuration details
        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.parser.read(current_dir + '/config/data.config')
        self.property_folder = self.parser.get('PREREQUISITES', 'PROPERTY_FOLDER')
        self.prereq_folder = self.parser.get('PREREQUISITES', 'PREREQ_FOLDER')
        self.script_folder = self.parser.get('PREREQUISITES', 'SCRIPT_FOLDER')
        self.property_script = self.script_folder + "cp4a-prerequisites.sh -m property"
        self.generatedcr_folder = self.parser.get('PREREQUISITES', 'GENERATED_CR')
        self.clone_folder = self.parser.get('PREREQUISITES', 'CLONE_FOLDER')
        self.clone_repo = self.parser.get('PREREQUISITES', 'CLONE_REPO')
        self.operand_namespace_suffix = self.parser.get('PREREQUISITES', 'OPERAND_NAMESPACE')
        self.storage_name = self.parser.get('PREREQUISITES', 'STORAGE_NAME')
        self.username = self.parser.get('CLUSTER_SETUP', 'username')
        self.password = self.parser.get('CLUSTER_SETUP', 'password')

        # Calling the logger
        self.logger = DeploymentLogs()
        print("The value of multildap is :",self.multildap)

        self.stage_prod = ''
        if stage_prod == 'dev':
            self.stage_prod = stage_prod
        

        # db_type_number method is not executed when db is none or empty. Example: In case of BAI Standalone
        if self.db not in [None, '']:
            self.db_type_number(self.db)
        else:
            self.logger.logger.warning('The database value is empty.')
            print('The database value is empty.')
        self.ldap_type_number(self.ldap)

        #Logging into the ocp
        if self.cluster_name == '' or self.cluster_pass == '':
            raise Exception("Please provide cluster name.")
        self.ocp_login()
        
        #Variable for Componentwisedeployement
        component_names = config_dict.get('component_names', 'all')
        self.logger.logger.info(f'Component selected is {component_names}')
        # If no component selected
        if (component_names == 'all' or component_names==''):
            component_names = ["content search services", "content management interoperability services", "ibm enterprise records","ibm content collector for sap", "business automation insights", "task manager"]
            self.logger.logger.info(f'Component selected Newly {component_names}, type= {type(component_names)}')
        else:
            component_names = component_names.split(",")
            self.logger.logger.info(f'Component selected by user {component_names}, type= {type(component_names)}')


        self.component_names=component_names
        self.logger.logger.info(f'Component name:: {self.component_names}')
        self.number_of_secrets=4
        self.logger.logger.info(f'self.db={self.db} \n self.ldap={self.ldap} \n self.project_name={self.project_name} \n self.branch={self.branch} \n stage_prod.={stage_prod} \n self.cluster_name={self.cluster_name} \n self.cluster_pass={self.cluster_pass} \n self.separation_duty_on={self.separation_duty_on} \n self.fips={self.fips} \n self.external_db={self.external_db} \n self.extcrt={self.extcrt} \n self.git_branch={self.git_branch} \n self.egress={self.egress} \n self.multildap={self.multildap} \n self.second_ldap_ssl_enabled={self.second_ldap_ssl_enabled} \n self.multildap_post_init={self.multildap_post_init} \n self.component_names={self.component_names} \n self.property_folder={self.property_folder} \n self.prereq_folder={self.prereq_folder} \n self.script_folder={self.script_folder} \n self.property_script={self.property_script} \n self.property_script={self.property_script} \n self.generatedcr_folder={self.generatedcr_folder} \n self.clone_folder={self.clone_folder} \n self.clone_repo={self.clone_repo} \n self.operand_namespace_suffix={self.operand_namespace_suffix} \n self.storage_name={self.storage_name} \n self.username={self.username} \n self.password={self.password} \n self.stage_prod={self.stage_prod } \n  self.tablespaceoption={self.tablespaceoption} \n')
        

    def ocp_login(self) :
        """
        Method name: ocp_login
        Description: Perform oc login using the kubeadmin user and password.
        Parameters:
            None
        Returns:
            True/False
        """
        login_command = ['oc', 'login', f'https://api.{self.cluster_name}.cp.fyre.ibm.com:6443', '-u', 'kubeadmin', '-p', f'{self.cluster_pass}', '--insecure-skip-tls-verify']
        try:

            result = subprocess.run(login_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = result.stdout.decode()
            self.logger.logger.info(f'Tried to login to cluster {self.cluster_name} and result is {result}')
            print(f'Tried to login to cluster {self.cluster_name} and result is {result}')
            return True
        except subprocess.TimeoutExpired:
            self.logger.logger.error(f'Login process timed out on the cluster {self.cluster_name}.')
            print(f'Login process timed out on the cluster {self.cluster_name}.')
            return False
        except Exception as e:
            self.logger.logger.error(f'Login process failed on the cluster {self.cluster_name} with error {e}.')
            print(f'Login process failed on the cluster {self.cluster_name} with error {e}.')
            return False

    def ldap_type_number(self, ldap):
        """
        Name: ldap_type_number
        Desc: To get the alias of the ldap selected.
        Parameters:
            ldap (string ): ldap type selected
        Returns:
            db_alias: db type
        """
        if ldap == 'msad':
            self.ldap_type_number = '1'
        elif ldap == 'sds':
            self.ldap_type_number = '2'
        elif ldap == 'pingdirectory':
            self.ldap_type_number = '3'
        else:
            self.ldap_type_number = '1'

    def db_type_number(self, db):
        """
        Name: db_type_number
        Desc: To get the alias of the db selected.
        Parameters:
            db_type (string ): Db type selected
        Returns:
            db_alias: db type
        """
        
        if self.branch[:4] in ["24.0"]: 
            db_dict = {'db2': '1', 'oracle': '2', 'mssql': '3', 'postgres': '4', 'postgresedb': '5'}
        else:
            db_dict = {
            'db2': '1',
            'Db2HADR': '2',
            'Db2RDS': '3',
            'Db2RDSHADR': '4',
            'oracle': '5',
            'mssql': '6',
            'postgres': '7',
            'postgresedb': '8'
        }
        if db in db_dict:
            self.db_type_number = db_dict[db]
        else:
            self.logger.logger.error(f'The database {db} is not present in the list of expected data bases {db_dict}')
            raise ValueError(f'The database {db} is not present in the list of expected data bases {db_dict}')

    def updater(self, config, splitter, ldap="", db="", file_name=False):
        """
        Function name: updater
        Params: 
            config: property file details
            parser: Configuration file which saves all the data. dta.config in our case
            splitter: By which we are splitting and creating the key
            ldap: LDAP values we are passing as a parameter
            db: Db type we are passing  
            file_name: In case of True and Oracle db it removes the first value in the array of key.
        Return:
            None

        """
        try:
            #Going over the configuration items and replacing with new values from data config
            for key, value in config.items():
                if db:
                    section = db
                    pro_key = key
                    if len(key.split(splitter)) > 1:
                        try:
                            # if db != 'ORACLE' or file_name == False:
                            key = key.split(splitter)[1]
                            if 'db.ORACLE_JDBC_URL' in config:
                                del(config['db.ORACLE_JDBC_URL'])

                            if db == 'POSTGRESQL' and file_name == True:
                                config['db.POSTGRESQL_SSL_CLIENT_SERVER'] = True
                            else:
                                if 'db.POSTGRESQL_SSL_CLIENT_SERVER' in config:
                                    del(config['db.POSTGRESQL_SSL_CLIENT_SERVER'])

                            if db == 'ORACLE' and file_name == True:
                                ## Provide the database server name or IP address of the database server.
                                del(config['db.DATABASE_SERVERNAME'])

                                ## Provide the database server port.  For Db2, the default is "50000".  For Oracle, the default is "1521"
                                del(config['db.DATABASE_PORT'])
                        except Exception as er:
                            pass
                else:
                    section = key.split(splitter)[0] + ldap
                    pro_key = key
                if self.parser.has_option(section, key): 
                    if key.lower() in ['gcd_db_name', 'os1_db_name', 'icn_db_name', 'cp4ba.im_external_postgres_database_name', 'cp4ba.bts_external_postgres_database_name', 'cp4ba.zen_external_postgres_database_name', 'os1_db_index_storage_location', 'os1_db_table_storage_location', 'os1_db_lob_storage_location']:
                        print(key , self.parser.get(section, key).strip('"') + fetch_host_shortname())
                        config[pro_key] = '"'+self.parser.get(section, key).strip('"') + fetch_host_shortname().lower()+'"'
                    else:
                        if (db == 'ORACLE') and (key.upper() in ['GCD_DB_USER_NAME', 'OS1_DB_USER_NAME', 'ICN_DB_USER_NAME', 'CP4BA.IM_EXTERNAL_POSTGRES_DATABASE_NAME', 'CP4BA.BTS_EXTERNAL_POSTGRES_DATABASE_NAME', 'CP4BA.ZEN_EXTERNAL_POSTGRES_DATABASE_NAME', 'OS1_DB_INDEX_STORAGE_LOCATION', 'OS1_DB_TABLE_STORAGE_LOCATION', 'OS1_DB_LOB_STORAGE_LOCATION']):
                            config[pro_key] = '"'+self.parser.get(section, key).strip('"') + fetch_host_shortname().lower()+'"'
                        else:
                            config[pro_key] = self.parser.get(section, key)
                    config.write()
                    self.logger.logger.info(f' {section} available in config file key {key}.')
                    print(f' {section} available in config file key {key}.')
                else:  
                    self.logger.logger.info(f' {section} section not available in config file key {key}.')
                    print(f' {section} section not available in config file key {key}.')
                    config[pro_key] = f'"{value}"'
                    config.write()

            print("Done...")
            return True
        except Exception as e:
            self.logger.logger.error(f'Error occured while updating the property file. Error {e}')
            return False

    def validate_generate(self, file_name=''):
        """
        Name: validate_generate
        Desc: Validate the generated property files
        Parameters:
            path (string ): Path to the generated file
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        file_list = [self.property_folder+'cp4ba_db_name_user.property', self.property_folder+'cp4ba_db_name_user.property', self.property_folder+'cp4ba_db_server.property', self.property_folder+'cp4ba_LDAP.property']
        self.logger.logger.info(f'Property files are {str(file_list)}')
        valid = True
        for file in file_list:
            file_path = Path(file)
            self.logger.logger.info(f'Property file path: {file_path}')
            if not file_path.is_file():
                valid = False
                return valid
        return valid

    def validate_createdsecrets(self, number_of_secrets):
        """
        Name: validate_createdsecrets
        Modified: Dhanesh
        Desc: Validate the generated secrets
        Parameters:
            number_of_secrets (int ): The number of secrets to validate
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        # Get the list of secrets with namespace and opaque type
        get_secrets = ['oc', 'get', 'secrets', '-n', self.project_name, '--field-selector',  'type=Opaque',  '-o', 'jsonpath={.items[*].metadata.name}']
        try:
            result = subprocess.run(get_secrets, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            secrets = result.stdout.decode().split()
            self.logger.logger.info(f'Number of secrets created: {len(secrets)}')
            print(f'Number of secrets created: {len(secrets)}')
            if len(secrets) < number_of_secrets:
                self.logger.logger.info(f"All required Secrets are not present- Actual {secrets}, Expected: {number_of_secrets}")
                print(f"All required Secrets are not present.")
                return False
            self.logger.logger.info(f"All required Secrets are present.")
            print(f"All required Secrets are present.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.logger.info(f"All required Secrets are not present. Error: {e.stderr.decode()}")
            print(f"All required Secrets are not present. Error: {e.stderr.decode()}")
            return False

    def run_subprocess(self, cmd):
        """
        Function name: run_subprocess
        Desc: Common function to run the commands
        Params:
            cmd: Command to run in bash
        Return:
            True/False depend on the command output
        """
        try:
            time.sleep(5)
            self.logger.logger.info(f'Command to run in subprocess is {cmd}')
            process = subprocess.run(['bash', cmd], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.logger.info(f"Command output is  {process.stdout.decode('utf-8')}")
            print(process.stdout.decode('utf-8'))
            if process.returncode == 0:
                return True
            else:
                self.logger.logger.info(f"Error: {process.stderr}")
                print(f"Error in processing the subprocess : {process.stderr}")
                raise subprocess.CalledProcessError(process.returncode, process.args)
        except subprocess.CalledProcessError as e:
            self.logger.logger.info(f"Error: Script returned an error: {e}")
            return False
        except Exception as e:
            self.logger.logger.info(f"Error: Script returned an error: {e}")
            return False

    def create_secret(self):
        """
        Name: create_secret
        Desc: Creating the secrets using the script
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        try:
            self.switch_namespace()
            # Start the shell script process
            script = self.script_folder + "cp4a-prerequisites.sh -m generate -n " + self.project_name
            self.logger.logger.info(f'Running the script {script}')
            process = pexpect.spawn("bash  " + script)
            process.sendline('')
            pattern = re.compile(r'.*' + re.escape('Create the databases and Kubernetes secrets manually based on your modified') + r'.*')
            process.expect(pattern, timeout=240)
            generate_op = process.before.decode('utf-8')
            self.logger.logger.info(f'Command Generate output : {generate_op}')

            #Copy the ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh to the folder in case of postgres
            if self.db == 'postgres':
                current_dir = os.getcwd()
                cp_from  = current_dir + '/certs/scripts/ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh '
                cp_to = self.prereq_folder + 'secret_template/cp4ba_db_ssl_secret/postgres/ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh'
                self.logger.logger.info(f'Coping the ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh file from  {cp_from} to {cp_to} ')
                os.system(f'cp -rf {cp_from} {cp_to}')    

            # Creating the secrets
            self.logger.logger.info(f'Creating the secrets using {self.prereq_folder + "create_secret.sh"} file')
            script = self.prereq_folder + "create_secret.sh"
            status, respo = self.valiate_cluster_component(script)
            if status:
                if 'failed' in respo.lower():
                    self.logger.logger.info(f"Sorry, Secret Creation Failed... ")
                    return False
            else:
                self.logger.logger.info(f"Sorry, Secret Creation Failed... ")
                return False
            
              
            secrets_status = self.validate_createdsecrets(self.number_of_secrets)
            if not secrets_status:
                print("Sorry, Secret Validation Failed... ")
                self.logger.logger.info(f"Sorry, Secret Validation Failed... ")
                return False
            return True
        except Exception as e:
            self.logger.logger.info(f"Creation of the secret is failed with error as {e} ")
            return False

    def validate_validation(self):
        """
        Name: validate_validation
        Desc: validating the o/p of the -m validate command 
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        # Get the list of secrets with namespace and opaque type
        self.switch_namespace()
        script = self.script_folder + "cp4a-prerequisites.sh"
        get_validation = [script,  '-m',  'validate', '-n', self.project_name]
        self.logger.logger.info(f'Going to do validation of the validate using command {str(get_validation)}')
        try:
            result = subprocess.run(get_validation, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.logger.debug(result)
            validation = result.stdout.decode()
            self.logger.logger.critical(validation)
            if "FAILED" in validation:
                self.logger.logger.critical('Validation failed with FAILED in the output. Please see the logs for more details.')
                return False
            return True
        except subprocess.CalledProcessError as e:
            self.logger.logger.error(f"Validation Failed. Error: {e.stderr.decode()}")
            print(f"Validation Failed. Error: {e.stderr.decode()}")
            return False

    def switch_namespace(self):
        """
        Name: switch_namespace
        Desc: Switch to the namespace
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        # Example function to switch or verify namespace using 'oc project' command
        try:
            command = ['oc', 'project', self.project_name]
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode == 0:
                self.logger.logger.info(f"Switched to namespace '{self.project_name}' successfully.")
            else:
                self.logger.logger.error(f"Failed to switch to namespace '{self.project_name}'.")
                self.logger.logger.error("Error:", result.stderr)
        
        except Exception as e:
            print(f"Error executing 'oc project' command: {e}")

    def ensure_double_quotes(self, data):
        """
        Name: ensure_double_quotes
        Desc: Ensuring the double quote comes with the values
        Parameters:
            Yaml data
        Returns:
            String: Yaml data
        Raises:
            ValueError: If the return value is False.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.ensure_double_quotes(value)
        elif isinstance(data, list):
            return [self.ensure_double_quotes(item) for item in data]
        elif isinstance(data, str):
            return DoubleQuotedScalarString(data)
        return data

    def validate_resources(self):
        """
        Name: validate_resource
        Desc: validating created secrets, ldap connection and db connections
        Parameters:
            dbval : Db values
            ldapval : Ldap value
            pjtval : Namespace
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        try:
            #Doing the validation
            valid_status = self.validate_validation()
            self.logger.logger.info(f'Validation status is {valid_status}')
            if not valid_status:
                self.logger.logger.info("Sorry, Validation Failed. Please see logs for more details. ")
                return True
            return True
        except Exception as e:
            print(f"Error executing resource validate: {e}")
            self.logger.logger.debug(f"Error executing resource validate: {e}")
            return True

    def componentwise_cr(self, loaded_yaml):
        """
        Name: componentwise_cr
        Desc: Updating the CR with the values from each component
        Parameters:
            None
        Returns:
            String: Yaml data
        Raises:
            ValueError: If the return value is False.
        """
        try:

            # Loading the cr file for updating the generated cr
            yaml = YAML()
            with open('/opt/ibm-cp-automation/descriptors/patterns/ibm_cp4a_cr_production_FC_content.yaml', 'r') as f:
                data = yaml.load(f)
                data = data['spec']['ecm_configuration']
                self.logger.logger.info(f"Following is the ecm configuration data from FC_content.yaml")
                self.logger.logger.info(f"{data}")

            #Getting the installed components and looping through the components.
            self.logger.logger.info(f"Getting the installed components and looping through the components.")
            components = loaded_yaml['spec']['content_optional_components']
            for key, value in components.items():
                if not value:
                    self.logger.logger.info(f"Deleting the components from the yaml {key}.")
                    if key in data.keys():
                        del data[key]
                        self.logger.logger.info(f"{key} Deleted from the yaml .")
            return data
        except Exception as e:
            print(f'Error while updating the CR file. Error is {e}')
            self.logger.logger.error(f"Error while updating the CR file. Error is {e}")
            return loaded_yaml
    
    def fisma_cr(self, loaded_yaml):
        """
        Name: fisma_cr
        Desc: Fisma cr updates
        Parameters:
            None
        Returns:
            String: Yaml data
        Raises:
            ValueError: If the return value is False.
        """
        fisma_setting = {'sc_audit_logging': {'enabled': False}}
        if '25.0' in self.branch and self.fisma.upper() == 'YES':
            fisma_setting = {'sc_audit_logging': {'enabled': True}}
        loaded_yaml['spec']['shared_configuration'].update(fisma_setting)
        return loaded_yaml

    def update_cr(self):
        """
        Name: update_cr
        Desc: Updating the CR with the values
        Parameters:
            None
        Returns:
            String: Yaml data
        Raises:
            ValueError: If the return value is False.
        """

        try:
            yaml = YAML()

            # Opening the cr file to update
            cr_file = self.generatedcr_folder + 'ibm_content_cr_final.yaml'
            with open(cr_file) as file:
                loaded_yaml = yaml.load(file)
            
            loaded_yaml['spec'].update({'ecm_configuration': {'graphql': {'graphql_production_setting': {'enable_graph_iql': True}}}})
            loaded_yaml['spec'].update(self.set_navconfiguration())
            loaded_yaml['spec']['shared_configuration'].update({'show_sensitive_log': True, 'no_log': True})
            loaded_yaml['spec']['shared_configuration']['sc_content_verification'] = True
            loaded_yaml['spec']['shared_configuration']['sc_content_initialization'] = True

            #LDAP  configurations depend on the ldap selected
            if loaded_yaml['spec']['ldap_configuration']['lc_selected_ldap_type'] == "IBM Security Directory Server":
                ic_ldap_admin_user_name = self.parser.get('CONTENT_INITIALIZATION_SDS', 'CONTENT_INITIALIZATION.LDAP_ADMIN_USER_NAME').replace('"', '')
                ic_ldap_admins_groups_name = self.parser.get('CONTENT_INITIALIZATION_SDS', 'CONTENT_INITIALIZATION.LDAP_ADMINS_GROUPS_NAME').replace('"', '')
                ldap_config = "LDAP_SDS"
            elif loaded_yaml['spec']['ldap_configuration']['lc_selected_ldap_type'] == "Microsoft Active Directory":
                ic_ldap_admin_user_name = self.parser.get('CONTENT_INITIALIZATION_MSAD', 'CONTENT_INITIALIZATION.LDAP_ADMIN_USER_NAME').replace('"', '')
                ic_ldap_admins_groups_name = self.parser.get('CONTENT_INITIALIZATION_MSAD', 'CONTENT_INITIALIZATION.LDAP_ADMINS_GROUPS_NAME').replace('"', '')
                ldap_config = "LDAP_MSAD"
            elif loaded_yaml['spec']['ldap_configuration']['lc_selected_ldap_type'] == "PingDirectory Server":
                ic_ldap_admin_user_name = self.parser.get('CONTENT_INITIALIZATION_PINGDIRECTORY', 'CONTENT_INITIALIZATION.LDAP_ADMIN_USER_NAME').replace('"', '')
                ic_ldap_admins_groups_name = self.parser.get('CONTENT_INITIALIZATION_PINGDIRECTORY', 'CONTENT_INITIALIZATION.LDAP_ADMINS_GROUPS_NAME').replace('"', '')
                ldap_config = "LDAP_PINGDIRECTORY"

            #Adding additonal ldap configurations if the multildap deployment is selected.
            if self.multildap=='True' and self.multildap_post_init == 'False':
                print("updating CR during initial stage")
                #if the selected ldap is MSAD , we need to add the configurations for TDS,else we need to add the configurations for MSAD
                if loaded_yaml['spec']['ldap_configuration']['lc_selected_ldap_type'] == "Microsoft Active Directory":
                    self.delete_secret()
                    self.re_create_secret_for_msad_selected()

                    # Set port and SSL values
                    if self.second_ldap_ssl_enabled == 'True':
                        lc_ldap_port = self.parser.get('LDAP_SDS', 'LDAP_PORT').replace('"', '')
                        self.create_ldap_ssl_secret_for_tds()
                        self.update_ldap_configuration_for_TDS(lc_ldap_port,loaded_yaml)
                    else:
                        lc_ldap_port = "389"
                        self.update_ldap_configuration_for_TDS(lc_ldap_port,loaded_yaml)

                elif loaded_yaml['spec']['ldap_configuration']['lc_selected_ldap_type'] == "IBM Security Directory Server":
                    self.delete_secret()
                    self.re_create_secret_for_tds_selected()

                    # Set port and SSL values
                    if self.second_ldap_ssl_enabled == 'True':
                        lc_ldap_port = self.parser.get('LDAP_MSAD', 'LDAP_PORT').replace('"', '')
                        self.create_ldap_ssl_secret_for_msad()
                        self.update_ldap_configuration_for_MSAD(lc_ldap_port,loaded_yaml)
                    else:
                        lc_ldap_port = "389"
                        self.update_ldap_configuration_for_MSAD(lc_ldap_port,loaded_yaml)

                #Nusaiba need to update this part.
                elif loaded_yaml['spec']['ldap_configuration']['lc_selected_ldap_type'] == "PingDirectory Server":
                    self.delete_secret()
                    self.re_create_secret_for_tds_selected()

                    # Set port and SSL values
                    if self.second_ldap_ssl_enabled == 'True':
                        lc_ldap_port = self.parser.get('LDAP_MSAD', 'LDAP_PORT').replace('"', '')
                        self.create_ldap_ssl_secret_for_msad()
                        self.update_ldap_configuration_for_MSAD(lc_ldap_port,loaded_yaml)
                    else:
                        lc_ldap_port = "389"
                        self.update_ldap_configuration_for_MSAD(lc_ldap_port,loaded_yaml)
                
            #Ldap data into cr file 
            self.logger.logger.info('Updating the initialize_configuration')
            loaded_yaml['spec']['initialize_configuration']['ic_ldap_creation']['ic_ldap_admin_user_name'] = [ic_ldap_admin_user_name]
            loaded_yaml['spec']['initialize_configuration']['ic_ldap_creation']['ic_ldap_admins_groups_name'] = [ic_ldap_admins_groups_name]
            loaded_yaml['spec']['initialize_configuration']['ic_obj_store_creation']['object_stores'][0]['oc_cpe_obj_store_admin_user_groups'] = [ic_ldap_admins_groups_name]

            #Setting up tables space
            self.logger.logger.info(f'Selecting the tables space: ')
            self.logger.logger.info(f"Database is {loaded_yaml['spec']['datasource_configuration']['dc_icn_datasource']['dc_database_type']}")
            if loaded_yaml['spec']['datasource_configuration']['dc_icn_datasource']['dc_database_type'] == 'db2':
                oc_cpe_obj_store_workflow_data_tbl_space = 'OSDATA_TS'
            elif loaded_yaml['spec']['datasource_configuration']['dc_icn_datasource']['dc_database_type'] == 'postgresql':
                oc_cpe_obj_store_workflow_data_tbl_space = "pg_default"
            elif loaded_yaml['spec']['datasource_configuration']['dc_icn_datasource']['dc_database_type'] == 'oracle':

                #Adding table space name
                host_shortname = fetch_host_shortname()
                oc_cpe_obj_store_workflow_data_tbl_space = 'OS1_' + host_shortname.upper() + 'DATATS'
            elif loaded_yaml['spec']['datasource_configuration']['dc_icn_datasource']['dc_database_type'] == 'sqlserver':
                oc_cpe_obj_store_workflow_data_tbl_space = "PRIMARY"
            self.logger.logger.info(f"Database tablespace is {oc_cpe_obj_store_workflow_data_tbl_space}")


            if self.tablespaceoption.upper() != 'NO':
                tablevalues = self.updatecr_with_tablespace()
                loaded_yaml['spec']['initialize_configuration']['ic_obj_store_creation']['object_stores'][0].update(tablevalues)


            #Adding component wise cofiguration from the yaml
            # component_data = self.componentwise_cr(loaded_yaml)
            # loaded_yaml['spec']['ecm_configuration'].update(component_data)
            # loaded_yaml['spec']['ecm_configuration']['graphql']['graphql_production_setting'].update({'add_repo_workflow_enable': True})

            # Cr file modificaion to include Icc team sanity check.
            # Setting icc_setting for the future modification.
            icc_setting = True
            if icc_setting == True:

                #Creating the secret icc-masterkey-txt from MasterKey.txt
                self.create_secret_formasterkey('icc-masterkey-txt', 'MasterKey.txt')
                # Ensure 'ecm_configuration' exists
                loaded_yaml['spec'].setdefault('ecm_configuration', {})

                # Update graphql settings
                loaded_yaml['spec']['ecm_configuration']['graphql'] = {'graphql_production_setting': {'enable_graph_iql': True}}

                # Update cpe settings
                loaded_yaml['spec']['ecm_configuration']['cpe'] = {'cpe_production_setting': {'jvm_customize_options': '-Dcom.filenet.engine.TolerateMissingReflectiveProperty=true'}}

                # Update css settings
                loaded_yaml['spec']['ecm_configuration']['css'] = {'css_production_setting': {'icc': {'icc_enabled': True, 'icc_secret_name':'ibm-icc-secret', 'p8domain_name':'P8DOMAIN', 'secret_masterkey_name':'icc-masterkey-txt'}}}

            #Object store data into cr file
            self.logger.logger.info('Updating the tables space')
            loaded_yaml['spec']['initialize_configuration']['ic_obj_store_creation']['object_stores'][0].update({'oc_cpe_obj_store_enable_content_event_emitter': True, 
                    'oc_cpe_obj_store_enable_workflow': True, 
                    'oc_cpe_obj_store_workflow_region_name': "design_region_name",
                    'oc_cpe_obj_store_workflow_region_number': 1,
                    'oc_cpe_obj_store_workflow_data_tbl_space': oc_cpe_obj_store_workflow_data_tbl_space, 
                    'oc_cpe_obj_store_workflow_index_tbl_space': "",
                    'oc_cpe_obj_store_workflow_blob_tbl_space': "",
                    'oc_cpe_obj_store_workflow_admin_group': ic_ldap_admins_groups_name,
                    'oc_cpe_obj_store_workflow_config_group': ic_ldap_admins_groups_name,
                    'oc_cpe_obj_store_workflow_date_time_mask': "mm/dd/yy hh:tt am",
                    'oc_cpe_obj_store_workflow_locale': "en",
                    'oc_cpe_obj_store_workflow_pe_conn_point_name': "pe_conn_os1"})
            
            #initialization configuration
            self.logger.logger.info('Updating the initialize_configuration')
            loaded_yaml['spec']['initialize_configuration']['ic_icn_init_info']['icn_repos'][0].update({'add_repo_workflow_enable': True})
            loaded_yaml['spec']['initialize_configuration']['ic_icn_init_info']['icn_desktop'][0].update({'add_desktop_is_default': True, 'add_desktop_repo_workflow_enable': True})
            loaded_yaml['spec']['verify_configuration']['vc_cpe_verification']['vc_cpe_workflow'][0].update({'workflow_cpe_enabled': True})

            #Adding fisma audit logging
            loaded_yaml = self.fisma_cr(loaded_yaml)

            #Ensuring the values are surrounded with double quotes
            self.ensure_double_quotes(loaded_yaml)

            #Writing all data into cr file
            with open(cr_file, 'wb') as f:
                yaml.dump(loaded_yaml, f)
                self.logger.logger.info(f'CR file {cr_file} updated successfully.')
                return True
        except Exception as e:
            self.logger.logger.error(f'Error while updating the CR file. Error is {e}')
            return False
    
    def updatecr_with_tablespace(self):
        """
        Name: updatecr_with_tablespace
        Desc: Updates the CR with the table space data.
        Parameters:
            self
        Returns:
             dict
        Raises:
            ValueError: If any error occurs during the update.
        """
        try:
            tablespace_dict = {}
            if tablespae_branch_check(self.clone_repo):
                config = CustomConfigObj(self.property_folder + "cp4ba_db_name_user.property")

                # Looping through the db username property file to findout the db anem and tablespace names
                for key, value in config.items():
                    self.logger.logger.info(f'updatecr_with_tablespace = {key} {value} ')
                    if 'OS1_DB_NAME' == key.upper():
                        dbname = value.lower()
                    if self.db == 'oracle':
                        if 'OS1_DB_USER_NAME' == key.upper():
                            dbname = value.lower()

                # Looping through the db username property file to findout the db names and tablespace names
                for key, value in config.items():

                    #making the newkey by removing the db alias name
                    newkey = key.split('.')[1]
                    self.logger.logger.info(f'newkey = {newkey} ')
                    if newkey in 'OS1_DB_INDEX_STORAGE_LOCATION':
                        indexpace_names = dbname+'_'+value.lower()
                        tablespace_dict.update({'oc_cpe_obj_store_index_storage_location': indexpace_names})
                    if newkey in 'OS1_DB_TABLE_STORAGE_LOCATION':
                        tablespace_names = dbname+'_'+value.lower()
                        tablespace_dict.update({'oc_cpe_obj_store_table_storage_location': tablespace_names})
                    if newkey in 'OS1_DB_LOB_STORAGE_LOCATION':
                        lobspace_names = dbname+'_'+value.lower()
                        tablespace_dict.update({'oc_cpe_obj_store_lob_storage_location': lobspace_names})
                return tablespace_dict     
        except Exception as e:
            self.logger.logger.error(f'Error while updating the CR file for the tablespace. Error is {e}')
            return tablespace_dict

    def update_ldap_configuration_for_MSAD(self, lc_ldap_port,loaded_yaml):
        """
        Name: update_ldap_configuration_for_MSAD
        Author: Nusaiba K K 
        Desc: Updates the CR with the additional MSAD LDAP configurations.
        Parameters:
            loaded yaml from update cr,ldap port whether ssl port or non ssl port
        Returns:
             YAML data
        Raises:
            ValueError: If any error occurs during the update.
        """
        try:
            print("Started updating the additional LDAP configuration...")
            print("Port number is:", lc_ldap_port)

            # Convert SSL enabled value to Boolean
            self.second_ldap_ssl_enabled = self.second_ldap_ssl_enabled == 'True'
            print("SSL enabled:", self.second_ldap_ssl_enabled)

            # Debug: Print the structure before modification
            print("Loaded YAML before modification:")
            print(loaded_yaml)

            # Ensure the key exists or add it
            if 'spec' not in loaded_yaml:
                loaded_yaml['spec'] = {}
            if 'ldap_configuration_2' not in loaded_yaml['spec']:
                print("Adding ldap_configuration_2 section...")
                loaded_yaml['spec']['ldap_configuration_2'] = {}

            # Update LDAP configuration for MSAD
            loaded_yaml['spec']['ldap_configuration_2'] = {
                'lc_ldap_id': 2,
                'ad': {
                    'lc_ad_gc_host': '',
                    'lc_ad_gc_port': '',
                    'lc_group_filter': '(&(cn=%v)(objectcategory=group))',
                    'lc_user_filter': '(&(sAMAccountName=%v)(objectcategory=user))'
                },
                'lc_ldap_user_display_name_attr': 'sAMAccountName',
                'lc_ldap_group_base_dn': 'DC=testa1OU,dc=testa1,DC=fyre,DC=ibm,DC=com',
                'lc_ldap_base_dn': 'DC=testa1,DC=fyre,DC=ibm,DC=COM',
                'lc_bind_secret': 'ldap-bind-secret',
                'lc_ldap_user_name_attribute': 'user:sAMAccountName',
                'lc_ldap_group_member_id_map': 'memberOf:member',
                'lc_ldap_port': lc_ldap_port,
                'lc_ldap_server': 'testa1.fyre.ibm.com',
                'lc_ldap_group_membership_search_filter': '(&(cn=%v)(objectcategory=group))',
                'lc_selected_ldap_type': 'Microsoft Active Directory',
                'lc_ldap_ssl_secret_name': "",
                'lc_ldap_group_name_attribute': '*:cn',
                'lc_ldap_group_display_name_attr': 'cn',
                'lc_ldap_ssl_enabled': self.second_ldap_ssl_enabled
            }

            # Debug: Print the structure after modification
            print("Loaded YAML after modification:")
            print(loaded_yaml)
            return loaded_yaml  
        except Exception as e:
            self.logger.logger.error(f'Error while updating the CR file. Error is {e}')
            raise Exception(f'Error while updating the CR file. Error is {e}')

    def update_ldap_configuration_for_TDS(self, lc_ldap_port,loaded_yaml):
        """
        Name: update_ldap_configuration_for_TDS
        Author: Nusaiba K K 
        Desc: Updates the CR with the additional TDS LDAP configurations.
        Parameters:
            loaded yaml from update cr,ldap port whether ssl port or non ssl port
        Returns:
             YAML data
        Raises:
            ValueError: If any error occurs during the update.
        """
        try:
            print("Started updating the additional LDAP configuration...")

            # Convert SSL enabled value to Boolean
            self.second_ldap_ssl_enabled = self.second_ldap_ssl_enabled == 'True'
            print("SSL enabled:", self.second_ldap_ssl_enabled)
            
            # Debug: Print the structure before modification
            print("Loaded YAML before modification:")
            print(loaded_yaml)

            # Ensure the key exists or add it
            if 'spec' not in loaded_yaml:
                loaded_yaml['spec'] = {}
            if 'ldap_configuration_2' not in loaded_yaml['spec']:
                print("Adding ldap_configuration_2 section...")
                loaded_yaml['spec']['ldap_configuration_2'] = {}

            # Update LDAP configuration for TDS
            loaded_yaml['spec']['ldap_configuration_2'] = {
                'lc_ldap_id': 2,
                'lc_selected_ldap_type': "IBM Security Directory Server",
                'lc_ldap_server': "seepage1.fyre.ibm.com",
                'lc_ldap_port': lc_ldap_port,
                'lc_bind_secret': "ldap-bind-secret",
                'lc_ldap_base_dn': "DC=EXAMPLE,DC=COM",
                'lc_ldap_ssl_enabled': self.second_ldap_ssl_enabled,
                'lc_ldap_ssl_secret_name': "ibm-cp4ba-ldap2-ssl-secret",
                'lc_ldap_user_name_attribute': "*:uid",
                'lc_ldap_user_display_name_attr': "uid",
                'lc_ldap_group_base_dn': "DC=EXAMPLE,DC=COM",
                'lc_ldap_group_name_attribute': "*:cn",
                'lc_ldap_group_display_name_attr': "cn",
                'lc_ldap_group_membership_search_filter': "(|(&(objectclass=groupofnames)(member={0}))(&(objectclass=groupofuniquenames)(uniquemember={0})))",
                'lc_ldap_group_member_id_map': "groupofnames:member",
                'tds': {
                    'lc_user_filter': "(&(uid=%v)(objectclass=ePerson))",
                    'lc_group_filter': "(&(cn=%v)(objectclass=groupofnames))"
                }
            }
            
            # Debug: Print the structure after modification
            print("Loaded YAML after modification:")
            print(loaded_yaml)
            return loaded_yaml
        except Exception as e:
            self.logger.logger.error(f'Error while updating the CR file. Error is {e}')
            raise Exception(f'Error while updating the CR file. Error is {e}')

    def delete_secret(self):
        """
        Name: delete_secret
        Author: Nusaiba K K 
        Desc: delete ldap-bind-secret
        Parameters:
            None
        Returns:
            None
        """
        try:
            # Hardcode the secret name in the kubectl command
            secret_name = "ldap-bind-secret"
            result = subprocess.run(
                ["kubectl", "delete", "secret", secret_name],  # Deletes only ldap-bind-secret
                check=True,
                text=True,
                capture_output=True
            )
            print(f"Secret '{secret_name}' deleted successfully.")
            print("Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete secret '{secret_name}'.")
            print("Error:", e.stderr)
    
    def create_secret_formasterkey(self,secret_name, key_filename):
        """
        Name: create_secret_formasterkey
        Desc: Creation of the secret using filename
        Parameters:
            None
        Returns:
            None
        """
        try:
            command = ["oc", "create", "secret", "generic", secret_name,
                        f"--from-file={key_filename}=/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/certs/icc/{key_filename}"
                ]
            # Execute the command
            result = subprocess.run(command, check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Error message
            print(f"Failed to create secret '{secret_name}'.")
            print("Error:", e.stderr)

    def re_create_secret_for_msad_selected(self):
        """
        Name: re_create_secret_for_msad_selected
        Author: Nusaiba K K 
        Desc: recreate ldap-bind-secret in case selected LDAP is MSAD
        Parameters:
            None
        Returns:
            None
        """
        try:
            secret_name = "ldap-bind-secret"
            
            # Retrieve the LDAP values from the config file
            ldap_username = self.parser.get('MULTILDAP', 'ldap_Username_msad')
            ldap_password = self.parser.get('MULTILDAP', 'ldap_Password_msad')
            ldap2_username = self.parser.get('MULTILDAP', 'ldap_Username_tds')
            ldap2_password = self.parser.get('MULTILDAP', 'ldap_Password_tds')
            
            # Construct the kubectl command
            command = [
                "kubectl", "create", "secret", "generic", secret_name,
                f"--from-literal=ldapUsername={ldap_username}",
                f"--from-literal=ldapPassword={ldap_password}",
                f"--from-literal=ldap2Username={ldap2_username}",
                f"--from-literal=ldap2Password={ldap2_password}"
            ]
            
            # Execute the command
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            
            # Success message
            print(f"Secret '{secret_name}' created successfully.")
            print("Output:", result.stdout)
            
        except subprocess.CalledProcessError as e:
            # Error message
            print(f"Failed to create secret '{secret_name}'.")
            print("Error:", e.stderr)

    def re_create_secret_for_tds_selected(self):
        """
        Name: re_create_secret_for_tds_selected
        Author: Nusaiba K K 
        Desc: recreate ldap-bind-secret in case selected ldap is TDS
        Parameters:
            None
        Returns:
            None
        """
        try:
            secret_name = "ldap-bind-secret"
            
            # Retrieve the LDAP values from the config file
            ldap_username = self.parser.get('MULTILDAP', 'ldap_Username_tds')
            ldap_password = self.parser.get('MULTILDAP', 'ldap_Password_tds')
            ldap2_username = self.parser.get('MULTILDAP', 'ldap_Username_msad')
            ldap2_password = self.parser.get('MULTILDAP', 'ldap_Password_msad')
            
            # Construct the kubectl command
            command = [
                "kubectl", "create", "secret", "generic", secret_name,
                f"--from-literal=ldapUsername={ldap_username}",
                f"--from-literal=ldapPassword={ldap_password}",
                f"--from-literal=ldap2Username={ldap2_username}",
                f"--from-literal=ldap2Password={ldap2_password}"
            ]
            
            # Execute the command
            result = subprocess.run(command, check=True, text=True, capture_output=True)
            
            # Success message
            print(f"Secret '{secret_name}' created successfully.")
            print("Output:", result.stdout)
            
        except subprocess.CalledProcessError as e:
            # Error message
            print(f"Failed to create secret '{secret_name}'.")
            print("Error:", e.stderr)

    def create_ldap_ssl_secret_for_msad(self):
        """
        Name: create_ldap_ssl_secret_for_msad
        Author: Nusaiba K K 
        Desc: create ldap-ssl-secret in case selected ldap is MSAD
        Parameters:
            None
        Returns:
            None
        """
        try:
            secret_name = "ibm-cp4ba-ldap2-ssl-secret"
            namespace = self.project_name
            print(self.project_name)
            cert_path = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/certs/msad/ldap-cert.crt"

            # Construct the kubectl command
            command = [
                "kubectl", "create", "secret", "generic", secret_name,
                f"--from-file=tls.crt={cert_path}",
                "-n", namespace
            ]

            # Execute the command
            result = subprocess.run(command, check=True, text=True, capture_output=True)

            # Success message
            print(f"Secret '{secret_name}' created successfully.")
            print("Output:", result.stdout)

        except subprocess.CalledProcessError as e:
            # Error message
            print(f"Failed to create secret '{secret_name}'.")
            print("Error:", e.stderr)

    def create_ldap_ssl_secret_for_tds(self):
        """
        Name: create_ldap_ssl_secret_for_tds
        Author: Nusaiba K K 
        Desc: create ldap-ssl-secret in case selected ldap is TDS
        Parameters:
            None
        Returns:
            None
        """
        try:
            secret_name = "ibm-cp4ba-ldap2-ssl-secret"
            namespace = self.project_name
            print(self.project_name)
            cert_path = "/opt/Cp4ba-Automation/cp4ba_proddeploy_automation/certs/sds/ldap-cert.crt"

            # Construct the kubectl command
            command = [
                "kubectl", "create", "secret", "generic", secret_name,
                f"--from-file=tls.crt={cert_path}",
                "-n", namespace
            ]

            # Execute the command
            result = subprocess.run(command, check=True, text=True, capture_output=True)

            # Success message
            print(f"Secret '{secret_name}' created successfully.")
            print("Output:", result.stdout)

        except subprocess.CalledProcessError as e:
            # Error message
            print(f"Failed to create secret '{secret_name}'.")
            print("Error:", e.stderr)

    def apply_yaml(self, file):
        """
        Name: apply_yaml
        Desc: Apply the yaml file 
        Parameters:
            file (string ): Path to the generated file
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        # Make the command to apply
        apply_file = ['oc', 'apply', '-f', file, '-n', self.project_name]
        try:
            result = subprocess.run(apply_file, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())

            # Checking the response from the oc apply
            if result.returncode != 0:
                self.logger.logger.error(f'Failed to apply the cr: {file}')
                print(f'Failed to apply the cr: {file}')
                return False
            self.logger.logger.info(f"CR file {file} applied")
            print(f"CR file {file} applied")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.logger.error(f"Failed to apply the cr: {file}. Error: {e.stderr.decode()}")
            print(f"Failed to apply the cr: {file}. Error: {e.stderr.decode()}")
            return False

    def check_saplibs(self):
        """
        Name: check_saplibs
        Desc: Checking the saplibs are loading fine or not
        Parameters:
            None
        Returns:
            Boolean : True/False
        """
        try:
            #Checking the saplibs is loading fine
            saplibs = self.parser.get('PREREQUISITES', 'SAPLIBS')
            url_status = url_check(saplibs)

            if url_status:
                self.logger.logger.info(f'Supplied URL is valid. {saplibs}')
                return True
            else:
                self.logger.logger.error(f'Supplied URL is not valid. {saplibs}')
                return False
        except Exception as e:
            self.logger.logger.error(f'Supplied URL is not valid. {saplibs}')
            return False

    def createcr_apply(self):
        """
        Name: createcr_apply
        Desc: Create the CR file and apply . Validation of Cr is also included.
        Parameters:
            None
        Returns:
            Boolean : True/False
        Raises:
            ValueError: If the return value is False.
        """

        try:
            self.logger.logger.info(f'Starting the Deployment of project {self.project_name} using db {self.db} ldap {self.ldap} on branch {self.branch} with tag {self.stage_prod}.')

            # Start the shell script process
            process = pexpect.spawn("bash  " + self.script_folder  + "cp4a-deployment.sh " + self.stage_prod +" -n " + self.project_name)
            self.logger.logger.info(f'Running the script {self.script_folder}  cp4a-deployment.sh {self.stage_prod} -n   {self.project_name}')
            #To select the Cloud Pak for Business Automation capability to install:  
            time.sleep(5) #Fix for 24.0.0-IF004

            process.sendline()
            time.sleep(2)

            #Do you accept the IBM Cloud Pak for Business Automation license (Yes/No, default: No): 
            process.sendline('Yes')
            time.sleep(2)

            #Did you deploy Content CR (CRD: contents.icp4a.ibm.com) in current cluster? (Yes/No, default: No): 
            process.sendline('No')
            time.sleep(2)
            self.logger.logger.info('Did you deploy Content CR (CRD: contents.icp4a.ibm.com) in current cluster? (Yes/No, default: No): No')

            # What type of deployment is being performed?
            # 1) Starter
            # 2) Production
            # Enter a valid option [1 to 2]: 
            process.sendline('2')
            time.sleep(2)

            # [INFO] Above CP4BA capabilities is already selected in the cp4a-prerequisites.sh script
            process.sendline()
            time.sleep(2)
            # Select the cloud platform to deploy: 
            # 1) RedHat OpenShift Kubernetes Service (ROKS) - Public Cloud
            # 2) Openshift Container Platform (OCP) - Private Cloud
            # 3) Other ( Certified Kubernetes Cloud Platform / CNCF)
            # Enter a valid option [1 to 3]: 
            process.sendline('2')
            time.sleep(2)
            self.logger.logger.info(f'Select the cloud platform to deploy: 2')

            # Is your OCP deployed on AWS or Azure? (Yes/No, default: No):
            self.logger.logger.info('Checking the branch is not in 24.0.0,24.0.0-IF001,24.0.0-IF002,24.0.0-IF003,24.0.0-IF004,24.0.1,24.0.1-IF001 and if yes then asking question regarding the aws or azure')
            branch_status = branch_check(self.branch)
            if branch_status:
                self.logger.logger.info('Sending No for AWS or AZURE quesrion')
                process.sendline('No')
                time.sleep(2)

            # Do you want to use the default IAM admin user: [cpadmin] (Yes/No, default: Yes): 
            process.sendline('Yes')
            time.sleep(2)
            # Provide a URL to zip file that contains JDBC and/or ICCSAP drivers.
            # (optional - if not provided, the Operator will configure using the default shipped JDBC driver): 
            # http://9.30.206.203:8888/saplibs.zip
            # jdbc_url = input("Please enter the JDBC driver URL: ") 
            saplibs = self.parser.get('PREREQUISITES', 'SAPLIBS')
            process.sendline(saplibs)
            time.sleep(2)
            self.logger.logger.info(saplibs)

            # Verify that the information above is correct.
            # To proceed with the deployment, enter "Yes".
            # To make changes, enter "No" (default: No): 
            process.sendline('Yes')
            self.logger.logger.info(f'To proceed with the deployment, enter "Yes".: Yes')
            time.sleep(5)

            #For 24.0.0-IF004
            if self.branch != '24.0.0-IF004' and self.branch != '24.0.1-IF001':
                process.sendline(self.project_name)
                self.logger.logger.info(f'Asking for the namespace : {self.project_name}')

            #Comparing the o/p with expect
            cr_pattern = re.compile(r'.*' + re.escape("To monitor the deployment status, follow the Operator logs") + r'.*')
            process.expect(cr_pattern, timeout=100)
            output = process.before.decode('utf-8')
            self.logger.logger.info(f"Creating Custom Resource file {output}")
            process.expect(['#', pexpect.EOF], timeout=10) 
            output = process.before.decode('utf-8')
            self.logger.logger.info(output)
            self.logger.logger.info('Call self.update_cr()')

            #Update the CR with the values.
            print("The value of multildap is :",self.multildap)
            print("The value of multildap_post_init is : ",self.multildap_post_init)
            self.logger.logger.info(self.second_ldap_ssl_enabled)
            cr_status = self.update_cr()
        
            if not cr_status:
                self.logger.logger.info('Deployment failed. Plese see the logs for more details...')
                print("Deployment Failed...")
                return False

            # Apply the CR
            self.switch_namespace()
            apply_yaml_status = self.apply_yaml(self.generatedcr_folder + 'ibm_content_cr_final.yaml')
            if not apply_yaml_status:
                self.logger.logger.info(f'Applying Generate CR failed with error')
                return False

            #Validate deployment
            if self.validate_deployment():
                print("Deployment Success...")
                self.logger.logger.info(f'Deployment Success...')
                return True
            else:
                print("Deployment Failed...")
                self.logger.logger.info(f'Deployment Failed...')
                return False
        except Exception as e:
            self.logger.logger.error(f'Deployment Failed with error... {e}')
            return False
        except:
            self.logger.logger.error(f'Deployment Failed with error. Please see the logs for more details.')
            return False

    def fetch_dbuser(self):
        """
        Function name: fetch_dbuser
        Desc: Common function to fetch the dbauser option number
        Params:
            logger( object): For the logging purpose
        Return:
            True/False depend on the command output
        """
        try:
            self.logger.logger.info(f'Fetching the dbauser option number using the command oc get user')
            result = subprocess.run(['oc', 'get', 'user'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Parse the output
            number = 0
            users = result.stdout.decode('utf-8').splitlines()

            #Checking the dbauser number
            for user in users:
                self.logger.logger.debug(f'User is {user}')
                username = user.split()[0]
                number = number + 1
                if username.lower() ==  self.parser.get('CLUSTER_SETUP', 'username').replace('"', '') :
                    self.logger.logger.info(f'Option nunber is {str(number)}')
                    return str(number)

            self.logger.logger.info(f"dbauser not available")
            return False
        except Exception as e:
            self.logger.logger.info(f"Dbauser not available {e}")
            print(f"Dbauser not available {e}")
            return False

    def operator_version_check(self):
        """
            Name: operator_version_check
            Desc: validating the operator version against the json file
            Parameters:
                None
            Returns:
                Boolean: True/False
        """

        try:
            version = '24.0.0'
            with open('./config/version.json') as f :
                cluster_data = json.load(f)
                self.logger.logger.info(f'Fetching the operator details.')
                result = subprocess.run(['oc', 'get', 'csv'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Parse the output
                csvs = result.stdout.decode('utf-8').splitlines()
                dict_data = cluster_data[version]

                #Verifying the version of operators
                for csv in csvs[1:]:
                    csv = csv.split()
                    operator = csv[0].split('.', 1)[0]
                    current_version = csv[0].split('.', 1)[1]
                    self.logger.logger.info(f'Operator is {operator} and Current version ={current_version} and {version} needed ={dict_data[operator]}')
                    if dict_data[operator] != current_version:
                        self.logger.logger.info(f'Version difference in the operator {operator}')
                        return False
                return True
        except Exception as e:
            self.logger.logger.info(f"Issue with version check. Error is {e}")
            return False

    def validate_operator_installation(self):
        """
        Name: validate_operator_installation
        Desc: Validate the statuses of operators installed
        Params:
            namespace: String value to check the namespace
            logger: Object for the logging purpose
        Returns:
            Boolean: True/False
        Raises:
            CalledProcessError: If the return value is False.
        """

        # Get the list of operators
        get_operators_command = ['oc', 'get', 'csv', '-n', self.project_name, '-o', 'jsonpath={.items[*].status.phase}']
        try:
            result = subprocess.run(get_operators_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            statuses = result.stdout.decode().split()
            self.logger.logger.info(statuses)
            print(statuses)

            #Checking the operators numbers
            if len(statuses) < 1:
                self.logger.logger.error(f"All the Operator installation failed. Status: {status}")
                print(f"All the Operator installation failed. Status: {status}")
                return False

            for status in statuses:
                if status not in ['Succeeded', 'Running']:
                    self.logger.logger.error(f"Operator installation failed. Status: {status}")
                    print(f"Operator installation failed. Status: {status}")
                    return False
            self.logger.logger.info("All operators installed successfully.")
            print("All operators installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.logger.error(f"Failed to get operator statuses. Error: {e.stderr.decode()}")
            print(f"Failed to get operator statuses. Error: {e.stderr.decode()}")
            return False

    def run_cp4a_clusteradmin_setup(self):
        """
        Name: run_cp4a_clusteradmin_setup
        Desc: function to setup the operators
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """
        
        try:
            # Read configuration values
            self.logger.logger.info('Getting the values from data config for the cluster admin script')
            print('Getting the values from data config for the cluster admin script')
            deployment_mode = self.parser.get('cluster_admin_setup', 'deployment_mode')
            cloud_platform = self.parser.get('cluster_admin_setup', 'cloud_platform')
            deployment_type = self.parser.get('cluster_admin_setup', 'deployment_type')
            private_catalog = self.parser.get('cluster_admin_setup', 'private_catalog')
            namespace = self.project_name
            entitlement_key_exists = self.parser.get('cluster_admin_setup', 'entitlement_key_exists')
            self.logger.logger.info(f'Got following values for the cluster admin script deployment_mode = {deployment_mode}, cloud_platform = {cloud_platform}, deployment_type ={deployment_type}, private_catalog = {private_catalog}, namespace = {namespace},  entitlement_key_exists ={entitlement_key_exists} ')
            
            #Dynamically fetching the dbauser number from the ocp
            dbauser_number = self.fetch_dbuser()
            if not dbauser_number:
                self.logger.logger.error('Error in fetching the dbauser number')
                return False   

            self.logger.logger.info(f'dbauser option number : {dbauser_number}')

            if entitlement_key_exists.lower() == 'yes':
                entitlement_key = self.parser.get('cluster_admin_setup', 'entitlement_key')
                if len(entitlement_key) < 190:
                    self.logger.logger.critical(f'Entitlement key is not valid. it is {entitlement_key}')
                    return False   
            else:
                entitlement_key = None
                self.logger.logger.critical(f' Entitlement key is not provided. it is {entitlement_key}')
                return False   
            self.logger.logger.info(f' Entitlement key is valid.')

            # The path to the script
            script_path = self.script_folder + 'cp4a-clusteradmin-setup.sh  ' + self.stage_prod
            self.logger.logger.info(f'Running the script {script_path}')

            # Start the script using pexpect
            child = pexpect.spawnu(f'{script_path}', timeout=None, logfile=None)
            time.sleep(5)

            # Do you wish setup your cluster for a online based CP4BA deployment or for a airgap/offline based CP4BA deployment : 
            # 1) Online
            # 2) Offline/Airgap
            child.sendline(deployment_mode) 
            self.logger.logger.info(f'Deployment mode is : {deployment_mode}')
   
            # Select the cloud platform to deploy: 
            # 1) RedHat OpenShift Kubernetes Service (ROKS) - Public Cloud
            # 2) Openshift Container Platform (OCP) - Private Cloud
            # 3) Other ( Certified Kubernetes Cloud Platform / CNCF)
            child.sendline(cloud_platform)
  
            # What type of deployment is being performed?
            # ATTENTION: The BAI standalone only supports "Production" deployment type.
            # 1) Starter
            # 2) Production
            # Enter a valid option [1 to 2]: 
            child.sendline(deployment_type)
            self.logger.logger.info(f'Deployment type is {deployment_type}.')
  
            # [NOTES] If you are planning to enable FIPS for CP4BA deployment, this script can perform a check on the OCP cluster to ensure the compute nodes have FIPS enabled.
            # Do you want to proceed with this check? (Yes/No, default: No): 
            child.sendline(self.fips)
            time.sleep(5)

            # [NOTES] You can install the CP4BA deployment as either a private catalog (namespace scope) or the global catalog namespace (GCN). The private option uses the same target namespace of the CP4BA deployment, the GCN uses the openshift-marketplace namespace.
            # Do you want to deploy CP4BA using private catalog (recommended)? (Yes/No, default: Yes): 
            child.sendline('yes')

            if (self.separation_duty_on.lower() == 'yes'):
                # [NOTES] CP4BA deployment supports separation of operators and operands, the script can deploy CP4BA operators and it's capabilities in different projects.
                # Do you want to deploy CP4BA as separation of operators and operands? (Yes/No, default: No):
                child.sendline('Yes')
                self.logger.logger.info(f'Do you want to deploy CP4BA as separation of operators and operands?  Yes')
            else:
                # [NOTES] CP4BA deployment supports separation of operators and operands, the script can deploy CP4BA operators and it's capabilities in different projects.
                # Do you want to deploy CP4BA as separation of operators and operands? (Yes/No, default: No):
                child.sendline('No')

            # Where do you want to deploy Cloud Pak for Business Automation?
            # Enter the name for a new project or an existing project (namespace): 
            child.sendline(namespace)

            self.logger.logger.info(f'Namespace is {namespace}.')

            # Where (namespace) do you want to deploy CP4BA operands (i.e., runtime pods)?
            # Enter the name for a new project or an existing project (namespace):
            if (self.separation_duty_on.lower() == 'yes'):
                #Creating new namespace in case of separation of duties
                namespace = str(namespace)+self.operand_namespace_suffix
                self.project_name = namespace
                self.logger.logger.info(f'Separation of duties selected so new Namespace is {namespace}.')
                time.sleep(5)
                child.sendline(namespace)
                time.sleep(5)

            # Here are the existing users on this cluster: 
            # 1) Cluster Admin
            # 2) Testa1admin
            # 3) admin
            # 4) dbauser
            # 5) group0001usr0001
            # Enter an existing username in your cluster, valid option [1 to 5], non-admin is suggested:
            child.sendline(dbauser_number)
            self.logger.logger.info(f'Enter an existing username in your cluster, valid option [1 to 5], non-admin is suggested: {dbauser_number}')

            #Do you have a Cloud Pak for Business Automation Entitlement Registry key (Yes/No, default: No): 
            child.sendline('yes')  # Assuming the prompt asks if the key exists

            #Enter your Entitlement Registry key: 
            child.sendline(entitlement_key)
            self.logger.logger.info(f'Entitlement key used: {entitlement_key}')
            #Logging the output
            child.expect(pexpect.EOF)
            print(child.before)
            self.logger.logger.info(f"cluster admin setup output {child.before}")

            #Check that operator status is ssucess or running state
            admin_status = self.validate_operator_installation()
            if not admin_status:
                self.logger.logger.error(f"Validation of the operator installation failed.")
                return False
            
            #Check that operator version
            # version_chk = self.operator_version_check()
            # if not version_chk:
            #     self.logger.logger.error(f"Operator version check Failed.")
            #     return False

            #Switching the project name to operand namespace
            self.logger.logger.info(f'Making new namespace from {self.project_name} to {namespace}.')
            self.project_name = namespace
            return True

        except configparser.Error as e:
            self.logger.logger.error(f"Error reading configuration: {e}")
            return False
        except pexpect.exceptions.EOF:
            self.logger.logger.error("EOF reached. Script terminated unexpectedly.")
            return False
        except pexpect.exceptions.TIMEOUT:
            self.logger.logger.error("Timeout reached. Script execution took too long.")
            return False
        except Exception as e:
            self.logger.logger.error(f"Error: {str(e)}")
            return False

    def coping_certs(self):
        """
        Name: coping_certs
        Desc: function to copy certificates (ldap, db) to the certificate folder
        Parameters:
            None
        Returns:
            Boolean: True/False
        """
        try:
            #Copy db certs
            self.logger.logger.info("Coping the DB certificates")
            present_dir = os.getcwd()
            src_dir = present_dir + '/certs/' + self.db
            dest_dir = self.property_folder + 'cert/db/'
            os.system('cp -rf '+ src_dir + ' ' + dest_dir)
            self.logger.logger.info(f'Certificates coping from {src_dir} to {dest_dir}')
            self.logger.logger.info(f"DB {self.db} certificates copied successfully.")

            #Copy ldap certs
            self.logger.logger.info("Coping the  LDAP certificates.")
            src_dir = present_dir +'/certs/' + self.ldap + '/*'
            dest_dir = self.property_folder  +'cert/ldap/'
            os.system('cp -rf '+ src_dir + ' ' + dest_dir)

            # Copying the postgres certificates to bts/zen/im folders
            if self.external_db.lower() == 'yes':
                self.logger.logger.info("Coping the postgres certificates to bts/zen/im folders.")
                src_dir = present_dir + '/certs/postgres/*'

                self.logger.logger.info("Coping the postgres certificates to BTS folders.")
                dest_dir = self.property_folder + 'cert/bts_external_db/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

                self.logger.logger.info("Coping the postgres certificates to ZEN folders.")
                dest_dir = self.property_folder + 'cert/zen_external_db/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

                self.logger.logger.info("Coping the postgres certificates to IM folders.")
                dest_dir = self.property_folder + 'cert/im_external_db/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

            # Copying the external certificates to cp4ba_tls_issuer
            if self.extcrt.lower() == 'yes':
                self.logger.logger.info("Coping the cp4ba_tls_issuer certificates to propertyfile/cert/cp4ba_tls_issuer folders.")
                src_dir = present_dir + '/certs/cp4ba_tls_issuer/*'

                self.logger.logger.info("Coping the postgres certificates to BTS folders.")
                dest_dir = self.property_folder + 'cert/cp4ba_tls_issuer/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

            self.logger.logger.info("Coping of LDAP/DB certificates is done successfully.")
            return True
        except Exception as e:
            self.logger.logger.error(f"Error: {str(e)}")
            return False

    def property_update(self):
        """
        Name: property_update
        Desc: function to update property files
        Parameters:
            None
        Returns:
            Boolean: True/False
        """
        try:
            #Updating the ldap property file
            self.logger.logger.info(f"Updating the cp4ba_LDAP.property")
            ldap_data = ''
            ldap_data = '_' + self.ldap
            ldap_data = ldap_data.upper()
            config = CustomConfigObj(self.property_folder + "cp4ba_LDAP.property")
            splitter = "_"
            ldap_property = self.updater(config, splitter, ldap_data)
            if not ldap_property:
                self.logger.logger.error(f"Updating property file {self.property_folder}cp4ba_LDAP.property failed.")
                return False
 
            #Updating the user profile property file
            self.logger.logger.info(f"Updating the cp4ba_user_profile.property")
            config = CustomConfigObj(self.property_folder + "cp4ba_user_profile.property")
            splitter = "."
            usre_profile = self.updater(config, splitter, ldap_data)
            if not usre_profile:
                self.logger.logger.error(f"Updating property file {self.property_folder}cp4ba_user_profile.property failed.")
                return False

            #No change in the db related property file if the db is postgresedb
            if self.db.lower() != 'postgresedb':
                #Updating the cp4ba_db_server property file
                self.logger.logger.info(f"Updating the cp4ba_db_server.property")
                splitter = "."
                db_alias = self.db.upper()
                config = CustomConfigObj(self.property_folder + "cp4ba_db_server.property")
                db_server = self.updater(config, splitter, db=db_alias, file_name=True)
                if not db_server:
                    self.logger.logger.error(f"Updating property file {self.property_folder}cp4ba_db_server.property failed.")
                    return False

                #Updating the cp4ba_db_name_user property file
                self.logger.logger.info(f"Updating the cp4ba_db_name_user.property")
                config = CustomConfigObj(self.property_folder + "cp4ba_db_name_user.property")
                db_name = self.updater(config, splitter, db=db_alias)
                if not db_name:
                    self.logger.logger.error(f"Updating property file {self.property_folder}cp4ba_db_name_user.property failed.")
                    return False

            self.logger.logger.info(f"All the property files are updated successfully.")
            return True
        except Exception as e:
            self.logger.logger.error(f"Error: {str(e)}")
            return False

    def valiate_cluster_component(self, cmd):
        """
            Name: valiate_cluster_component
            Desc: Get the result values of the oc commands
            Raises:
                ValueError: If the return value is False. 
        """

        try:
            time.sleep(5)
            self.logger.logger.info(f"Running the command {cmd} to get validate cluster components ")
            print(f"Running the command {cmd} to get validate cluster components ")
            process = subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            component_result = process.stdout.decode()
            self.logger.logger.info(f"Commad result :{component_result}")
            print(f"Commad result :{component_result}")
            if process.returncode == 0:
                return True, component_result 
            else:
                self.logger.logger.error(f"Error: {process.stderr}")
                self.logger.logger.error(f"Error in processing the subprocess : {process.stderr}")
                raise subprocess.CalledProcessError(process.returncode, process.args)
        except subprocess.CalledProcessError as e:
            self.logger.logger.error(f"Error: Script returned an error: {e}")
            print(f"Error: Script returned an error: {e}")
            return False, False
        except Exception as e:
            self.logger.logger.error(f"Error: Script returned an error: {e}")
            print(f"Error: Script returned an error: {e}")
            return False, False

    def property_setup(self):
        """
        Name: property_setup
        Desc: function to setup the property
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """
        try:
            self.logger.logger.info('Property creation starting.')
            self.logger.logger.info(f'Db = {self.db} Ldap = {self.ldap} Project = {self.project_name}')
            self.logger.logger.info(f'Property script is {self.property_script}')
            process = pexpect.spawn("bash  " + self.property_script + " -n " + self.project_name)
            self.logger.logger.info(f'Command running is {"bash  " + self.property_script + " -n " + self.project_name}.')   

            # Checking that the cp4ba fips status to show the question following question
            # Your OCP cluster has FIPS enabled, do you want to enable FIPS with this CP4BA deployment？
            oc_cmd1 = f'oc get configmap cp4ba-fips-status --no-headers --ignore-not-found -n {self.project_name} -o '
            oc_cmd2 = 'jsonpath={.data.all-fips-enabled}'
            status, respo = self.valiate_cluster_component(oc_cmd1 + oc_cmd2)
            if 'no' in respo.lower():
                status = False

            self.logger.logger.info(f'Checking the vault')
            if vault_instana_branch_check(self.branch):
                self.logger.logger.info(f'#Do you want to enable external Vault integration for FileNet Content Manager (y/n, Default is No)?:{self.vault.upper()}')
                process.sendline(self.vault.upper())

            #To select the Cloud Pak for Business Automation capability to install:  
            #sending 1 to select FileNet Content Manager 
            process.sendline('1')
            self.logger.logger.info('FileNet Content Manager selected')
            process.sendline()

            # Select optional components: 
            # 1) Content Search Services (Selected)
            # 2) Content Management Interoperability Services (Selected)
            # 3) IBM Enterprise Records (Selected)
            # 4) IBM Content Collector for SAP (Selected)
            # 5) Business Automation Insights (Selected)
            # 6) Task Manager (Selected)
                                   
            component_mapping = {
                "content search services": '1',
                "content management interoperability services": '2',
                "ibm enterprise records": '3',
                "ibm content collector for sap": '4',
                "business automation insights": '5',
                "task manager": '6'
            }

            # Split component_names into a list or set to default to "all components"
            self.logger.logger.info(f'Component name: {self.component_names}, type is {type(self.component_names)}')
            for com in self.component_names:
                # Ensure the component exists in the mapping
                if com in component_mapping:
                    self.logger.logger.info(f'Component Mapping value {component_mapping[com]}')
                    process.sendline(component_mapping[com])
                    self.logger.logger.info(f'Selected Component: {com} and ComponentNo:{component_mapping[com]}')
                else:
                    self.logger.logger.error(f'Component {com} not found in component mapping.')
            process.sendline()
            
            # What is the LDAP type that is used for this deployment? 
            # 1) Microsoft Active Directory
            # 2) IBM Tivoli Directory Server / Security Directory Server
            # Enter a valid option [1 to 2]: 
            self.logger.logger.info(f'What is the LDAP type that is used for this deployment? {self.ldap_type_number}')
            process.sendline(self.ldap_type_number)

            # To provision the persistent volumes and volume claims
            # please enter the file storage classname for slow storage(RWX): 
            self.logger.logger.info(f'please enter the file storage classname for slow storage(RWX): {self.storage_name}')
            process.sendline(self.storage_name)
            process.sendline(self.storage_name)
            process.sendline(self.storage_name)
            process.sendline(self.storage_name)

            # Please select the deployment profile (default: small).  Refer to the documentation in CP4BA Knowledge Center for details on profile.
            # 1) small
            # 2) medium
            # 3) large
            # Enter a valid option [1 to 3]: 
            self.logger.logger.info(f'Please select the deployment profile (default: small).  Refer to the documentation in CP4BA Knowledge Center for details on profile: 1')
            process.sendline('1')

            ##What is the Database type that is used for this deployment? 
            ## 1) IBM Db2 Database
            ## 2) Oracle
            ## 3) Microsoft SQL Server
            ## 4) PostgreSQL
            ## 5) PostgreSQL EDB (deployed by CP4BA Operator)

            #For 2500
            # What is the Database type that is used for this deployment? 
            # 1) IBM Db2 Database
            # 2) IBM Db2 HADR
            # 3) IBM Db2 RDS
            # 4) IBM Db2 RDS HADR
            # 5) Oracle
            # 6) Microsoft SQL Server
            # 7) PostgreSQL
            # 8) PostgreSQL EDB (deployed by CP4BA Operator)
            # Enter a valid option [1 to 8]: 
            self.logger.logger.info(f'What is the Database type that is used for this deployment? {self.db_type_number}')
            process.sendline(self.db_type_number)

            # Enter the alias name(s) for the database server(s)/instance(s) to be used by the CP4BA deployment.
            # (NOTE: NOT the host name of the database server, and CANNOT include a dot[.] character)
            # (NOTE: This key supports comma-separated lists (for example: dbserver1,dbserver2,dbserver3)
            # The alias name(s): 
            self.logger.logger.info(f' Enter the alias name(s) for the database server(s)/instance(s) to be used by the CP4BA deployment. The alias name(s): {self.db}')
            process.sendline(self.db)

            #project name not asked in case of separation of duties
            # Where do you want to deploy Cloud Pak for Business Automation?
            # Enter the name for an existing project (namespace):
            self.logger.logger.info(f'Where do you want to deploy Cloud Pak for Business Automation?: {self.project_name}')
            process.sendline(self.project_name)
            time.sleep(5)
            
            # process.expect('Do you want to restrict network egress to unknown external destination for this CP4BA deployment*')
            if status:
                # Your OCP cluster has FIPS enabled, do you want to enable FIPS with this CP4BA deployment？ (Notes: If you select "Yes", in order to complete enablement of FIPS for CP4BA, please refer to "FIPS wall" configuration in IBM documentation.) (Yes/No, default: No):
                self.logger.logger.info(f'Your OCP cluster has FIPS enabled, do you want to enable FIPS with this CP4BA deployment？ (Notes: If you select "Yes", in order to complete enablement of FIPS for CP4BA, please refer to "FIPS wall" configuration in IBM documentation.) (Yes/No, default: No): {self.fips}')
                process.sendline(self.fips)

            # Do you want to restrict network egress to unknown external destination for this CP4BA deployment? (Notes: CP4BA 24.0.0 prevents all network egress to unknown destinations by default. You can either (1) enable all egress or (2) accept the new default and create network policies to allow your specific communication targets as documented in the knowledge center.) (Yes/No, default: Yes): 
            self.logger.logger.info(f'Do you want to restrict network egress to unknown external destination for this CP4BA deployment? (Notes: CP4BA 24.0.0 prevents all network egress to unknown destinations by default. You can either (1) enable all egress or (2) accept the new default and create network policies to allow your specific communication targets as documented in the knowledge center.) (Yes/No, default: Yes): : {self.egress}')
            process.sendline(self.egress)

            self.logger.logger.info(f'Checking the Instana')
            if vault_instana_branch_check(self.branch):
                self.logger.logger.info(f'#Do you want to enable external Vault integration for FileNet Content Manager (y/n, Default is No)?:{self.vault.upper()}')
                process.sendline(self.instana.upper())

            if self.db == 'postgres':
                # Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE APPLY CP4BA CUSTOM RESOURCE] as IM metastore DB for this CP4BA deployment? (Notes: IM service can use an external Postgres DB to store IM data. If select "Yes", IM service uses an external Postgres DB as IM metastore DB. If select "No", IM service uses an embedded cloud native postgresql DB as IM metastore DB.) (Yes/No, default: No): 
                self.logger.logger.info(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE APPLY CP4BA CUSTOM RESOURCE] as IM metastore DB for this CP4BA deployment? (Notes: IM service can use an external Postgres DB to store IM data. If select "Yes", IM service uses an external Postgres DB as IM metastore DB. If select "No", IM service uses an embedded cloud native postgresql DB as IM metastore DB.) (Yes/No, default: No): {self.external_db}')
                process.sendline(self.external_db)

                # Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE APPLY CP4BA CUSTOM RESOURCE] as Zen metastore DB for this CP4BA deployment? (Notes: Zen stores all metadata such as users, groups, service instances, vault integration, secret references in metastore DB. If select "Yes", Zen service uses an external Postgres DB as Zen metastore DB. If select "No", Zen service uses an embedded cloud native postgresql DB as Zen metastore DB ) (Yes/No, default: No): 
                self.logger.logger.info(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE APPLY CP4BA CUSTOM RESOURCE] as Zen metastore DB for this CP4BA deployment? (Notes: Zen stores all metadata such as users, groups, service instances, vault integration, secret references in metastore DB. If select "Yes", Zen service uses an external Postgres DB as Zen metastore DB. If select "No", Zen service uses an embedded cloud native postgresql DB as Zen metastore DB ) (Yes/No, default: No): {self.external_db}')
                process.sendline(self.external_db)

                #  Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE APPLY CP4BA CUSTOM RESOURCE] as BTS metastore DB for this CP4BA deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No): 
                self.logger.logger.info(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE APPLY CP4BA CUSTOM RESOURCE] as BTS metastore DB for this CP4BA deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No): {self.external_db}')
                process.sendline(self.external_db)

            # Do you want to use an external certificate (root CA) for this Opensearch/Kafka deployment? (Notes: Opensearch/Kafka operator can consume external tls certificate. If select "No", CP4BA operator will creates leaf certificates based CP4BA's root CA ) (Yes/No, default: No): 
            self.logger.logger.info(f'Do you want to use an external certificate (root CA) for this Opensearch/Kafka deployment? (Notes: Opensearch/Kafka operator can consume external tls certificate. If select "No", CP4BA operator will creates leaf certificates based CP4BAs root CA ) (Yes/No, default: No): {self.extcrt}')
            process.sendline(self.extcrt)

            pattern = re.compile(r'.*' + re.escape('How many object stores will be deployed for the content') + r'.*')
            process.expect(pattern, timeout=240)

            # How many object stores will be deployed for the content pattern? 
            process.sendline('1')

            property_setup_output = (process.before).decode('utf-8')
            self.logger.logger.info(f'property_setup_output :  {property_setup_output}')

            property_setup_after = (process.after).decode('utf-8')
            self.logger.logger.info(f'property_setup_after :  {property_setup_after}')

            self.logger.logger.info(f"Created the property files for db {self.db} and ldap {self.ldap} in the project {self.project_name}")
            time.sleep(5)

            # To copy certificates to the db/ldap folders
            copy_cert_status = self.coping_certs()
            if not copy_cert_status:
                self.logger.logger.error(f"Coping the certificates is failed.")
                return False

            # To copy certificates to the db/ldap folders
            property_update_status = self.property_update()
            if not property_update_status:
                self.logger.logger.error(f"Property update is failed.")
                return False

            return True
        except Exception as e:
            self.logger.logger.error(f"Error: {str(e)}")
            return False
    
    def validate_deployment(self):
        """
        Name: validate_deployment
        Desc: Validating the deployment is correct or not
        Raises:
            ValueError: If the return value is False. 
        """
        try:
            # Run oc get content command
            get_content_command = ['oc', 'get', 'content', '-n', self.project_name]
            result = subprocess.run(get_content_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check the output to determine if content is present
            if result.stdout.decode() == '':
                print("Deployment creation failed.")
                return False
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error running oc get content command: {e}")
            print("Deployment creation failed.")
            return False

    def set_navconfiguration(self):
        """
        Name: set_navconfiguration
        Desc: Setting up the navigator configuration for the jmail
        Raises:
            ValueError: If the return value is False.
        """
        try:
            # Getting the values from the configuration file
            jmail_username = self.parser.get('NAV_CONFIGURATION', 'JMAIL_USER_NAME')
            jmail_password = self.parser.get('NAV_CONFIGURATION', 'JMAIL_USER_PASSWORD')
            jmail_host = self.parser.get('NAV_CONFIGURATION', 'HOST')
            jmail_sender = self.parser.get('NAV_CONFIGURATION', 'SENDER')
            jmail_ssl = self.parser.get('NAV_CONFIGURATION', 'SSL_ENABLED')
            if jmail_ssl.lower() == 'true':
                jmail_ssl = True
            else:
                jmail_ssl = False
            navigator_configuration = {'navigator_configuration': {'java_mail': {'host': jmail_host, 'sender':jmail_sender, 'ssl_enabled':bool(jmail_ssl)}}}
            self.logger.logger.info(f'Navigator configurations : {navigator_configuration}')
            return navigator_configuration

        except  Exception as e:
            print(f"Error in creating the navigator configuration: {e}")
            return False

    def run_command(self, cmd):
        """
        Name: run_command
        Desc: Running the command which we provided
        Params:
            cmd: command list
            logger: Object for the logging purpose
        Returns:
            Boolean: True/False
        """

        try:
            self.logger.logger.info(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if result.stdout:
                self.logger.logger.debug(f"Command stdout: {result.stdout}")
            if result.stderr:
                self.logger.logger.warning(f"Command stderr: {result.stderr}")
            self.logger.logger.info(f"Command completed successfully with return code: {result.returncode}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.logger.error(f"Command failed: {' '.join(cmd)}")
            self.logger.logger.error(f"Return code: {e.returncode}")
            if e.stdout:
                self.logger.logger.error(f"Stdout: {e.stdout}")
            if e.stderr:
                self.logger.logger.error(f"Stderr: {e.stderr}")
            return False
        except FileNotFoundError as e:
            self.logger.logger.error(f"Command not found: {' '.join(cmd)}")
            self.logger.logger.error(f"Error: {str(e)}")
            return False
        except Exception as e:
            self.logger.logger.error(f"Unexpected error running command: {' '.join(cmd)}")
            self.logger.logger.error(f"Error: {str(e)}")
            return False
        
    def pathupdate_dataconfig(self):
        """
        Name: pathupdate_dataconfig
        Desc: To find and replace the project property folder for 24.00 ifix onwards. From ifix onwards project folder structure is changed
        Params:
           self
        Returns:
            Boolean: True/False
        """
        
        try:
            self.logger.logger.info("Starting pathupdate_dataconfig function")
            self.logger.logger.info(f"Branch: {self.branch}, Type: {type(self.branch)}")
            
            # Check branch condition
            if self.branch == '24.0.0':
                self.logger.logger.info("Branch is 24.0.0, skipping path updates")
                return True
            
            self.logger.logger.info(f"Branch is not 24.0.0, proceeding with path updates")
            
            # Update project name if separation duty is enabled
            if hasattr(self, 'separation_duty_on') and self.separation_duty_on == 'yes':
                if hasattr(self, 'operand_namespace_suffix'):
                    original_project_name = self.project_name
                    self.project_name = str(self.project_name) + str(self.operand_namespace_suffix)
                    self.logger.logger.info(f"Updated project name from '{original_project_name}' to '{self.project_name}' due to separation duty")
                else:
                    self.logger.logger.warning("separation_duty_on is 'yes' but operand_namespace_suffix is not set")
            
            # Validate data.config file exists
            current_dir = os.getcwd()
            dataconfig_path = os.path.join(current_dir, 'config', 'data.config')
            
            self.logger.logger.info(f"Current directory: {current_dir}")
            self.logger.logger.info(f"Data config path: {dataconfig_path}")
            
            if not os.path.exists(dataconfig_path):
                self.logger.logger.error(f"data.config file not found at: {dataconfig_path}")
                return False
            
            if not os.access(dataconfig_path, os.R_OK | os.W_OK):
                self.logger.logger.error(f"data.config file is not readable/writable: {dataconfig_path}")
                return False
                
            self.logger.logger.info(f"data.config file validated successfully")
            
            # Create backup of data.config
            backup_path = dataconfig_path + ".backup"
            try:
                import shutil
                shutil.copy2(dataconfig_path, backup_path)
                self.logger.logger.info(f"Created backup at: {backup_path}")
            except Exception as e:
                self.logger.logger.warning(f"Failed to create backup: {e}")
            
            # Helper function to validate and perform sed replacement
            def perform_sed_replacement(replace_from, replace_with, target_path, description):
                self.logger.logger.info(f"=== {description} ===")
                self.logger.logger.info(f"Target file: {target_path}")
                self.logger.logger.info(f"Replace FROM: '{replace_from}'")
                self.logger.logger.info(f"Replace WITH: '{replace_with}'")
                
                # Check if target file exists
                if not os.path.exists(target_path):
                    self.logger.logger.error(f"Target file does not exist: {target_path}")
                    return False
                
                # Check if pattern exists in file before replacement
                try:
                    with open(target_path, 'r') as f:
                        content = f.read()
                    
                    pattern_count = content.count(replace_from)
                    self.logger.logger.info(f"Pattern '{replace_from}' found {pattern_count} times in {target_path}")
                    
                    if pattern_count == 0:
                        self.logger.logger.warning(f"Pattern '{replace_from}' not found in {target_path} - skipping replacement")
                        return True  # Not an error, just no match
                        
                except Exception as e:
                    self.logger.logger.error(f"Error reading file {target_path}: {e}")
                    return False
                
                # Perform sed replacement
                cmd = ["sed", "-i", f"s;{replace_from};{replace_with};g", target_path]
                result = self.run_command(cmd)
                
                if result:
                    self.logger.logger.info(f"✓ Successfully completed {description}")
                else:
                    self.logger.logger.error(f"✗ Failed {description}")
                
                return result
            
            # 1. Replace the property file folder path
            if not perform_sed_replacement(
                'cp4ba-prerequisites/propertyfile',
                f'cp4ba-prerequisites/project/{self.project_name}/propertyfile',
                dataconfig_path,
                "property file folder path replacement"
            ):
                return False

            # 2. Replace the db file path
            if not perform_sed_replacement(
                'scripts/cp4ba-prerequisites/dbscript',
                f'scripts/cp4ba-prerequisites/project/{self.project_name}/dbscript',
                dataconfig_path,
                "db file path replacement"
            ):
                return False

            # 3. Replace the prereq folder path
            if not perform_sed_replacement(
                'PREREQ_FOLDER=/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/',
                f'PREREQ_FOLDER=/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/project/{self.project_name}/',
                dataconfig_path,
                "prereq folder path replacement"
            ):
                return False

            # 4. Generated CR path update
            if not perform_sed_replacement(
                'GENERATED_CR=/opt/ibm-cp-automation/scripts/generated-cr/',
                f'GENERATED_CR=/opt/ibm-cp-automation/scripts/generated-cr/project/{self.project_name}/',
                dataconfig_path,
                "generated CR path replacement"
            ):
                return False

            # 5. Handle postgres-specific script update
            if hasattr(self, 'db') and self.db == 'postgres':
                scriptpath = os.path.join(current_dir, 'certs/scripts/ibm-cp4ba-db-ssl-cert-secret-for-postgres.sh')
                self.logger.logger.info(f"Database is postgres, checking script: {scriptpath}")
                
                if os.path.exists(scriptpath):
                    if not perform_sed_replacement(
                        'scripts/cp4ba-prerequisites/propertyfile',
                        f'scripts/cp4ba-prerequisites/project/{self.project_name}/propertyfile',
                        scriptpath,
                        "postgres script path replacement"
                    ):
                        return False
                else:
                    self.logger.logger.warning(f"Postgres script not found: {scriptpath} - skipping")

            # 6. Update external certificate path
            if not perform_sed_replacement(
                'cp4ba-prerequisites/propertyfile/cert/cp4ba_tls_issuer',
                f'cp4ba-prerequisites/project/{self.project_name}/propertyfile/cert/cp4ba_tls_issuer',
                dataconfig_path,
                "external certificate path replacement"
            ):
                return False

            self.logger.logger.info(f"✓ Successfully completed pathupdate_dataconfig with branch '{self.branch}' and project name '{self.project_name}'")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"✗ Exception in pathupdate_dataconfig: {str(e)}")
            self.logger.logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            self.logger.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def cloning_repo(self):
        """
        Function name: clonning_repo
        Desc: Creating the directory and clonning the 2400 to the directory
        Params: 
            None
        Return:
            None
        """  
        try:
            #Removing the folder first
            self.logger.logger.info(f'Removing the {self.clone_folder}')
            shutil.rmtree(self.clone_folder)

            #Clonning into the folder
            self.logger.logger.debug(f'Clonning the repo {self.clone_repo} into {self.clone_folder} ')
            git.Repo.clone_from(self.clone_repo, self.clone_folder, 
                    branch=self.git_branch, depth=1, multi_options=['--recurse-submodules', '--shallow-submodules'])
            self.logger.logger.info(f'Clonning is done.')
            return True
        except FileNotFoundError as e:
            self.logger.logger.info(f'File not found. So creating the {self.clone_folder} and retrying...')
            os.makedirs(self.clone_folder)
            self.cloning_repo()
        except Exception as e:
            self.logger.logger.info(f'Error in cloning because of {e}')
            return False

    def check_resource(self, resource_cmd, check_against):
        """
        Function name: check_resource
        Desc: Checking resource ICSP available or not for production ER and Fresh
        Params:
            resource_cmd : Command to run
            check_against: Validating against the expected one
        Return:
            True/False
        """

        try:
            self.ocp_login()
        except Exception as e:
            self.logger.logger.error(f'Running the command to check the login Failed with error {e}')
            return False

        try:
            result = subprocess.run(resource_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = result.stdout.decode().split()
            self.logger.logger.info(f'Checking the {check_against} in the list {str(result)}')
            if check_against in result:
                return True
        except Exception as e:
            self.logger.logger.error(f'Running the command to check the resource {str(resource_cmd)}, checking against {check_against} is failed with error {e}')
            return False
 
    def check_cluster(self, resource_cmd):
        """
        Function name: check_cluster
        Desc: Checking Cluster is enabled with required resources
        Params:
            resource_cmd : Command to run
        Return:
            True/False
        """
        try:
            result = subprocess.run(resource_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = result.stdout.decode().split()
            self.logger.logger.info(f'Cluster is Fips Enabled. Result is {result}')
            return True
        except Exception as e:
            self.logger.logger.error(f'Cluster is Fips Disabled.')
            return False

    def create_dbscript_folder(self, db_filepath):
        """
        Function name: create_dbscript_folder
        Desc: Creating the /opt/ibm-cp-automation/scripts/cp4ba-prerequisites/dbscript folder
        Params:
            db_filepath: File path of the db (IM/BTS/ZEN)
        Return:
            True/False
        """
        try:
            dirname = os.path.dirname(db_filepath)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
                self.logger.logger.info(f'Creating folder {dirname} success.')
            else:
                self.logger.logger.info(f'Folder {dirname} already available.')
            return True
        except Exception as e:
            self.logger.logger.error(f'Creating folder {dirname} failed. Error is {e}')
            return False

    def create_sql(self):
        """
        Function name: create_sql
        Desc: Creating the sql statement file
        Params:
            db_name: Name of the database
        Return:
            True/False
        """
        try:
            #Fetching the db related values
            db_name = ''
            section = 'CP4BA_'+self.ldap.upper()
            dbuser = self.parser.get(section, 'CP4BA.IM_EXTERNAL_POSTGRES_DATABASE_USER').strip('\"')
            dbpass = self.parser.get(section, 'EXTERNAL_POSTGRES_DATABASE_USER_PASSWD').strip('\"')
            host_shortname = fetch_host_shortname()

            # Reading the content of the file using the read() function and storing them in a new variable
            current_dir = os.getcwd()
            with open(current_dir + '/config/ext_db_template.sql', 'r') as file:
                sql_statement_template = file.read()

            # Creating each sql files with statements
            self.postgres_createIM = self.parser.get('DATABASE_CONFIG', 'postgres_createIM').strip()
            self.postgres_createZEN = self.parser.get('DATABASE_CONFIG', 'postgres_createZEN').strip()
            self.postgres_createBTS = self.parser.get('DATABASE_CONFIG', 'postgres_createBTS').strip()

            # Checking the dbscript folder already there or not, if not creating it
            dbscript_status = self.create_dbscript_folder(self.postgres_createIM)
            if not dbscript_status:
                self.logger.logger.error(f'Creating folder {self.postgres_createIM} failed.')
                return False

            file_names = {'im': self.parser.get('DATABASE_CONFIG', 'postgres_createIM').strip(), 'zen': self.parser.get('DATABASE_CONFIG', 'postgres_createZEN').strip(), 'bts': self.parser.get('DATABASE_CONFIG', 'postgres_createBTS').strip()}
            for db_name,file_fullpath in file_names.items():
                db_name = db_name + '_' + host_shortname.lower()
                self.logger.logger.info(f'Creating the sql statement for the database {db_name}')
                sql_statement = sql_statement_template.format(dbuser = dbuser, dbuserpwd = dbpass, tablespace = db_name+'_tbs', dbname = db_name, dbschema = dbuser)

                # Saving into /opt/ibm-cp-automation/scripts/cp4ba-prerequisites/project/{namespae}/dbscript/ folder
                with open(file_fullpath, "w") as text_file:
                    self.logger.logger.info(f'Writing the sql statement for the database {db_name} into file {file_fullpath}')
                    text_file.write(sql_statement)
            return True
        except Exception as e:
            self.logger.logger.error(f'Creating the sql statement for the database {db_name} failed. Error is {e}')
            return False

    def check_pullsecret(self):
        """
        Function name: check_pullsecret
        Desc: Checking Cluster is enabled with required pull-secrets
        Params:
            None
        Return:
            True/False
        """
        try:
            #Creating the file to save secrets
            pull_secret_file = './config/pull-secret.json'
            cmd = [f'touch {pull_secret_file}']
            self.logger.logger.info(f'Creating the pull-secret.json file using the command {cmd}')
            self.check_cluster(cmd)

            # Saving the secrets into file {pull_secret_file}
            self.logger.logger.info(f'Getting all the pull-secrets and saving it in {pull_secret_file}')
            cmd = ["oc get secret/pull-secret -n openshift-config --template='{{index .data \".dockerconfigjson\" | base64decode}}' >./config/pull-secret.json"]
            self.check_cluster(cmd)

            # Pulling the details from the data.config
            pull_secret = dict(self.parser.items('PULL_SECRET'))
            usrname_and_pass = pull_secret['userandpass']
            cp_prod = pull_secret['cp_prod']
            cp_stg = pull_secret['cp_stg']

            # Reading the pull-secret.json file to removing data incase of prod ER
            if self.stage_prod != 'dev':
                with open(pull_secret_file, 'r') as file:
                    data = json.load(file)

            try:
                # Updating the file with the secrets
                self.logger.logger.info(f'Running through loop and updating the pull-secrets')
                is_svl_machine = svl_machine(self.cluster_name)
                if is_svl_machine:
                    custom_img_list = pull_secret['custom_img_list'].split(',')
                else:
                    custom_img_list = pull_secret['custom_img_list_rtp'].split(',')

                # Looping through pull secrets and adding it to the pull-secret file
                for img_list in custom_img_list:

                    # Removing data incase of prod ER
                    if self.stage_prod != 'dev':
                        self.logger.logger.info(f'Deleting {img_list}')
                        removed_value = data['auths'].pop(img_list)
                    else:
                        cmd = [f'oc registry login --registry="{img_list}" --auth-basic="{usrname_and_pass}" --to={pull_secret_file}']
                        self.logger.logger.info(f'Updating the pull secret using command {cmd}')
                        self.check_cluster(cmd)
            except Exception as e:
                self.logger.logger.error(f'Error in Delete or Updte {e}')

            # Writing the data into pull-secret.json file incase of prod ER
            if self.stage_prod != 'dev':
                with open(pull_secret_file, 'w') as file:
                    json.dump(data, file)

            # Updating the cp.icr.io into the file
            cmd = [f'oc registry login --registry="cp.icr.io" --auth-basic="cp:{cp_prod}" --to={pull_secret_file}']
            self.logger.logger.info(f'Updating the cp.icr.io using command {cmd}')
            self.check_cluster(cmd)

            # Updating the cp.icr.io into the file
            cmd = [f'oc registry login --registry="cp.stg.icr.io" --auth-basic="cp:{cp_stg}" --to={pull_secret_file}']
            self.logger.logger.info(f'Updating the cp.stg.icr.io using command {cmd}')
            self.check_cluster(cmd)

            # Setting the secrets with the updated pullsecretsvalues
            cmd = [f'oc set data secret/pull-secret -n openshift-config --from-file=.dockerconfigjson={pull_secret_file}']
            self.logger.logger.info(f'Setting the pull-secret using command {cmd}')
            self.check_cluster(cmd)
            return True
        except Exception as e:
            self.logger.logger.error(f'Setting the pull-secret failed. Error is {e}')
            return False

    def create_storage_class(self):
        """
            Name: create_storage_class
            Author: Dhanesh
            Desc: To create the storage class in a newly created cluster
            Parameters:
                none
            Returns:
                none
            Raises:
                Exception, ValueError
        """
        try:
            current_dir = os.getcwd()
            current_dir = os.path.join(current_dir, 'config/managed-nfs')
            print(f'Navigating to {current_dir}')
            os.chdir(current_dir)
            print(f'Current working directory: {os.getcwd()}')

            # Running the script and creating a new managed-nfs-storage storage class
            self.logger.logger.info('Storage class creation initiated....')
            print('Storage class creation initiated....')
            storage_class_creation_script = './CreateStorageClass.sh'
            subprocess.run([f'chmod +x {storage_class_creation_script}'], shell = True, check = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process = subprocess.run([storage_class_creation_script], shell = True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f'Storage class creation result: \n{process.stdout.decode('utf-8')}')
            self.logger.logger.info(f'Storage class creation result: \n{process.stdout.decode('utf-8')}')
            self.logger.logger.info('Storage class creation completed.')
            print('Storage class creation completed.')

            #Verfying the storage class created successfully
            result = subprocess.run('oc get storageclass -o=jsonpath="{.items[*].metadata.name}" | grep managed-nfs-storage', shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.logger.info(f"Command oc get storageclass output: \n{result.stdout.decode('utf-8')}")
            print(f"Command oc get storageclass output: \n{result.stdout.decode('utf-8')}")

            #check if the command executed successfully
            if result.returncode == 0:
                if result.stderr:
                    print(f"Error: {result.stderr.decode('utf-8')}")
                    raise ValueError(f"Error: {result.stderr.decode('utf-8')}")
                else:
                    print('Command oc get storageclass executed successfully')
                    self.logger.logger.info('Command oc get storageclass executed successfully')
                    if 'managed-nfs-storage' in result.stdout.decode('utf-8').strip():
                        print('Storageclass class managed-nfs-storage created successfully')
                        self.logger.logger.info('Storageclass class managed-nfs-storage created successfully')
                    else:
                        self.logger.logger.info('Storageclass class managed-nfs-storage is not present in the output')
                        raise ValueError('Storageclass class managed-nfs-storage is not present in the output')
            else:
                print('Command oc get storageclass execution was unsuccessful')
                self.logger.logger.error('Command oc get storageclass execution was unsuccessful')
                raise ValueError(f"Command returned an error: \n{result.stderr.decode('utf-8')}")
            
        except Exception as e:
            self.logger.logger.error(f'Storage class creation failed with error {e}')
            raise Exception(f'Storage class creation failed with error {e}')
        finally:
            print('Navigating to root folder: cp4ba_proddeploy_automation')
            os.chdir('/opt/Cp4ba-Automation/cp4ba_proddeploy_automation')
            print(f'Current working directory: {os.getcwd()}')
    
    def create_user(self):
        """
            Name: create_user
            Author: Dhanesh
            Desc: To create a new user
            Parameters:
                none
            Returns:
                none
            Raises:
                Exception
        """
        try:

            #Login to ocp cluster
            self.ocp_login()
            
            current_dir = os.getcwd()
            current_dir = os.path.join(current_dir, 'config/Users')
            print(f'Navigating to {current_dir}')
            os.chdir(current_dir)
            print(f'Current working directory: {os.getcwd()}')

            # Creating new user
            self.logger.logger.info('Creating new user....')
            print('Creating new user....')
            user_creation_script = f'./CreateUser.sh -u {self.username} -p {self.password}'
            print(user_creation_script)
            subprocess.run(['chmod +x ./CreateUser.sh'], shell = True, check = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process = pexpect.spawn("bash  " + user_creation_script)
            pattern = re.compile(r'.*' + re.escape('cluster configured') + r'.*')
            process.expect(pattern, timeout=120)
            print(process.before.decode('utf-8'))

            #verify user created
            time.sleep(300)
            os.system('clear')
            print(f'Logging in with new user {self.username}....')
            user_login_command = 'oc login -u ' + self.username + ' -p ' + self.password
            print(user_login_command)
            
            #Login to the user created
            process = pexpect.spawn(user_login_command)
            pattern = re.compile(r'.*' + re.escape('Login successful') + r'.*')
            process.expect(pattern, timeout=60)
            print(process.before.decode('utf-8'))
            print(f'User {self.username} logged in successfully.')

            #Login to ocp cluster
            self.ocp_login()

            result = subprocess.run(f'oc get user | grep {self.username}', shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.logger.info(f"Command oc get user output: \n{result.stdout.decode('utf-8')}")
            print(f"Command oc get user output: \n{result.stdout.decode('utf-8')}")

            #check if the command executed successfully
            if result.returncode == 0:
                if result.stderr:
                    print(f"Error: {result.stderr.decode('utf-8')}")
                    raise ValueError(f"Error: {result.stderr.decode('utf-8')}")
                else:
                    print('Command oc get user executed successfully')
                    self.logger.logger.info('Command oc get user executed successfully')
                    if self.username in result.stdout.decode('utf-8').strip():
                        print(f'User {self.username} created successfully')
                        self.logger.logger.info(f'User {self.username} created successfully')
                    else:
                        self.logger.logger.info(f'User {self.username} is not present in the output')
                        raise ValueError(f'User {self.username} is not present in the output')
            else:
                print('Command oc get user execution was unsuccessful')
                self.logger.logger.error('Command oc get user execution was unsuccessful')
                raise ValueError(f"Command returned an error: \n{result.stderr.decode('utf-8')}")
            
        except Exception as e:
            self.logger.logger.error(f'User creation failed with error {e}')
            raise Exception(f'User creation failed with error {e}')
        finally:
            print('Navigating to root folder: cp4ba_proddeploy_automation')
            os.chdir('/opt/Cp4ba-Automation/cp4ba_proddeploy_automation')
            print(f'Current working directory: {os.getcwd()}')
        
