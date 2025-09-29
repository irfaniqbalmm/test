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
        
def generate_bai_html_report():
    """
    Method name: generate_html_report
    Author: Dhanesh
    Description: Generate the html reprot using the template
    Parameters:
        None
    Returns:
        None
    """
    with open("./BAI_BVT/resources/config.toml","r") as file :
        config = parse(file.read())

    cluster = config['configurations']['cluster']
    images_folder = config['paths']['screenshot_path']
    output_html = config['paths']['report_path']
    generated_reports_path = config['paths']['generated_reports_path']
    template_str = read_template(config['paths']['report_template_path'])
    template = Template(template_str)

    try : 
        logger.info("Loading Bvt status ... ")
        with open(f'{generated_reports_path}/bvt_status.json') as f:
            bvt_status = json.load(f)
    except Exception as e:
        logger.error(f"An exception occured during reading bvt status from bvt_status.json file : {e}")
    
    logger.info("Setting report data ...")
    report_data = {
        'report_title': f"BVT - BAI Standalone {config['configurations']['build']} {config['configurations']['ifix_version']} production Deployment ",
        'Logs' : bvt_status["Logs"],
        'BAI_Content_Dashboard' : bvt_status["BAI_Content_Dashboard"],
        'BAI_Navigator_Dashboard' : bvt_status["BAI_Navigator_Dashboard"],
        'OCP_installed_operators' : bvt_status["OCP_installed_operators"],
        'OCP_access_configmaps' : bvt_status["OCP_access_configmaps"],
        'access_info_contents' : bvt_status["access_info_contents"],
        'bai_bpc_dashboard_login' : bvt_status["bai_bpc_dashboard_login"],
        'bai_bpc_dashboard_count' : bvt_status["bai_bpc_dashboard_count"],
        'Opensearch' : bvt_status["Opensearch"],
        'platform': f"OCP {config['configurations']['ocp_version']}",
        'project': f"{config['configurations']['project_name']}",
        'env': f'{cluster} Cluster',
        'console_link': f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com',
        'credentials': f"{config['credentials']['app_login_username']}/{config['credentials']['app_login_password']}",
        'infrastructure_node': f'api.{cluster}.cp.fyre.ibm.com',
        'root_credentials': f"root / {config['credentials']['infra_node_pwd']}",
        'ldap': f"{config['configurations']['LDAP']}",
        'products': ['BAI Standalone'],
        'test_cases': [
            'Verify operators are installed successfully',
            'Verify the bai-access-info generated successfully',
            'Verify all expected data is present in the bai-access-info',
            'Verify bai dashboard login and count of dashboards are accurate',
            'Verify content dashboard and data is present in all the components',
            'Verify navigator dashboard and data is present in all the components',
            'Verify opensearch url is present and able to access',
            'Verify no errors are present in the bai operator logs'
        ],
        'scripts_tested': [
            f"{config['configurations']['build']}",
            'bai-cluster-admin-setup',
            'bai-prerequisites',
            'bai-deployment',
        ],
        'installed_operators': f'{images_folder}/installed_operators.png',
        'access_configmaps': f'{images_folder}/access_configmaps.png',
        'bai_dashboard': f'{images_folder}/bai_bpc_dashboard.png',
        'content_dashboard': f'{images_folder}/bai_content_dashboard.png',
        'navigator_dashboard': f'{images_folder}/bai_navigator_dashboard.png',
        'opensearch' : f'{images_folder}/opensearch.png'
    }
    logger.info("Report data setting completed!")
    logger.info("Rendering HTML template..")
    html_content = template.render(report_data)
    logger.info("Template rendered.")
    with open(output_html, 'w') as html_file:
        html_file.write(html_content)
        logger.info("HTML report generated.")

if __name__ == "__main__":
    generate_bai_html_report()
