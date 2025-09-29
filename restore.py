import argparse
import os
import shutil
import subprocess
from utils import login, endpoints 
from utils.clean_data import CleanFolder
from component_pages.logs.get_logs import logs_check
from reports import pdf_report
import inputs.input_data as input_data
import utils.json_to_xml as json_to_xml


class Restore:
    """
    Name: Restore
    Author : Nusaiba K K
    Description: Rerun components after restoring
    Parameters:  
        script_name : date , cluster  , deployment type , namespace , component to be rerun
    Returns:  None
    """
    def __init__(self, args) -> None:
        ##### Paths ######
        self.base_path = os.getcwd()  # Expected location is ../Cp4ba-Automation/CP4BA_Package/
        self.screenshot_path = os.path.join(self.base_path, 'screenshots')
        self.download_path = os.path.join(self.base_path, 'downloads')
        self.reports_path = os.path.join(self.base_path, 'reports')
        self.gen_report_path = os.path.join(self.reports_path, 'generated_reports')
        self.bvt_status_file = os.path.join(self.gen_report_path, 'bvt_status.json')
        self.args = args

    def restore_backup(self):
        """
        Method name: restore_backup
        Author : Nusaiba K K
        Description: Restore files from backup folder
        """
        backup_folder = os.path.join(self.base_path, "backup", self.args.date, self.args.cluster, f"{self.args.namespace}_{self.args.deployment}")
        
        if not os.path.exists(backup_folder):
            print(f"Backup folder not found: {backup_folder}")
            return
        
        try:
            # Restore bvt_status.json
            bvt_status_path = os.path.join(backup_folder,"generated_reports", "bvt_status.json")
            if os.path.exists(bvt_status_path):
                shutil.copy(bvt_status_path, os.getcwd())
                print("Restored file: bvt_status.json")

            # Restore screenshots
            self.restore_directory(os.path.join(backup_folder, "screenshots"), self.screenshot_path)

            # Restore generated reports
            self.restore_directory(os.path.join(backup_folder, "generated_reports"), self.gen_report_path)

            
            # Restore config.ini
            config_path = os.path.join(backup_folder, "config.ini")
            if os.path.exists(config_path):
                shutil.copy(config_path, os.getcwd())
                print("Restored file: config.ini")

        except Exception as e:
            print(f"Error occurred during restoration: {e}")

    def restore_directory(self, src, dest):
        """
        Method name: restore_directory
        Author : Nusaiba K K
        Description: Restores files from src to dest.
        """
        if not os.path.exists(src):
            print(f"Source directory {src} does not exist.")
            return
        if os.path.exists(dest):
            try:
                shutil.rmtree(dest)
                print(f"Removed existing {dest} directory.")
            except Exception as e:
                print(f"Failed to remove {dest}: {e}")

        if os.path.exists(src):
            try:
                shutil.copytree(src, dest)
                print(f"Restored: {dest}")
            except Exception as e:
                print(f"Failed to restore {src}: {e}")
        else:
            print(f"Skipping {src} as it does not exist in backup.")

    def re_execute(self):
        """
        Method name: re_execute
        Author : Nusaiba K K
        Description: Re-execute components failed
        """
        component_map = {
            "OCP installed operators": "./component_pages/ocp.py",
            "OCP access configmaps": "./component_pages/ocp.py",
            "OCP init configmaps": "./component_pages/ocp.py",
            "OCP verify configmaps": "./component_pages/ocp.py",
            "ICCSAP": "./component_pages/iccsap.py",
            "CMIS CP4BA": "./component_pages/cmis.py",
            "CMIS OCP (Legacy route)": "./component_pages/cmis.py",
            "graphql": "./component_pages/graphql.py",
            "CPE index area": "./component_pages/cpe/cpe.py",
            "CPE ICN Object store": "./component_pages/cpe/cpe.py",
            "CSS search": "./component_pages/cpe/cpe.py",
            "CPE Health Page": "./component_pages/cpe/cpe.py",
            "CPE Ping page": "./component_pages/cpe/cpe.py",
            "CPE Legacy Health Page": "./component_pages/cpe/cpe.py",
            "CPE Legacy Ping Page": "./component_pages/cpe/cpe.py",
            "CPE P8BPMREST Endpoint": "./component_pages/cpe/p8bpmrest.py",
            "FileNet Process Services ping page": "./component_pages/cpe/filenet.py",
            "FileNet Process Services details page": "./component_pages/cpe/filenet.py",
            "FileNet P8 Content Engine Web Service page": "./component_pages/cpe/filenet.py",
            "FileNet Process Engine Web Service page": "./component_pages/cpe/filenet.py",
            "Content Search Services health check": "./component_pages/cpe/filenet.py",
            "Stateless FileNet Process Services ping page": "./component_pages/cpe/filenet_stateless.py",
            "Stateless FileNet Process Services details page": "./component_pages/cpe/filenet_stateless.py",
            "Stateless FileNet P8 Content Engine Web Service page": "./component_pages/cpe/filenet_stateless.py",
            "Stateless FileNet Process Engine Web Service page": "./component_pages/cpe/filenet_stateless.py",
            "Stateless Content Search Services health check": "./component_pages/cpe/filenet_stateless.py",
            "opensearch/elasticsearch": "./component_pages/opensearch.py",
            "Navigator desktops": "./component_pages/navigator/nav_utility.py",
            "CM8": "./component_pages/navigator/nav_cm8.py",
            "CMOD": "./component_pages/navigator/nav_cmod.py",
            "Navigator Legacy route": "./component_pages/navigator/nav_legacy.py",
            "IER": "./component_pages/ier/ier.py",
            "IER Plugin": "./component_pages/ier/ier_nav.py",
            "TM": "./component_pages/taskmanager.py",
            "BAI Content Dashboard": "./component_pages/bai.py",
            "BAI Navigator Dashboard": "./component_pages/bai.py",
            "Operator logs": "logs_check()"
        }

        # Clean up component input
        
        script_set = set()

        print("Components passed:", self.args.component)
        components = self.args.component[0].split(',')
        print("splitted components:",components)
        for component in components:
            mapped_script = component_map.get(component)
            print(f"Component: {component}, Mapped Script: {mapped_script}")  # Debugging
            if component == "Operator logs":
                logs_check()
            elif component in component_map :
                script_set.add(mapped_script)
            else:
                print(f"Warning: Unknown component '{component}', skipping.")
        print("Scripts to execute:", script_set)
        # Execute each script only once
        for script in script_set:
            try:
                script_path = os.path.abspath(script)
                print(f"Running script: {script_path}")
                subprocess.run(["python", script_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error executing {script_path}: {e}")
        
        if hasattr(pdf_report, 'convert_html_to_pdf'):
            pdf_report.convert_html_to_pdf()
        else:
            print("Error: convert_html_to_pdf() not found in pdf_report")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore Backup Script")
    parser.add_argument("--date", required=True, help="Backup date (YYYY-MM-DD)")
    parser.add_argument("--cluster", required=True, help="Cluster name")
    parser.add_argument("--namespace", required=True, help="Namespace/project name")
    parser.add_argument("--deployment", required=True, help="Deployment type")
    parser.add_argument("--component", nargs='+', required=True, help="Component to re-execute (comma-separated)")

    args = parser.parse_args()
    restore = Restore(args)
    restore.restore_backup()
    login.ocp_login()
    input_data.initialize_input_data()
    endpoints.fetch_endpoints()
    restore.re_execute()
    json_to_xml.generate_xml_report("bvt_rerun_xml_report")
    clean = CleanFolder() 
    backup_restored_files = clean.create_backup()
