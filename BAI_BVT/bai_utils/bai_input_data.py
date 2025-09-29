import os
import sys
import configparser
import json
from tomlkit import parse,dumps
from bai_utils.get_cr_property import get_ldap_from_bai_deployment
sys.path.append(os.getcwd())
import utils.oc_version as oc_version
from  utils.logger import logger
import utils.login as login

def write_input_data():
    """
        Method name: write_input_data
        Author: Dhanesh
        Description: Read data from config.ini file and setting values into config.toml file
        Parameters:
            None
        Returns:
            None
    """
    logger.info("==========================================Starting execution of bai_input_data.py==========================================")
    # Reading config.toml file
    logger.info("Reading ./BAI_BVT/resources/config.toml file into input_data variable ...")
    try : 
        with open("./BAI_BVT/resources/config.toml","r") as file : 
            input_data = parse(file.read())
    except Exception as e :
        logger.critical(f"An exception occured during reading the toml file : {e}")

    deployment_type = 'production'
    # Configurations from config.ini
    logger.info("Reading configurations from config.ini file")
    config = configparser.ConfigParser()
    config.read('./BAI_BVT/resources/config.ini')
    project_name = config.get('configurations', 'project_name')
    build = config.get('configurations', 'build')
    ifix_version = config.get('configurations', 'ifix_version')
    cluster = config.get('configurations', 'cluster')
    ldap = get_ldap_from_bai_deployment()
    git_user = config.get('configurations','git_user')
    git_pwd = config.get('configurations','git_pwd')

    username,password = login.get_ldap_bind_secret(project_name)
    logger.info(f"Applogin credentilas used : {username}/{password}")
    
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
    input_data['configurations']['LDAP'] = ldap
    input_data['configurations']['ocp_version'] = ocp_version
    input_data['configurations']['user'] = 'admin'

    # git
    logger.info("Setting git configurations")
    input_data['git']['git_user'] = git_user
    input_data['git']['git_pwd'] = git_pwd

    # paths
    base_path = os.getcwd() #Expected location is ../Cp4ba-Automation/CP4BA_Package/
    screenshot_path = os.path.join(base_path, 'BAI_BVT', 'screenshots')
    download_path = os.path.join(base_path, 'BAI_BVT', 'downloads')
    reports = os.path.join(base_path, 'BAI_BVT', 'reports')
    generated_reports_path = os.path.join(reports,'generated_reports')
    report_path = os.path.join(generated_reports_path, 'bvt_report.html')
    report_template_path = os.path.join(reports, 'templates', 'template.html')
    cluster_file = os.path.join(base_path, 'clusters.json')

    f = open(f'{cluster_file}')
    cluster_data = json.load(f)
    cluster_found = False
    for i in cluster_data :
        if str(i).lower() == cluster.lower() :
            cluster_found = True
            infra_node_pwd = cluster_data[i]['root_pwd']
            kube_Admin_password = cluster_data[i]['kube_pwd']
    if not cluster_found:
        logger.error("Add cluster details to cluster.json file!")
        logger.critical("Exiting BVT execution!!")
        exit()

    # credentials
    logger.info("Setting credentials")
    input_data['credentials']['infra_node_uname'] = 'root'
    input_data['credentials']['infra_node_pwd'] = infra_node_pwd
    input_data['credentials']['kube_admin_username'] = 'kubeadmin'
    input_data['credentials']['kube_admin_password'] = kube_Admin_password
    input_data['credentials']['app_login_username'] = username
    input_data['credentials']['app_login_password'] = password

    # ocp paths
    ocp = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/operators.coreos.com~v1alpha1~ClusterServiceVersion'
    config_maps = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/core~v1~ConfigMap?orderBy=desc&sortBy=Created'
    secrets = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/secrets/secret_name'

    # paths
    logger.info("Setting paths")
    input_data['paths']['base_path'] = base_path
    input_data['paths']['screenshot_path'] = screenshot_path
    input_data['paths']['download_path'] = download_path
    input_data['paths']['reports'] = reports
    input_data['paths']['generated_reports_path'] = generated_reports_path
    input_data['paths']['report_path'] = report_path
    input_data['paths']['report_template_path'] = report_template_path
    input_data['paths']['cluster_file'] = cluster_file

    #ocp_paths
    logger.info("Setting ocp_paths")
    input_data['ocp_paths']['ocp'] = ocp
    input_data['ocp_paths']['config_maps'] = config_maps
    input_data['ocp_paths']['secrets'] = secrets

    # dumping the config values to config.tml file
    logger.info("Writing values to bai config.toml file ...")
    try : 
        with open("./BAI_BVT/resources/config.toml","w") as file :
            file.write(dumps(input_data))
    except Exception as e :
        logger.error(f"An exception occured during writing input_data to bai config.toml file : {e}")
        logger.critical("Exiting BVT execution!")
        exit()
    
    logger.info("==========================================Ended execution of bai_input_data.py==========================================\n\n")
