import json
import os
import sys
import configparser

from tomlkit import parse, dumps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from component_sanity_tests.exceptions.sanity_exception import SanityTestException
from utils.get_cr_config import get_db_ldap
import utils.login as login
import utils.oc_version as oc_version
from  utils.logger import logger

class PrepareConfiguration():
    def __init__(self, initial_config_file, config_file):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the PrepareConfiguration class
        Parameters:
            config_file: Path to the configuration file
        Returns:
            None
        """
        self.config_file = config_file
        self.initial_config_file = initial_config_file

    def prepare_config_file(self):
        """
        Method name     :    prepare_config_file
        Author          :    Anisha Suresh (anisha-suresh@ibm.com)
        Description     :    Prepares the configuration file
        Parameters      :    None
        Returns         :    None
        """
        try:
            logger.info("==========================================Starting execution of input_data.py==========================================")
            # Reading config.toml file
            logger.info("Reading config.toml file into input_data variable ...")
            try : 
                with open(self.config_file, "r") as file : 
                    input_data = parse(file.read())
            except Exception as e :
                logger.critical(f"An exception occured during reading the toml file : {e}")
                raise SanityTestException(f"Failed to read the toml file") from e 

            # Configurations from config.ini
            logger.info("Reading configurations from config.ini file")
            config = configparser.ConfigParser()
            config.read(self.initial_config_file)
            project_name = config.get('configurations', 'project_name')
            build = config.get('configurations', 'build')
            ifix_version = config.get('configurations', 'ifix_version')
            cluster = config.get('configurations', 'cluster')
            deployment_type = config.get('configurations', 'deployment_type')
            DB,LDAP = get_db_ldap(deployment_type,build)
            ier_sanity = config.get('configurations','ier_sanity')
            cpe_sanity = config.get('configurations','cpe_sanity')
            iccsap_sanity = config.get('configurations','iccsap_sanity')

            #fetching OCP version
            ocp_version = oc_version.fetch_oc_version()
            logger.info("Fetched OCP version.")

            # configurations
            logger.info("Setting configurations")
            input_data['configurations']['project_name'] = project_name
            input_data['configurations']['build'] = build
            input_data['configurations']['ifix_version'] = ifix_version
            input_data['configurations']['cluster'] = cluster
            input_data['configurations']['deployment_type'] = deployment_type
            input_data['configurations']['DB'] = DB
            input_data['configurations']['LDAP'] = LDAP
            input_data['configurations']['ocp_version'] = ocp_version
            input_data['configurations']['ier_sanity'] = ier_sanity
            input_data['configurations']['iccsap_sanity'] = iccsap_sanity

            # paths
            base_path = os.getcwd() #Expected location is ../Cp4ba-Automation/CP4BA_Package/
            cluster_file = os.path.join(base_path, 'clusters.json')

            EXPECTED_DIR = os.path.normpath("/Cp4ba-Automation/CP4BA_Package/")
            if EXPECTED_DIR not in (os.path.normpath(base_path)) :
                logger.error("This script is not executed from the expected base directory.")
                logger.error(f"Current directory : {base_path}")
                logger.error(f"Expected directory : {EXPECTED_DIR}")
                logger.critical("Exiting BVT execution!!!")
                exit()
            else:
                logger.info(f"Running from directory : {base_path}")

            f = open(f'{cluster_file}')
            cluster_data = json.load(f)
            cluster_found = 0
            for i in cluster_data :
                if str(i).lower() == cluster.lower() :
                    cluster_found = 1
                    infra_node_pwd = cluster_data[i]['root_pwd']
                    kube_Admin_password = cluster_data[i]['kube_pwd']
            if cluster_found == 0 :
                logger.error("Add cluster details to cluster.json file!")
                logger.critical("Exiting BVT execution!!")
                exit()

            credentials = login.get_credentials(project_name)
            username, password = credentials.get("appLoginUsername"), credentials.get("appLoginPassword")
            logger.info(f"Applogin credentials used : {username}/{password}")

            # credentials
            logger.info("Setting credentials")
            input_data['credentials']['infra_node_uname'] = 'root'
            input_data['credentials']['infra_node_pwd'] = infra_node_pwd
            input_data['credentials']['kube_admin_username'] = 'kubeadmin'
            input_data['credentials']['kube_admin_password'] = kube_Admin_password
            input_data['credentials']['app_login_username'] = username
            input_data['credentials']['app_login_password'] = password

            # paths
            logger.info("Setting paths")
            input_data['paths']['base_path'] = base_path
            input_data['paths']['cluster_file'] = cluster_file

             # ocp paths
            ocp = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/operators.coreos.com~v1alpha1~ClusterServiceVersion'
            config_maps = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/core~v1~ConfigMap?orderBy=desc&sortBy=Created'
            secrets = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/secrets/secret_name'

            #ocp_paths
            logger.info("Setting ocp_paths")
            input_data['ocp_paths']['ocp'] = ocp
            input_data['ocp_paths']['config_maps'] = config_maps
            input_data['ocp_paths']['secrets'] = secrets

            # ICCSAP Sanity Tests
            if iccsap_sanity:
                iccsap_reports_folder = os.path.join(base_path, 'component_sanity_tests', 'reports', 'iccsap')
                iccsap_screenshot_path = os.path.join(iccsap_reports_folder, 'screenshots')
                iccsap_generated_reports_path = os.path.join(iccsap_reports_folder,'generated_reports')
                iccsap_report_path = os.path.join(iccsap_generated_reports_path, 'iccsap_sanity_tests_report.html')
                iccsap_report_template_path = os.path.join(iccsap_reports_folder, 'templates', 'iccsap_template.html')
                iccsap_resources_folder = os.path.join(base_path, 'component_sanity_tests', 'resources', 'iccsap')
                iccsap_downloads_folder = os.path.join(base_path, 'component_sanity_tests', 'downloads', 'iccsap')

                logger.info("Setting configurations for ICCSAP sanity tests")
                input_data['iccsap']['screenshot_path'] = iccsap_screenshot_path
                input_data['iccsap']['reports'] = iccsap_reports_folder
                input_data['iccsap']['generated_reports_path'] = iccsap_generated_reports_path
                input_data['iccsap']['report_path'] = iccsap_report_path
                input_data['iccsap']['report_template_path'] = iccsap_report_template_path
                input_data['iccsap']['resources'] = iccsap_resources_folder
                input_data['iccsap']["download_path"] = iccsap_downloads_folder

             # IER Sanity Tests
            if ier_sanity:
                ier_reports_folder = os.path.join(base_path, 'component_sanity_tests', 'reports', 'ier')
                ier_screenshot_path = os.path.join(ier_reports_folder, 'screenshots')
                ier_generated_reports_path = os.path.join(ier_reports_folder,'generated_reports')
                ier_report_path = os.path.join(ier_generated_reports_path, 'ier_sanity_tests_report.html')
                ier_report_template_path = os.path.join(ier_reports_folder, 'templates', 'ier_template.html')
                ier_resources_folder = os.path.join(base_path, 'component_sanity_tests', 'resources', 'ier')
                ier_downloads_folder = os.path.join(base_path, 'component_sanity_tests', 'downloads', 'ier')

                logger.info("Setting configurations for IER sanity tests")
                input_data['ier']['screenshot_path'] = ier_screenshot_path
                input_data['ier']['reports'] = ier_reports_folder
                input_data['ier']['generated_reports_path'] = ier_generated_reports_path
                input_data['ier']['report_path'] = ier_report_path
                input_data['ier']['report_template_path'] = ier_report_template_path
                input_data['ier']['resources'] = ier_resources_folder
                input_data['ier']["download_path"] = ier_downloads_folder

            # CPE Sanity Tests
            if  cpe_sanity:
                cpe_reports_folder = os.path.join(base_path, 'component_sanity_tests', 'reports', 'cpe')
                cpe_screenshot_path = os.path.join(cpe_reports_folder, 'screenshots')
                cpe_generated_reports_path = os.path.join(cpe_reports_folder,'generated_reports')
                cpe_report_path = os.path.join(cpe_generated_reports_path, 'cpe_sanity_tests_report.html')
                cpe_report_template_path = os.path.join(cpe_reports_folder, 'templates', 'cpe_template.html')
                cpe_resources_folder = os.path.join(base_path, 'component_sanity_tests', 'resources', 'cpe')
                cpe_downloads_folder = os.path.join(base_path, 'component_sanity_tests', 'downloads', 'cpe')

                logger.info("Setting configurations for CPE sanity tests")
                input_data['cpe']['screenshot_path'] = cpe_screenshot_path
                input_data['cpe']['reports'] = cpe_reports_folder
                input_data['cpe']['generated_reports_path'] = cpe_generated_reports_path
                input_data['cpe']['report_path'] = cpe_report_path
                input_data['cpe']['report_template_path'] = cpe_report_template_path
                input_data['cpe']['resources'] = cpe_resources_folder
                input_data['cpe']["download_path"] = cpe_downloads_folder

            # dumping the config values to config.tml file
            logger.info("Writing values to config.toml file ...")
            try : 
                with open(self.config_file, "w") as file :
                    file.write(dumps(input_data))
            except Exception as e :
                logger.error(f"An exception occured during writing input_data to config.toml file : {e}")
                logger.critical("Exiting execution!!")
                exit()
            
            logger.info("==========================================Ended preparation of config file==========================================\n\n")
        except Exception as e:
            raise SanityTestException("Failed to prepare the config file", cause=e) from e

if __name__ == "__main__":
    prepare_config = PrepareConfiguration()
    prepare_config.prepare_config_file()