import configparser
import os
from utils.utils_class import *
import json
import yaml
import time
import requests
from requests.auth import HTTPBasicAuth
from utils.common import svl_machine


class BaiUtils(Utils):

    def __init__(self, ldap='', project_name='', branch='master', stage_prod='dev', cluster_name='', cluster_pass='', seprationduty_on='no', external_db='no', extcrt='no', git_branch='master', egress='No', global_catalog='No'):
        
        #Getting and setting the configuration details
        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.parser.read(current_dir + '/config/bai_data.config')
        self.property_folder = self.parser.get('PREREQUISITES', 'PROPERTY_FOLDER')
        self.prereq_folder = self.parser.get('PREREQUISITES', 'PREREQ_FOLDER')
        self.script_folder = self.parser.get('PREREQUISITES', 'SCRIPT_FOLDER')
        self.property_script = self.script_folder + "bai-prerequisites.sh -m property"
        self.generatedcr_folder = self.parser.get('PREREQUISITES', 'GENERATED_CR')
        self.clone_folder = self.parser.get('PREREQUISITES', 'CLONE_FOLDER')
        self.clone_repo = self.parser.get('PREREQUISITES', 'CLONE_REPO')
        self.operand_namespace_suffix = self.parser.get('PREREQUISITES', 'OPERAND_NAMESPACE')
        self.storage_name = self.parser.get('PREREQUISITES', 'STORAGE_NAME')
        self.accept_license = self.parser.get('PREREQUISITES', 'ACCEPT_LICENSE')
        self.cloud_platform = self.parser.get('CLUSTER_ADMIN_SETUP', 'cloud_platform')
        self.external_db = external_db
        self.extcrt = extcrt.lower()
        self.global_catalog = global_catalog.lower()

        #Setting the ldap, project, branch etc
        #Check for the separation of duties
        self.seprationduty_on = seprationduty_on
        self.project_name = project_name
        self.branch = branch
        self.git_branch = git_branch
        self.egress = egress

        self.stage_prod = ''
        if stage_prod == 'dev':
           self.stage_prod = stage_prod

        #Cluster data
        self.cluster_name = cluster_name
        self.cluster_pass = cluster_pass
        self.ldap = ldap
        self.ldap_type_number(ldap)
        self.logger = DeploymentLogs()

        #Logging into the ocp
        if cluster_name == '' or cluster_pass == '':
            raise Exception("Please provide the cluster name.")
        super().ocp_login()
    
    def run_bai_clusteradmin_setup(self):
        """
        Name: run_bai_clusteradmin_setup
        Author: Dhanesh
        Desc: Install the operators using cluster admin script
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
            deployment_mode = self.parser.get('CLUSTER_ADMIN_SETUP', 'deployment_mode')
            deployment_type = self.parser.get('CLUSTER_ADMIN_SETUP', 'deployment_type')
            private_catalog = self.parser.get('CLUSTER_ADMIN_SETUP', 'private_catalog')
            namespace = self.project_name
            entitlement_key_exists = self.parser.get('CLUSTER_ADMIN_SETUP', 'entitlement_key_exists')
            self.logger.logger.info(f'Values for the cluster admin script :-  deployment_mode = {deployment_mode}, cloud_platform = {self.cloud_platform}, deployment_type ={deployment_type}, private_catalog = {private_catalog}, namespace = {namespace},  entitlement_key_exists ={entitlement_key_exists} ')
            print(f'Values for the cluster admin script :-  deployment_mode = {deployment_mode}, cloud_platform = {self.cloud_platform}, deployment_type ={deployment_type}, private_catalog = {private_catalog}, namespace = {namespace},  entitlement_key_exists ={entitlement_key_exists} ')
            
            #Dynamically fetching the dbauser number from the ocp
            dbauser_number = super().fetch_dbuser()
            if not dbauser_number:
                self.logger.logger.error('Error in fetching the dbauser number')
                return False   

            self.logger.logger.info(f'dbauser option number : {dbauser_number}')

            if entitlement_key_exists.lower() == 'yes':
                entitlement_key = self.parser.get('CLUSTER_ADMIN_SETUP', 'entitlement_key')
                if len(entitlement_key) < 190:
                    self.logger.logger.critical(f'Entitlement key {entitlement_key} is not valid')
                    print(f'Entitlement key {entitlement_key} is not valid')
                    return False   
            else:
                entitlement_key = None
                self.logger.logger.critical(f' Entitlement key is not provided - {entitlement_key}')
                print(f' Entitlement key is not provided - {entitlement_key}')
                return False   
            self.logger.logger.info(f' Entitlement key is valid.')
            print(f' Entitlement key is valid.')

            # The path to the script
            script_path = self.script_folder + 'bai-clusteradmin-setup.sh  ' + self.stage_prod
            self.logger.logger.info(f'Running the script {script_path}')
            print(f'Running the script {script_path}')

            # Start the script using pexpect
            child = pexpect.spawnu(f'{script_path}', timeout=None, logfile=None)
            time.sleep(5)

            # Do you wish setup your cluster for a online based IBM Business Automation Insights deployment or for a airgap/offline based IBM Business Automation Insights deployment: 
            # 1) Online
            # 2) Offline/Airgap
            # Enter a valid option [1 to 2]: 
            child.sendline(deployment_mode) 
            self.logger.logger.info(f'Deployment mode is : {deployment_mode}')
            print(f'Deployment mode is : {deployment_mode}')

            # Select the cloud platform to deploy: 
            # 1) RedHat OpenShift Kubernetes Service (ROKS) - Public Cloud
            # 2) Openshift Container Platform (OCP) - Private Cloud
            # Enter a valid option [1 to 2]:

            #From 25.0.0 verion
            # Select the cloud platform to deploy: 
            # 1) RedHat OpenShift Kubernetes Service (ROKS) - Public Cloud
            # 2) Openshift Container Platform (OCP) - Private Cloud
            # 3) Other ( Rancher Kubernetes Engine (RKE) / VMware Tanzu Kubernetes Grid Integrated Edition (TKGI) )
            # Enter a valid option [1 to 3]:
            child.sendline(self.cloud_platform)
            self.logger.logger.info(f'Select the cloud platform to deploy: {self.cloud_platform}')
            print(f'Select the cloud platform to deploy: {self.cloud_platform}')

            # [NOTES] You can install the IBM Business Automation Insights deployment as either a private catalog (namespace scope) or the global catalog namespace (GCN). The private option uses the same target namespace of the IBM Business Automation Insights deployment, the GCN uses the openshift-marketplace namespace.
            # Do you want to deploy IBM Business Automation Insights using private catalog? (Yes/No, default: Yes):
            if self.global_catalog == 'yes':
                child.sendline('No')
                self.logger.logger.info('Do you want to deploy IBM Business Automation Insights using private catalog? (Yes/No, default: Yes): No')
                print('Do you want to deploy IBM Business Automation Insights using private catalog? (Yes/No, default: Yes): No')
            else:
                child.sendline('Yes')
                self.logger.logger.info('Do you want to deploy IBM Business Automation Insights using private catalog? (Yes/No, default: Yes): Yes')
                print('Do you want to deploy IBM Business Automation Insights using private catalog? (Yes/No, default: Yes): Yes')

            # [NOTES] IBM Business Automation Insights (BAI) deployment supports separation of operators and operands, the script can deploy BAI operator and BAI runtime pods in different projects.
            # Do you want to deploy IBM Business Automation Insights as separation of operators and operands? (Yes/No, default: No): 
            if (self.seprationduty_on.lower() == 'yes'):
                self.logger.logger.info(f'Do you want to deploy IBM Business Automation Insights as separation of operators and operands? (Yes/No, default: No):  Yes')
                print(f'Do you want to deploy IBM Business Automation Insights as separation of operators and operands? (Yes/No, default: No):  Yes')
                child.sendline('Yes')
            else:
                self.logger.logger.info(f'Do you want to deploy IBM Business Automation Insights as separation of operators and operands? (Yes/No, default: No):  No')
                print(f'Do you want to deploy IBM Business Automation Insights as separation of operators and operands? (Yes/No, default: No):  No')
                child.sendline('No')

            # Where do you want to deploy IBM Business Automation Insights?
            # Enter the name for a new project or an existing project (namespace):
            child.sendline(namespace)
            self.logger.logger.info(f'Entered namespace: {namespace}.')
            print(f'Entered namespace: {namespace}.')

            # Where (namespace) do you want to deploy BAI operands (i.e., runtime pods)?
            # Enter the name for a new project or an existing project (namespace):
            if (self.seprationduty_on.lower() == 'yes'):
                #Creating new namespace in case of separation of duties
                namespace = str(namespace) + self.operand_namespace_suffix
                self.project_name = namespace
                self.logger.logger.info(f'Separation of duties operand namespace: {namespace}.')
                print(f'Separation of duties operand namespace: {namespace}.')
                time.sleep(5)
                child.sendline(namespace)
                time.sleep(5)

            # This script prepares the OLM for the deployment of IBM Business Automation Insights capability 

            # Here are the existing users on this cluster: 
            #  1) Cluster Admin
            #  2) Testa1admin
            #  3) admin
            #  4) cp4admin
            #  5) dbauser
            #  6) environmentOwner
            #  7) group0001usr0001
            #  8) group0001usr0002
            #  9) rrServiceUser
            # 10) umsServiceUser
            # Enter an existing username in your cluster, valid option [1 to 10], non-admin is suggested:
            child.sendline(dbauser_number)
            self.logger.logger.info(f'Enter an existing username in your cluster, valid option [1 to 5], non-admin is suggested: {dbauser_number}')
            print(f'Enter an existing username in your cluster, valid option [1 to 5], non-admin is suggested: {dbauser_number}')

            # Do you have a IBM Business Automation Insights Entitlement Registry key (Yes/No, default: No): 
            child.sendline('Yes')

            # Enter your Entitlement Registry key:
            child.sendline(entitlement_key)
            self.logger.logger.info(f'Entitlement key used: {entitlement_key}')
            print(f'Entitlement key used: {entitlement_key}')
            #Logging the output
            child.expect(pexpect.EOF)
            print(child.before)
            self.logger.logger.info(f"cluster admin setup output {child.before}")

            # Check that operator status is ssucess or running state
            admin_status = super().validate_operator_installation()
            if not admin_status:
                self.logger.logger.error(f"Validation of the operator installation failed.")
                print(f"Validation of the operator installation failed.")
                return False

            #Switching the project name to operand namespace
            self.logger.logger.info(f'Changing new namespace from {self.project_name} to {namespace}.')
            print(f'Changing new namespace from {self.project_name} to {namespace}.')
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
    
    def run_bai_property(self):
        """
        Name: run_bai_property
        Desc: Run the bai-prerequisite.sh -m property and generate the property files
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """
        try:
            #Read config values
            configure_ldap = self.parser.get('PREREQUISITES', 'CONFIGURE_LDAP')
            deployment_profile = self.parser.get('PREREQUISITES', 'DEPLOYMENT_PROFILE')
            is_iam_admin_default = self.parser.get('PREREQUISITES', 'IS_IAM_ADMIN_DEFAULT')

            self.logger.logger.info('Running prerequisite scripts...')
            self.logger.logger.info(f'Ldap = {self.ldap} Project = {self.project_name}')
            self.logger.logger.info(f'Property script: {self.property_script}')
            print('Running prerequisite scripts...')
            print(f'Ldap = {self.ldap} Project = {self.project_name}')
            print(f'Property script: {self.property_script}')
            process = pexpect.spawn("bash  " + self.property_script + " -n " + self.project_name)
            self.logger.logger.info(f'Command running is {"bash  " + self.property_script}.')
            print(f'Command running is {"bash  " + self.property_script}.')

            # IMPORTANT: Review the IBM Business Automation Insights stand-alone license information here: 
            # https://www14.software.ibm.com/cgi-bin/weblap/lap.pl?li_formnum=L-PSZC-SHQFWS
            # Press any key to continue
            self.logger.logger.info(""" 
            IMPORTANT: Review the IBM Business Automation Insights stand-alone license information here: 
            https://www14.software.ibm.com/cgi-bin/weblap/lap.pl?li_formnum=L-PSZC-SHQFWS
            Press any key to continue
            """)
            print(""" 
            IMPORTANT: Review the IBM Business Automation Insights stand-alone license information here: 
            https://www14.software.ibm.com/cgi-bin/weblap/lap.pl?li_formnum=L-PSZC-SHQFWS
            Press any key to continue
            """)
            time.sleep(5)
            process.sendline()
            time.sleep(3)

            # Do you accept the IBM Business Automation Insights stand-alone license (Yes/No, default: No):
            self.logger.logger.info(f'Do you accept the IBM Business Automation Insights stand-alone license (Yes/No, default: No): {self.accept_license}')
            print(f'Do you accept the IBM Business Automation Insights stand-alone license (Yes/No, default: No): {self.accept_license}')
            process.sendline(self.accept_license)

            # Select the cloud platform to deploy: 
            # 1) RedHat OpenShift Kubernetes Service (ROKS) - Public Cloud
            # 2) Openshift Container Platform (OCP) - Private Cloud
            # Enter a valid option [1 to 2]: 

            #From 25.0.0
            # Select the cloud platform to deploy: 
            # 1) RedHat OpenShift Kubernetes Service (ROKS) - Public Cloud
            # 2) Openshift Container Platform (OCP) - Private Cloud
            # 3) Other ( Rancher Kubernetes Engine (RKE) / VMware Tanzu Kubernetes Grid Integrated Edition (TKGI) )
            # Enter a valid option [1 to 3]: 
            self.logger.logger.info(f'Select the cloud platform to deploy: {self.cloud_platform}')
            print(f'Select the cloud platform to deploy: {self.cloud_platform}')
            process.sendline(self.cloud_platform)

            # Do you want to configure an LDAP for this IBM Business Automation Insights stand-alone deployment? (Yes/No, default: Yes):
            self.logger.logger.info(f'Do you want to configure an LDAP for this IBM Business Automation Insights stand-alone deployment? (Yes/No, default: Yes): {configure_ldap}')
            print(f'Do you want to configure an LDAP for this IBM Business Automation Insights stand-alone deployment? (Yes/No, default: Yes): {configure_ldap}')
            process.sendline(configure_ldap)

            # For BAI stand-alone, if you select LDAP, then provide one ldap user here for onborading ZEN.
            # please enter one LDAP user for BAI stand-alone: 
            ldap_user = self.ldap_user(self.ldap)
            self.logger.logger.info(f'please enter one LDAP user for BAI stand-alone: {ldap_user}')
            print(f'please enter one LDAP user for BAI stand-alone: {ldap_user}')
            process.sendline(ldap_user)

            # What is the LDAP type that will be used for this deployment? 
            # 1) Microsoft Active Directory
            # 2) IBM Tivoli Directory Server / Security Directory Server
            # 3) Custom
            # Enter a valid option [1 to 3]:
            self.logger.logger.info(f'What is the LDAP type that will be used for this deployment?  {self.ldap_type_number}')
            print(f'What is the LDAP type that will be used for this deployment?  {self.ldap_type_number}')
            process.sendline(self.ldap_type_number)

            # To provision the persistent volumes and volume claims
            # please enter the file storage classname for medium storage(RWX): 
            # please enter the file storage classname for fast storage(RWX): 
            # please enter the block storage classname for Zen(RWO): 
            self.logger.logger.info(f'please enter the file storage classname for medium storage(RWX): {self.storage_name}')
            print(f'please enter the file storage classname for medium storage(RWX): {self.storage_name}')
            process.sendline(self.storage_name)
            self.logger.logger.info(f'please enter the file storage classname for fast storage(RWX):  {self.storage_name}')
            print(f'please enter the file storage classname for fast storage(RWX):  {self.storage_name}')
            process.sendline(self.storage_name)
            self.logger.logger.info(f'please enter the block storage classname for Zen(RWO):   {self.storage_name}')
            print(f'please enter the block storage classname for Zen(RWO):   {self.storage_name}')
            process.sendline(self.storage_name)

            # Please select the deployment profile (default: small).  Refer to the documentation in BAI stand-alone Knowledge Center for details on profile.
            # 1) small
            # 2) medium
            # 3) large
            # Enter a valid option [1 to 3]: 
            self.logger.logger.info(f'Please select the deployment profile (default: small) - {deployment_profile}')
            print(f'Please select the deployment profile (default: small) - {deployment_profile}')
            process.sendline(deployment_profile)

            # Do you want to use the default IAM admin user: [cpadmin] (Yes/No, default: Yes): 
            self.logger.logger.info(f'Do you want to use the default IAM admin user: [cpadmin] (Yes/No, default: Yes): {is_iam_admin_default}')
            print(f'Do you want to use the default IAM admin user: [cpadmin] (Yes/No, default: Yes): {is_iam_admin_default}')
            process.sendline(is_iam_admin_default)

            if '25.0' in self.branch:
                #From 25.0.0
                # Do you want to generate the network policy templates for this BAI stand-alone deployment? (Notes: Starting from 25.0.0, the BAI stand-alone operators no longer install network policies automatically. If you want the operators to generate network policies from a set of templates, select Yes. You can install the network policies by running a script after the BAI Deployment is installed. If you select No, then no network policies will be generated.) (Yes/No, default: No):
                self.logger.logger.info(f'Do you want to generate the network policy templates for this BAI stand-alone deployment? (Notes: Starting from 25.0.0, the BAI stand-alone operators no longer install network policies automatically. If you want the operators to generate network policies from a set of templates, select Yes. You can install the network policies by running a script after the BAI Deployment is installed. If you select No, then no network policies will be generated.) (Yes/No, default: No): Yes')
                print(f'Do you want to generate the network policy templates for this BAI stand-alone deployment? (Notes: Starting from 25.0.0, the BAI stand-alone operators no longer install network policies automatically. If you want the operators to generate network policies from a set of templates, select Yes. You can install the network policies by running a script after the BAI Deployment is installed. If you select No, then no network policies will be generated.) (Yes/No, default: No): Yes')
                process.sendline('Yes')
            else:
                # Do you want to restrict network egress to unknown external destination for this BAI stand-alone deployment? (Notes: BAI stand-alone 24.0.1 prevents all network egress to unknown destinations by default. You can either (1) enable all egress or (2) accept the new default and create network policies to allow your specific communication targets as documented in the knowledge center.) (Yes/No, default: Yes): 
                self.logger.logger.info(f'Do you want to restrict network egress to unknown external destination for this BAI stand-alone deployment? {self.egress}')
                print(f'Do you want to restrict network egress to unknown external destination for this BAI stand-alone deployment? {self.egress}')
                process.sendline(self.egress)

            # Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as IM metastore DB for this BAI deployment? (Notes: IM service can use an external Postgres DB to store IM data. If you select "Yes", IM service uses an external Postgres DB as IM metastore DB. If you select "No", IM service uses an embedded cloud native postgresql DB as IM metastore DB.) (Yes/No, default: No): 
            self.logger.logger.info(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as IM metastore DB for this BAI deployment? (Notes: IM service can use an external Postgres DB to store IM data. If you select "Yes", IM service uses an external Postgres DB as IM metastore DB. If you select "No", IM service uses an embedded cloud native postgresql DB as IM metastore DB.) (Yes/No, default: No): {self.external_db}')
            print(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as IM metastore DB for this BAI deployment? (Notes: IM service can use an external Postgres DB to store IM data. If you select "Yes", IM service uses an external Postgres DB as IM metastore DB. If you select "No", IM service uses an embedded cloud native postgresql DB as IM metastore DB.) (Yes/No, default: No): {self.external_db}')
            process.sendline(self.external_db)

            # Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as BTS metastore DB for this BAI deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If you select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If you select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No):
            self.logger.logger.info(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as BTS metastore DB for this BAI deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If you select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If you select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No): {self.external_db}')
            print(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as BTS metastore DB for this BAI deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If you select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If you select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No): {self.external_db}')
            process.sendline(self.external_db)

            # Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as BTS metastore DB for this BAI deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If you select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If you select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No):
            self.logger.logger.info(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as BTS metastore DB for this BAI deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If you select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If you select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No): {self.external_db}')
            print(f'Do you want to use an external Postgres DB [YOU NEED TO CREATE THIS POSTGRESQL DB BY YOURSELF FIRST BEFORE YOU APPLY THE BAI CUSTOM RESOURCE] as BTS metastore DB for this BAI deployment? (Notes: BTS service can use an external Postgres DB to store meta data. If you select "Yes", BTS service uses an external Postgres DB as BTS metastore DB. If you select "No", BTS service uses an embedded cloud native postgresql DB as BTS metastore DB ) (Yes/No, default: No): {self.external_db}')
            process.sendline(self.external_db)

            # Which are the components you want to enable the Flink job for: 
            # 1) BAW 
            # 2) BAW Advanced events 
            # 3) ICM 
            # 4) ODM 
            # 5) Content 
            # 6) ADS 
            # 7) Navigator 
            # Tips:Press [ENTER] to accept the default (None of the components is selected)
            # Enter a valid option [1 to 7]: 
            self.logger.logger.info(f'Enabling fink jobs - 1, 2, 3, 4, 5, 6, 7')
            print(f'Enabling fink jobs - 1, 2, 3, 4, 5, 6, 7')
            process.sendline('1')
            process.sendline('2')
            process.sendline('3')
            process.sendline('4')
            process.sendline('5')
            process.sendline('6')
            process.sendline('7')
            process.sendline()

            pattern = re.compile(r'.*' + re.escape('Created all property files for BAI stand-alone') + r'.*')
            process.expect(pattern, timeout=120)

            property_setup_output = (process.before).decode('utf-8')
            self.logger.logger.info(f'property setup output :  {property_setup_output}')
            print(f'property setup output :  {property_setup_output}')

            property_setup_after = (process.after).decode('utf-8')
            self.logger.logger.info(f'property setup after :  {property_setup_after}')
            print(f'property setup after :  {property_setup_after}')

            process.expect(pexpect.EOF)

            property_setup_output = (process.before).decode('utf-8')
            self.logger.logger.info(f'property setup output :  {property_setup_output}')
            print(f'property setup output :  {property_setup_output}')

            self.logger.logger.info(f"Created the property files for ldap {self.ldap} in the project {self.project_name}")
            print(f"Created the property files for ldap {self.ldap} in the project {self.project_name}")
            return True
        
        except Exception as e:
            self.logger.logger.error(f"Error while running bai-prerequisite.sh -m property: {str(e)}")
            print((f"Error while running bai-prerequisite.sh -m property: {str(e)}"))
            return False
    
    def update_property_files(self):
        try:
            # Copy certificates to the ldap folders
            copy_cert_status = self.copy_bai_certs()
            if not copy_cert_status:
                self.logger.logger.error("Error copying the certificates")
                print("Error copying the certificates")
                return False

            # Copy certificates to the ldap folders
            property_update_status = self.bai_property_update()
            if not property_update_status:
                self.logger.logger.error('Failed to update the property files')
                print('Failed to update the property files')
                return False

            return True
        except Exception as e:
            self.logger.logger.error(f"Error during property file updation: {str(e)}")
            print(f"Error during property file updation: {str(e)}")
            return False
        
    def ldap_user(self, ldap):
        """
        Name: ldap_user
        Author: Dhanesh
        Desc: To get the user name of the ldap selected.
        Parameters:
            ldap (string ): ldap type selected
        Returns:
            ldap_user: The ldap username
        """
        if ldap == 'msad':
            ldap_user = self.parser.get('PREREQUISITES', 'MSAD_LDAP_USER')
        elif ldap == 'sds':
            ldap_user = self.parser.get('PREREQUISITES', 'SDS_LDAP_USER')
        else:
            raise ValueError(f'Invalid ldap type: {ldap}')
        return ldap_user
    
    def copy_bai_certs(self):
        """
        Name: copy_bai_certs
        Author: Dhanesh
        Desc: function to copy certificates (ldap) to the certificate folder
        Parameters:
            None
        Returns:
            Boolean: True/False
        """
        try:
            #Copy ldap certs
            present_dir = os.getcwd()
            self.logger.logger.info("Coping the LDAP certificates...")
            print("Coping the LDAP certificates...")
            print(f'Property file path: {self.property_folder}')
            src_dir = present_dir +'/certs/' + self.ldap + '/*'
            dest_dir = self.property_folder  +'cert/ldap/'
            print(f'Cert destination folder: {dest_dir}')
            os.system('cp -rf '+ src_dir + ' ' + dest_dir)

            # Copying the postgres certificates to bts/zen/im folders
            if self.external_db.lower() == 'yes':
                self.logger.logger.info("Coping the postgres certificates to bts/zen/im folders.")
                print("Coping the postgres certificates to bts/zen/im folders.")
                src_dir = present_dir + '/certs/postgres/*'

                self.logger.logger.info("Coping the postgres certificates to BTS folders.")
                print("Coping the postgres certificates to BTS folders.")
                dest_dir = self.property_folder + 'cert/bts_external_db/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

                self.logger.logger.info("Coping the postgres certificates to ZEN folders.")
                print("Coping the postgres certificates to ZEN folders.")
                dest_dir = self.property_folder + 'cert/zen_external_db/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

                self.logger.logger.info("Coping the postgres certificates to IM folders.")
                print("Coping the postgres certificates to IM folders.")
                dest_dir = self.property_folder + 'cert/im_external_db/'
                os.system('cp -rf '+ src_dir + ' ' + dest_dir)

            self.logger.logger.info("Coping of LDAP certificates is done successfully.")
            return True
        except Exception as e:
            self.logger.logger.error(f"Error: {str(e)}")
            return False
    
    def bai_property_update(self):
        """
        Name: bai_property_update
        Author: Dhanesh
        Desc: function to update property files
        Parameters:
            None
        Returns:
            Boolean: True/False
        """
        try:
            #Updating the ldap property file
            self.logger.logger.info("Updating the bai_LDAP.property...")
            print("Updating the bai_LDAP.property...")
            ldap_data = ''
            ldap_data = '_' + self.ldap
            ldap_data = ldap_data.upper()
            config = CustomConfigObj(self.property_folder + "bai_LDAP.property")
            splitter = "_"
            ldap_property = super().updater(config, splitter, ldap_data)
            if not ldap_property:
                self.logger.logger.error(f"Updating property file {self.property_folder}bai_LDAP.property failed.")
                print(f"Updating property file {self.property_folder}bai_LDAP.property failed.")
                return False

            #Updating the user profile property file
            self.logger.logger.info("Updating the bai_user_profile.property")
            print('Updating the bai_user_profile.property')
            config = CustomConfigObj(self.property_folder + "bai_user_profile.property")
            splitter = "."
            user_profile = self.bai_updater(config, splitter)
            if not user_profile:
                self.logger.logger.error(f"Updating property file {self.property_folder}bai_user_profile.property failed.")
                return False

            self.logger.logger.info(f"All the property files are updated successfully.")
            return True
        except Exception as e:
            self.logger.logger.error(f"Error: {str(e)}")
            return False
    
    def bai_updater(self, config, splitter):
        """
        Function name: bai_updater
        Author: Dhanesh
        Params: 
            config: property file details
            splitter: By which we are splitting and creating the key
            ldap: LDAP values we are passing as a parameter
        Return:
            None
        """
        try:
            #Going over the configuration items and replacing with new values from data config
            for key, value in config.items():
                section = key.split(splitter)[0]
                pro_key = key
                if self.parser.has_option(section, key): 
                    if key.lower() in ['bai.im_external_postgres_database_name', 'bai.bts_external_postgres_database_name', 'bai.zen_external_postgres_database_name']:
                        print(key , self.parser.get(section, key).strip('"') + fetch_host_shortname())
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

    def validate_generate(self):
        """
        Name: validate_generate
        Author: Dhanesh
        Desc: Validate the generated property files
        Parameters:
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        file_list = [self.property_folder+'bai_user_profile.property', self.property_folder+'bai_LDAP.property']
        self.logger.logger.info(f'Property files are {str(file_list)}')
        print(f'Property files are {str(file_list)}')
        for file in file_list:
            file_path = Path(file)
            self.logger.logger.info(f'Property file path: {file_path}')
            print(f'Property file path: {file_path}')
            if not file_path.is_file():
                return False
        return True 
    
    def run_bai_generate(self):
        """
        Name: run_bai_generate
        Author: Dhanesh
        Desc: Running the bai-prerequisites.sh -m generate to create the create_secret.sh
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """
        try:
            super().switch_namespace()

            # Start the shell script process
            script = self.script_folder + "bai-prerequisites.sh -m generate -n " + self.project_name
            self.logger.logger.info(f'Running the script {script}')
            print(f'Running the script {script}')
            process = pexpect.spawn("bash  " + script)
            process.sendline('')
            pattern = re.compile(r'.*' + re.escape('bai-prerequisites.sh -m validate') + r'.*')
            process.expect(pattern, timeout=240)
            generate_op = process.before.decode('utf-8')
            self.logger.logger.info(f'{script} output :\n {generate_op}')
            print(f'{script} output :\n {generate_op}')
            time.sleep(10)
            return True
        
        except Exception as e:
            self.logger.logger.info(f"Running {script} failed with error as {e} ")
            print(f"Running {script} failed with error as {e} ")
            return False
        
    def create_secret(self):
        """
        Name: create_secret
        Author: Dhanesh
        Desc: Creating the secrets using the script
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        try:
            # Creating the secrets
            self.logger.logger.info(f'Creating the secrets using {self.prereq_folder + "create_secret.sh"} file')
            print(f'Creating the secrets using {self.prereq_folder + "create_secret.sh"} file')
            script = self.prereq_folder + "create_secret.sh"
            if os.path.exists(script):
                print(f'File {script} generated successfully')
            else:
                print(f'File {script} is not generated.')
            status, respo = super().valiate_cluster_component(script)
            if status:
                if 'failed' in respo.lower():
                    self.logger.logger.info(f"Secret creation failed... ")
                    return False
            else:
                self.logger.logger.info(f"Secret creation failed... ")
                return False

            secrets_status = super().validate_createdsecrets(2)
            if not secrets_status:
                print("Secret validation failed... ")
                self.logger.logger.info(f"Secret validation failed... ")
                return False
            return True
        except Exception as e:
            self.logger.logger.info(f"Creation of the secret is failed with error as {e} ")
            print(f"Creation of the secret is failed with error as {e} ")
            return False
    
    def bai_validation(self):
        """
        Name: bai_validation
        Author: Dhanesh
        Desc: Run bai-prerequisites.sh -m validate
        Parameters:
            None
        Returns:
            Boolean: True/False
        Raises:
            ValueError: If the return value is False.
        """

        # Get the list of secrets with namespace and opaque type
        super().switch_namespace()
        script = self.script_folder + "bai-prerequisites.sh"
        get_validation = [script,  '-m',  'validate', '-n', self.project_name]
        self.logger.logger.info(f'Running validation:  {str(get_validation)}')
        try:
            result = subprocess.run(get_validation, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.logger.debug(result)
            validation = result.stdout.decode()
            self.logger.logger.critical(validation)
            print(validation)
            if "FAILED" in validation:
                self.logger.logger.critical(f'Validation {get_validation} failed')
                print(f'Validation {get_validation} failed')
                return False
            return True
        except subprocess.CalledProcessError as e:
            self.logger.logger.error(f"Validation Failed. Error: {e.stderr.decode()}")
            print(f"Validation Failed. Error: {e.stderr.decode()}")
            return False
    
    def run_bai_deployment(self):
        """
        Name: run_bai_deployment
        Author: Dhanesh
        Desc: Run the bai_deployment.sh and generate the CR file.
        Parameters:
            None
        Returns:
            Boolean : True/False
        Raises:
            Exception: If the return value is False.
        """
        try:
            self.logger.logger.info(f'Starting the Deployment: project {self.project_name} , ldap {self.ldap}, branch {self.branch} {self.stage_prod}.')
            print(f'Starting the Deployment: project {self.project_name} , ldap {self.ldap}, branch {self.branch} {self.stage_prod}.')

            # Start the shell script process
            self.logger.logger.info(f'Running the script {self.script_folder}  bai-deployment.sh {self.stage_prod} -n   {self.project_name}')
            print(f'Running the script {self.script_folder}  bai-deployment.sh {self.stage_prod} -n   {self.project_name}')
            process = pexpect.spawn("bash  " + self.script_folder  + "bai-deployment.sh " + self.stage_prod +" -n " + self.project_name)
            time.sleep(10)

            # IMPORTANT: Review the IBM Business Automation Insights standalone license information here: 
            # https://www.ibm.com/support/customer/csol/terms/?id=L-YZSW-9CAE3A
            # Press any key to continue
            self.logger.logger.info('Press any key to continue')
            print('Press any key to continue')
            process.sendline()
            time.sleep(2)

            # Do you accept the IBM Business Automation Insights standalone license (Yes/No, default: No): 
            self.logger.logger.info(f'Do you accept the IBM Business Automation Insights standalone license (Yes/No, default: No): {self.accept_license}')
            print(f'Do you accept the IBM Business Automation Insights standalone license (Yes/No, default: No): {self.accept_license}')
            process.sendline('Yes')
            time.sleep(2)

            if self.branch == '24.0.0' or self.branch == '24.0.0-IF001' or self.branch == '24.0.0-IF002' or self.branch == '24.0.1':
                # Where do you want to deploy IBM Business Automation Insights standalone?
                # Enter the name for an existing project (namespace):
                self.logger.logger.info(f'Where do you want to deploy Cloud Pak for Business Automation?: {self.project_name}')
                print(f'Where do you want to deploy Cloud Pak for Business Automation?: {self.project_name}')
                process.sendline(self.project_name)
                time.sleep(2)

            if not self.branch.startswith("25.0"):
                # Do you want to restrict network egress to unknown external destination for this BAI stand-alone deployment? (Notes: BAI stand-alone 24.0.1 prevents all network egress to unknown destinations by default. You can either (1) enable all egress or (2) accept the new default and create network policies to allow your specific communication targets as documented in the knowledge center.) (Yes/No, default: Yes): 
                self.logger.logger.info(f'Do you want to restrict network egress to unknown external destination for this BAI stand-alone deployment? {self.egress}')
                print(f'Do you want to restrict network egress to unknown external destination for this BAI stand-alone deployment? {self.egress}')
                process.sendline(self.egress)

            # Verify that the information above is correct.
            # To proceed with the deployment, enter "Yes".
            # To make changes, enter "No" (default: No): 
            self.logger.logger.info(f'To proceed with the deployment, enter Yes: Yes')
            print(f'To proceed with the deployment, enter Yes: Yes')
            process.sendline('Yes')

            #Comparing the o/p with expect
            if self.branch == '24.0.0-IF001' or self.branch == '24.0.0':
                cr_pattern = re.compile(r'.*' + re.escape("Applied value in property file into final CR") + r'.*')
            else:
                cr_pattern = re.compile(r'.*' + re.escape("All values in the property file have been applied in the final CR") + r'.*')
            process.expect(cr_pattern, timeout=120)
            output = process.before.decode('utf-8')
            self.logger.logger.info(f"Creating Custom Resource file \n {output}")
            print(f"Creating Custom Resource file \n {output}")
            process.expect(['#', pexpect.EOF], timeout=120)
            output = process.before.decode('utf-8')
            self.logger.logger.info(output)
            print(output)

            #verify CR file created successfully
            cr_path = self.generatedcr_folder + 'ibm_bai_cr_final.yaml'
            if os.path.exists(cr_path):
                self.logger.logger.info(f'File {cr_path} generated successfully')
                print(f'File {cr_path} generated successfully')
            else:
                self.logger.logger.info(f'File {cr_path} is not generated.')
                print(f'File {cr_path} is not generated.')
                return False
            return True

        except Exception as e:
            self.logger.logger.error(f'Running deployment.sh failed: {e}')
            print(f'Running deployment.sh failed: {e}')
            return False
    
    def apply_bai_cr(self):
        """
        Name: apply_cr
        Author: Dhanesh
        Desc: To apply the custom resource file generated
        Parameters:
            None
        Returns:
            Boolean : True/False
        Raises:
            Exception: If the return value is False.
        """
        super().switch_namespace()
        apply_yaml = self.apply_yaml(self.generatedcr_folder + 'ibm_bai_cr_final.yaml')
        if not apply_yaml:
            self.logger.logger.info(f'Applying generate CR failed with error')
            print(f'Applying generated CR failed with error')
            return False
        return True
    
    def validate_deployment(self):
        """
        Name: validate_deployment
        Author: Dhanesh
        Desc: Validating if the CR applied correctly.
        Raises:
            ValueError: If the return value is False. 
        """
        try:
            # Run oc get content command
            get_content_command = ['oc', 'get', 'insightsEngine', '-n', self.project_name]
            result = subprocess.run(get_content_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(result.stdout.decode())

            # Check the output to determine if content is present
            if result.stdout.decode() == '':
                print("CR instance bai is not present in insightsEngine.")
                return False
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error running oc get content command: {e}")
            print("Deployment creation failed.")
            return False
    
    def bai_pathupdate_dataconfig(self):
        """
        Name: pathupdate_dataconfig
        Author: Dhanesh
        Desc: To find and replace the project property folder for 24.00 ifix onwards. From ifix onwards project folder structure is changed
        Params:
           self
        Returns:
            Boolean: True/False
        """

        try:
            result = True
            print(self.branch)
            if self.branch != '24.0.0' and self.branch != '24.0.0-IF001' and self.branch != '24.0.0-IF002' and self.branch != '24.0.1':

                #Taking the operand namespace  to set the path name
                if self.seprationduty_on == 'yes':
                    self.project_name = str(self.project_name) + str(self.operand_namespace_suffix)
                    self.logger.logger.info(f"New project name is {self.project_name}")

                #Replace the property file folder path
                current_dir = os.getcwd()
                dataconfig_path = current_dir + '/config/bai_data.config'
                replace_from = 'bai-prerequisites/propertyfile'
                replace_with = f'bai-prerequisites/project/{self.project_name}/propertyfile'
                cmd = ["sed", "-i", f"s;{replace_from};{replace_with};g", dataconfig_path]
                self.logger.logger.info(f"Replace the path from {replace_from} to {replace_with}  using the command {str(cmd)} and dataconfig_path is {dataconfig_path} ")
                result = self.run_command(cmd)
                if not result:
                    return result


                #Replace the prereq folder path with project name if exsists
                replace_from = 'PREREQ_FOLDER=/opt/ibm-bai-automation/scripts/bai-prerequisites/'
                replace_with = f'PREREQ_FOLDER=/opt/ibm-bai-automation/scripts/bai-prerequisites/project/{self.project_name}/'
                cmd = ["sed", "-i", f"s;{replace_from};{replace_with};g", dataconfig_path]
                self.logger.logger.info(f"Replace the path from {replace_from} to {replace_with}  using the command {str(cmd)} and dataconfig_path is {dataconfig_path} ")
                result = self.run_command(cmd)
                if not result:
                    return result

                #Generated CR path update
                replace_from = 'GENERATED_CR=/opt/ibm-bai-automation/scripts/generated-cr/'
                replace_with = f'GENERATED_CR=/opt/ibm-bai-automation/scripts/generated-cr/project/{self.project_name}/'
                cmd = ["sed", "-i", f"s;{replace_from};{replace_with};g", dataconfig_path]
                self.logger.logger.info(f"Replace the path from {replace_from} to {replace_with}  using the command {str(cmd)} and dataconfig_path is {dataconfig_path} ")
                result = self.run_command(cmd)
                if not result:
                    return result

                self.logger.logger.info(f"Succesfully run the pathupdate_dataconfig with branch {str(self.branch)} and namespace is {self.project_name}.")
            return result
        except:
            self.logger.logger.error(f"Failed to run the pathupdate_dataconfig with branch {str(self.branch)} and namespace is {self.project_name}.")
            return False
        
    def sent_data_to_event_stream(self, fncm_version):
        """
            Name: sent_data_to_event_stream
            Author: Dhanesh
            Desc: Sent data to the Ansible automation platform event stream 
            Parameters:
                None
            Returns:
                None
            Raises:
                Exception
        """
        url = self.parser.get('FNCM_ANISBLE_PLATFORM', 'url')
        username = self.parser.get('FNCM_ANISBLE_PLATFORM', 'username')
        password = self.parser.get('FNCM_ANISBLE_PLATFORM', 'password')
        try:
            cur_dir = os.getcwd()
            configmap_path = cur_dir + '/config/bai_kafka_info.txt'
            secret_path = cur_dir + '/config/bai_kafka_secret.yaml'
            is_svl_machine = svl_machine(self.cluster_name)
            if is_svl_machine:
                site = "SVL"
            else:
                site = "RTP"
            
            #Getting build, ifix version and ldap
            build, ifix_version = self.extract_build_and_ifix(self.branch)
            ldap = self.ldap.upper()

            # Reading data from the bai_kafka_info.txt
            try:
                #Getting the cluster details.
                cluster_details = {
                    "namespace": self.project_name,
                    "build": build,
                    "ifixVersion": ifix_version,
                    "ldap": ldap,
                    "clusterName": self.cluster_name,
                    "clusterPassword": self.cluster_pass,
                    "site": site,
                    "fncm_version": fncm_version
                }
                
                # Reading text data and YAML data from the file and converting it into a JSON dictionary
                print('Reading the data from bai_kafka_info.txt and ai_kafka_secret.yaml...')
                self.logger.logger.info('Reading the data from bai_kafka_info.txt and bai_kafka_secret.yaml...')
                with open(configmap_path, 'r') as txt_file, open(secret_path, 'r') as yaml_file:
                    text_data = txt_file.read().replace("'", '"')
                    text_data_dict = json.loads(text_data)
                    yaml_data_dict = yaml.safe_load(yaml_file)                 
                
                # Convert the combined data to JSON format
                combined_data = [cluster_details ,text_data_dict, yaml_data_dict]
                combined_json_data = json.dumps(combined_data, indent=4)
                print(f'The combined json data: \n {combined_json_data}')
                self.logger.logger.info(f'The combined json data: \n {combined_json_data}')

            except FileNotFoundError as e: 
                self.logger.logger.info(f'File not found: - {e}')
                raise FileNotFoundError(f'File not found: - {e}')
            except json.JSONDecodeError as e:
                self.logger.logger.info(f'Error parsing JSON: {e}')
                raise Exception(f'Error parsing JSON: {e}')
            except PermissionError as e:
                self.logger.logger.info(f'Permission denied to read file: - {e}')
                raise PermissionError(f'Permission denied to read file: - {e}')
            except Exception as err:
                self.logger.logger.info(f'Error reading file: {err}')
                raise Exception(f'Error reading file: {err}')

            # Authentication and send post request with the kakfa data read from the text file saved
            auth = HTTPBasicAuth(username, password)
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
            url,
            auth=auth,
            headers=headers,
            verify=False,
            data=combined_json_data,
            )
            status_code = response.status_code
            print(f'Response status code: {status_code}')
            self.logger.logger.info(f'Response status code: {status_code}')

            # Check response status code for kafka request
            if status_code == 200:
                print(f'Request sent successful!.. \n {response.text}')
                self.logger.logger.info(f'Request sent successful!.. \n {response.text}')
            else:
                self.logger.logger.info(f'Request failed with status code: {response.status_code} \n {response.text}')
                raise Exception(f'Request failed with status code: {response.status_code} \n {response.text}')
                
        except requests.exceptions.HTTPError as http_err:
            self.logger.logger.info(f'HTTP error occurred: {http_err}')
            raise Exception(f'HTTP error occurred: {http_err}')
        except requests.exceptions.ConnectionError as conn_err:
            self.logger.logger.info(f'Connection error occurred: {conn_err}')
            raise ConnectionError(f'Connection error occurred: {conn_err}')
        except requests.exceptions.Timeout as timeout_err:
            self.logger.logger.info(f'Timeout error occurred: {timeout_err}')
            raise TimeoutError(f'Timeout error occurred: {timeout_err}')
        except requests.exceptions.RequestException as err:
            self.logger.logger.info(f'Request exception occurred: {err}')
            raise Exception(f'Request exception occurred: {err}')
    
    def run_oc_command(self, oc_command):
        """
            Name: run_oc_command
            Author: Dhanesh
            Desc: Common function to run the oc commands
            Parameters:
                oc_command(string): The oc command to run
            Returns:
                result: oc command execution output
                False: if the oc command execution fails
            Raises:
                none
        """
        try:
            #Execute oc comands 
            self.logger.logger.info(f'Executing oc command: {oc_command}')
            result = subprocess.run(oc_command, shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.logger.info(f"oc command {oc_command} output: \n{result.stdout.decode('utf-8')}")
            print(f"oc command {oc_command} output: \n{result.stdout.decode('utf-8')}")

            #check if the oc command executed successfully
            if result.returncode == 0:

                #verify errors are present in the output
                if result.stderr:
                    print(f"Error: {result.stderr.decode('utf-8')}")
                    self.logger.logger.info(f"Error: {result.stderr.decode('utf-8')}")
                    return False
                else:
                    print(f"oc command {oc_command} executed successfully")
                    self.logger.logger.info(f"oc command {oc_command} executed successfully")
                    if not result.stdout.decode('utf-8').strip():
                        return True
                    else:
                        return result.stdout.decode('utf-8').strip()
            else:
                print(f"oc command {oc_command} execution was unsuccessful")
                self.logger.logger.info(f"oc command {oc_command} execution was unsuccessful")
                self.logger.logger.info(f"oc command  returned an error: \n{result.stderr.decode('utf-8')}")
                print(f"oc command returned an error: \n{result.stderr.decode('utf-8')}")
                return False
            
        except subprocess.CalledProcessError as e:
            self.logger.logger.info(f"Error: {result.stderr.decode('utf-8')}")
            print(f"Error: {result.stderr.decode('utf-8')}")
            self.logger.logger.info(f"Error: Script returned an error for {oc_command}: {e}")
            print(f"Error: Script returned an error for {oc_command}: {e}")
            return False
        except Exception as e:
            print(f"Error: Unable to execute the oc oc_command {oc_command}: {e}")
            self.logger.logger.info(f"Error: Unable to execute the oc oc_command {oc_command}:  {e}")
            return False

    def get_config_map(self):
        """
            Name: get_config_map
            Author: Dhanesh
            Desc: Get the config map from the BAI deployment and save it in a txt file.
            Parameters:
                None
            Returns:
                None
            Raises:
                none
        """
        try:
            # Getting the configmap and saving to /config
            cur_dir = os.getcwd()
            get_configmap_cmd = "kubectl get configmap/ibm-bai-foundation-shared-info -o jsonpath='{.data.bai_kafka_configuration}'"
            get_configmap_cmd += f' -n {self.project_name}'
            get_configmap_cmd += f' > {cur_dir}/config/bai_kafka_info.txt'
            output = self.run_oc_command(get_configmap_cmd)
            if not output:
                self.logger.logger.info(f'Failed to get the configmap from BAI deployment.')
                raise ValueError(f'Failed to get the configmap from BAI deployment.')
            else:
                print('Configmap from BAI depoyment retreved successfully')
                self.logger.logger.info('Configmap from BAI depoyment retreved successfully.')

                # Verifying the file saved successfully
                time.sleep(1)
                if os.path.exists(f'{cur_dir}/config/bai_kafka_info.txt'):
                    self.logger.logger.info(f'Configmap file saved successfuly in {cur_dir}/config/bai_kafka_info.txt')
                    print(f'Configmap file saved successfuly in {cur_dir}/config/bai_kafka_info.txt')
                else:
                    self.logger.logger.info(f'Configmap file is not present in {cur_dir}/config/bai_kafka_info.txt')
                    raise FileNotFoundError(f'Configmap file is not present in {cur_dir}/config/bai_kafka_info.txt')
        except Exception as e:
            print(f'Error occured getting the configmap from the BAI deployment: {e}')
            self.logger.logger.info(f'Error occured getting the configmap from the BAI deployment: {e}')

    def get_kafka_secret(self):
        """
            Name: get_kafka_secret
            Author: Dhanesh
            Desc: Get the secret from the BAI deployment and save it in a yaml file.
            Parameters:
                None
            Returns:
                None
            Raises:
                none
        """
        try:
            # Getting the configmap and saving to /config
            cur_dir = os.getcwd()
            get_secret_cmd = "kubectl get secret/kafka-iaf-connection-secret -o yaml"
            get_secret_cmd += f' -n {self.project_name}'
            get_secret_cmd += f' > {cur_dir}/config/bai_kafka_secret.yaml'
            output = self.run_oc_command(get_secret_cmd)
            if not output:
                self.logger.logger.info(f'Failed to get the kafka-iaf-connection-secret from BAI deployment.')
                raise ValueError(f'Failed to get the kafka-iaf-connection-secret from BAI deployment.')
            else:
                print('kafka-iaf-connection-secret from BAI depoyment retreved successfully')
                self.logger.logger.info('kafka-iaf-connection-secret from BAI depoyment retreved successfully.')

                # Verifying the file saved successfully
                time.sleep(2)
                if os.path.exists(f'{cur_dir}/config/bai_kafka_secret.yaml'):
                    self.logger.logger.info(f'kafka-iaf-connection-secret file saved successfuly in {cur_dir}/config/bai_kafka_secret.yaml')
                    print(f'kafka-iaf-connection-secret file saved successfuly in {cur_dir}/config/bai_kafka_secret.yaml')
                else:
                    self.logger.logger.info(f'kafka-iaf-connection-secret file is not present in {cur_dir}/config/bai_kafka_secret.yaml')
                    raise FileNotFoundError(f'kafka-iaf-connection-secret file is not present in {cur_dir}/config/bai_kafka_secret.yaml')
        except Exception as e:
            print(f'Error occured getting the kafka-iaf-connection-secret from the BAI deployment: {e}')
            self.logger.logger.info(f'Error occured getting the kafka-iaf-connection-secret from the BAI deployment: {e}')
    
    def extract_build_and_ifix(self, branch):
        """
            Name: extract_build_and_ifix
            Author: Dhanesh
            Desc: Extract the 
            Parameters:
                None
            Returns:
                build and ifix
            Raises:
                none
        """
        try:
            # Split the string by '-'
            print(f'branch: {branch}')
            parts = branch.split('-')
            print(f'Splitted parts: {parts}')
            if len(parts) != 2 or not parts[1].startswith("IF"):
                print("Input format is X.Y.Z")
                return branch, 'IFix 0'
            
            # Extract the build version
            build = parts[0]
            print(f'Build: {build}')
            
            # Extract the IFix version number and convert it to an integer to remove leading zeros
            ifixversion = str(int(parts[1][2:]))  # Remove the 'IF' prefix and convert to int
            print(f'Ifix version: {ifixversion}')
            return build, f"IFix {ifixversion}"
        except (ValueError, IndexError) as e:
            raise Exception(f"Error: {e}")


