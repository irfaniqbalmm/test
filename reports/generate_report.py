import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from jinja2 import Template
import json
from tomlkit import parse
from utils.logger import logger

def read_template(file_path):
    """
    Method name: read_template
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Open and read the template file
    Parameters:
        file_path : path to template
    Returns:
        template data
    """
    logger.info("Reading template ...")
    try:
        with open(file_path, 'r') as template_file:
            return template_file.read()
        logger.info("Template read.")
    except Exception as e :
        logger.error(f"An exception occured while reading template : {e}")
        
def generate_html_report() :
    """
    Method name: generate_html_report
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Generate the html reprot using the template
    Parameters:
        None
    Returns:
        None
    """
    with open("./inputs/config.toml","r") as file :
        config = parse(file.read())

    cluster = config['configurations']['cluster']
    images_folder = config['paths']['screenshot_path']
    output_html = config['paths']['report_path']
    generated_reports_path = config['paths']['generated_reports_path']
    template_str = read_template(config['paths']['report_template_path'])
    template = Template(template_str)
    try : 
        logger.info("Reading deployment status ...")
        with open(f'{generated_reports_path}/cp4ba_deployment_status.json') as f:
            deployment_status = json.load(f)
    except Exception as e:
        logger.error(f"An exception occured during reading deployment status from cp4ba_deployment_status.json file : {e}")

    try : 
        logger.info("Loading Bvt status ... ")
        with open(f'{generated_reports_path}/bvt_status.json') as f:
            bvt_status = json.load(f)
    except Exception as e:
        logger.error(f"An exception occured during reading bvt status from bvt_status.json file : {e}")
    
    logger.info("Setting report data ...")
    report_data = {
        'report_title': f"BVT - CP4BA {config['configurations']['build']} {config['configurations']['ifix_version']} {config['configurations']['deployment_type']} Deployment ",
        'BAI_Content_Dashboard' : bvt_status["BAI_Content_Dashboard"],
        'BAI_Navigator_Dashboard' : bvt_status["BAI_Navigator_Dashboard"],
        'ICCSAP' : bvt_status["ICCSAP"],
        'CMIS_CP4BA' : bvt_status["CMIS_CP4BA"],
        'CMIS_OCP' : bvt_status["CMIS_OCP"],
        'TM' : bvt_status["TM"],
        'IER' : bvt_status["IER"],
        'IER_Plugin' : bvt_status["IER_Plugin"],
        'OCP_installed_operators' : bvt_status["OCP_installed_operators"],
        'OCP_access_configmaps' : bvt_status["OCP_access_configmaps"],
        'OCP_init_configmap' : bvt_status["OCP_init_configmap"],
        'OCP_verify_configmap' : bvt_status["OCP_verify_configmap"],
        'CPE_index_area' : bvt_status["CPE_index_area"],
        'CPE_ICN_Object_store' : bvt_status["CPE_ICN_Object_store"],
        'CPE_ObjectStore_Tablespaces_Creation' : bvt_status["OS_Tablespaces_Creation"],
        'CSS_search' : bvt_status["CSS_search"],
        'CPE_Health_Page' : bvt_status["CPE_Health_Page"],
        'CPE_Ping_page' : bvt_status["CPE_Ping_page"],
        'CPE_P8BPMREST' : bvt_status["CPE_P8BPMREST"],
        'CPE_Stateless_Health_Page' : bvt_status["CPE_Stateless_Health_Page"],
        'CPE_Stateless_Ping_Page' : bvt_status["CPE_Stateless_Ping_Page"],
        'FileNet_Process_Services_ping_page' : bvt_status["FileNet_Process_Services_ping_page"],
        'FileNet_Process_Services_details_page' : bvt_status["FileNet_Process_Services_details_page"],
        'FileNet_P8_Content_Engine_Web_Service_page' : bvt_status["FileNet_P8_Content_Engine_Web_Service_page"],
        'FileNet_Process_Engine_Web_Service_page' : bvt_status["FileNet_Process_Engine_Web_Service_page"] ,
        'Content_Search_Services_health_check' : bvt_status["Content_Search_Services_health_check"],
        'Stateless_FileNet_Process_Services_ping_page' : bvt_status["Stateless_FileNet_Process_Services_ping_page"],
        'Stateless_FileNet_Process_Services_details_page' : bvt_status["Stateless_FileNet_Process_Services_details_page"],
        'Stateless_FileNet_P8_Content_Engine_Web_Service_page' : bvt_status["Stateless_FileNet_P8_Content_Engine_Web_Service_page"],
        'Stateless_FileNet_Process_Engine_Web_Service_page' : bvt_status["Stateless_FileNet_Process_Engine_Web_Service_page"],
        'Stateless_Content_Search_Services_health_check' : bvt_status["Stateless_Content_Search_Services_health_check"],
        'Opensearch' : bvt_status["Opensearch"],
        'Navigator_desktops' : bvt_status["Navigator_desktops"],
        'Navigator_Second' : bvt_status["Navigator_Second"],
        'CMOD' : bvt_status["CMOD"],
        'CM8' : bvt_status["CM8"],
        'Graphql' : bvt_status["Graphql"],
        'Logs' : bvt_status["Logs"],
        'FISMA' :bvt_status["FISMA"],
        'platform': f"OCP {config['configurations']['ocp_version']}",
        'project': f"{config['configurations']['project_name']}",
        'deployment_type': f"{config['configurations']['deployment_type']}",
        'liberty': f'{bvt_status["liberty_version"]}',
        'java_version': f'{bvt_status["java_version"]} (build {bvt_status["java_build"]})', 
        'credentials': f"{config['credentials']['app_login_username']}/{config['credentials']['app_login_password']}",
        'env': f'{cluster} Cluster',
        'console_link': f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com',
        'infrastructure_node': f'api.{cluster}.cp.fyre.ibm.com',
        'root_credentials': f"root / {config['credentials']['infra_node_pwd']}",
        'fips_status' : bvt_status["fips"],
        'egress' : bvt_status["egress"],
        'OC_Automations' : bvt_status["OC_Automations"],
        'JVM_Custom_Options' : bvt_status["JVM_Custom_Options"],
        'database': f"{config['configurations']['DB']}",
        'ldap': f"{config['configurations']['LDAP']}",
        'products': ['CPE', 'CSS', 'ICN', 'GraphQL', 'TM', 'CMIS', 'IER', 'BAI', ],
        'test_cases': [
            'Create domain via ACCE (Init)',
            'Create object store(s) via ACCE (Init)',
            'Configure CSS on an object store (Init)',
            'Create folder and document (Verify)',
            'Query document (CSS) (Verify)',
            'Create repository and desktop in Navigator',
            'Browse object store in Navigator'
            'External Share Config & Share Document',
            'Task Manager Ping Page',
            'Workflow Transfer and Launch',
            'GraphQl Query and Mutation',
        ],
        'scripts_tested': [
            f"{config['configurations']['build']}",
            'cp4a-cluster-admin-setup',
            'cp4a-deployment',
        ],
        'installed_operators': f'{images_folder}/installed_operators.png',
        'init_configmaps': f'{images_folder}/initialization_configmaps.png',
        'verify_configmaps': f'{images_folder}/verification_configmaps.png',
        'access_configmaps': f'{images_folder}/access_configmaps.png',
        'cpe': {
            'index_area': f'{images_folder}/cpe-os01_index_area.png',
            'os_tablespaces' : f'{images_folder}/os_tablespaces.png',
            'health_page': f'{images_folder}/cpe-health-page.png',
            'ping_page': f'{images_folder}/cpe-ping-page.png',
            'p8bpmrest': f'{images_folder}/p8bpmrest.png',
            'legacy_health_page' : f'{images_folder}/cpe-stateless-health-page.png',
            'legacy_ping_page' : f'{images_folder}/cpe-stateless-ping-page.png',
            'FileNet_Process_Services_ping_page' : f'{images_folder}/fps_ping_page.png',
            'FileNet_Process_Services_details_page' : f'{images_folder}/fps_details_page.png',
            'FileNet_P8_Content_Engine_Web_Service_page' : f'{images_folder}/ce_web_page.png',
            'FileNet_Process_Engine_Web_Service_page' : f'{images_folder}/pe_web_page.png',
            'Content_Search_Services_health_check' : f'{images_folder}/css_web_page.png',
            'Stless_FileNet_Process_Services_ping_page' : f'{images_folder}/Stless_FPS_ping_page.png',
            'Stless_FileNet_Process_Services_details_page' : f'{images_folder}/Stless_FPS_details_page.png',
            'Stless_FileNet_P8_Content_Engine_Web_Service_page' : f'{images_folder}/Stless_ce_web_page.png',
            'Stless_FileNet_Process_Engine_Web_Service_page' : f'{images_folder}/Stless_pe_web_page.png',
            'Stless_Content_Search_Services_health_check' : f'{images_folder}/Stless_css_web_page.png',
        },
        'css_search': f'{images_folder}/css_search.png',
        'navigator': {
            'd1': f'{images_folder}/nav1_desktop.png',
            'd2': f'{images_folder}/Nav2_desktop.png',
            'cm8': f'{images_folder}/cm8.png',
            'cmod': f'{images_folder}/cmod.png',
        },
        'icn_object_store_browse': f'{images_folder}/icn_obj_store.png',
        'task_manager': f'{images_folder}/taskmanager.png',
        'cmis': {
            'cp4ba': f'{images_folder}/cmis1.png',
            'ocp_route': f'{images_folder}/cmis_2.png',
        },
        'graphql1': f'{images_folder}/graphql1.png',
        'graphql2': f'{images_folder}/graphql2.png',
        'graphql3': f'{images_folder}/graphql3.png',
        'ier1': f'{images_folder}/ier1.png',
        'ier2': f'{images_folder}/ier2.png',
        'IER_plugin' : f'{images_folder}/IER_plugin.png',
        'bai': f'{images_folder}/bai.png',
        'nav_dash' : f'{images_folder}/Navigator_dashboard.png',
        'iccsap': f'{images_folder}/iccsap.png',
        'iccsap_pluggin': f'{images_folder}/iccsap_jar_files.png',
        'opensearch' : f'{images_folder}/opensearch.png',
        'deployment_status' : deployment_status,
    }
    logger.info("Report data setting completed!")
    logger.info("Rendering HTML template..")
    html_content = template.render(report_data)
    logger.info("Template rendered.")
    with open(output_html, 'w') as html_file:
        html_file.write(html_content)
        logger.info("HTML report generated.")

if __name__ == "__main__":
    generate_html_report()
