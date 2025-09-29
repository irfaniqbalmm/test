from types import SimpleNamespace
import json
import os
import subprocess
import sys
from subprocess import PIPE

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tomlkit import parse

from utils.bvt_status import update_status
from utils.logger import logger
import utils.login as login



from component_sanity_tests.tests.acce import ACCE
from component_sanity_tests.tests.ier import IER
import component_sanity_tests.reports.ier.generate_report as generate_report
from component_sanity_tests.utils.ier.preconfig_cmdline_exn import PreconfigCmdExn
import component_sanity_tests.utils.common_utils.create_pdf_report as pdf_report
import component_sanity_tests.utils.common_utils.reset_execution as reset_execution

CONFIG_FILE = "./component_sanity_tests/config/config.toml"
class IERSanityRunner:
    def __init__(self):
        """
        Method name: __init__
        Author: Nusaiba K K
        Description : Initialize the IERSanityRunner class with a list of object stores.
        Returns:
            None
        """
        objectstores = ["FPOS","ROS"]
        self.args = SimpleNamespace(objectstore=objectstores, config_file_path=CONFIG_FILE, product="IER")
        self.reset_execution_data = reset_execution.ResetExecutionData(self.args.product)

    def run(self):
        """
        Method name: run
        Author: Nusaiba K K 
        Description: Run the IER configurations
        Parameters:None    
        Returns:None
        """
        logger.info(f"{self.args}")

        with open(CONFIG_FILE, "r") as file :
            config = parse(file.read())
        username = config['credentials']['app_login_username']
        password = config['credentials']['app_login_password']
        project_name = config['configurations']['project_name']
        
        try:
            #reset execution data before starting the execution of testcases.
            self.reset_execution_data.reset_execution_data(CONFIG_FILE)
            #Creating FPOS and ROS object stores and creating workflow system in the FPOS object store.
            ier_sanity_checks = ACCE(self.args)
            ier_sanity_checks.ier_acce_runner()

            execution_of_profile_tasks_status = "FAILED"
            preconfig_for_cmd_exn = PreconfigCmdExn()

            batch_file = os.path.join(os.getcwd(), "component_sanity_tests", "resources", "ier", "ier_configurations.bat")
            logger.info(f"Batch file path: {batch_file}")

            #Opening the endpoints.json file to fetch the endpoints like cpe and navigator endpoint.
            with open('./inputs/endpoints.json', 'r') as json_file:
                endpoints = json.load(json_file)
            # Define the variables to update
            vars_to_update = {
                "ce_wsi_url": endpoints.get("FileNet_P8_Content_Engine_Web_Service_page"),
                "ldap_username": username,
                "gcd_password": password,
                "navigator_url": endpoints.get("navigator_route")
            }

            route_name = "content-cpe-route"
            namespace = project_name
            jre_path = r"C:\Program Files\IBM\EnterpriseRecords\jre"

            preconfig_for_cmd_exn.update_truststore_from_ocp_route(route_name, namespace, jre_path)
            # Update the .bat file
            preconfig_for_cmd_exn.update_batch_variables(batch_file, vars_to_update)
            # Run the .bat file
            # Run the .bat file and capture output
            process = subprocess.run(batch_file, shell=True, stdout=PIPE, stderr=PIPE, text=True)

            console_output = process.stdout + process.stderr
            logger.debug("Batch file output:\n" + console_output)

            # Define success markers to check for in the output
            success_markers = [
                "Completed running Create Marking Sets and Add-ons.",
                "Completed running Configure File Plan Object Store.",
                "Completed running Configure Record Object Store.",
                "Completed running Configure Workflows.",
                "Completed running Transfer Workflows.",
                "Completed running Configure Content Engine Sweep."
            ]


            # Check if all success markers are found in the output
            if all(marker in console_output for marker in success_markers):
                execution_of_profile_tasks_status = "PASSED"
                logger.info(f"Profile Tasks Execution Status is : {execution_of_profile_tasks_status}")
                update_status("Running Profile Tasks", execution_of_profile_tasks_status, self.args.product.lower())
            else:
                execution_of_profile_tasks_status = "FAILED"
                logger.info(f"Profile Tasks Execution Status is : {execution_of_profile_tasks_status}")
                update_status("Running Profile Tasks", execution_of_profile_tasks_status, self.args.product.lower())
            # Final status update
            update_status("Running Profile Tasks", execution_of_profile_tasks_status, self.args.product.lower())
            logger.info(f"Profile Tasks Execution Status updates successfully to : {execution_of_profile_tasks_status}")
            #Creating required Repository and Desktops

            ier = IER(CONFIG_FILE)
            ier.ier_icn_runner()
            

            generate_report.generate_html_report()
            pdf_report.convert_html_to_pdf(self.args.product.lower(), CONFIG_FILE)
        except Exception as e:
            logger.exception("Script execution failed")

if __name__ == "__main__":
    runner = IERSanityRunner()
    runner.run()