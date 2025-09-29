import sys
import subprocess
import json
import os
import time

from utils.utils_class import Utils
from utils.common import *

class Optional_ComponentDeletion:
    def __init__(self, cluster_name, cluster_pass):
        """
        Initializes Optional_ComponentDeletion instance.
        """
        config_dict = {"cluster_name": cluster_name, "cluster_pass": cluster_pass}
        self.setup = Utils(config_dict)
        self.exception_list = []
        self.cluster_name = cluster_name
        self.cluster_pass = cluster_pass
        self.logger = self.setup.logger
        
    def patch_content_components_by_user_choice(self, components_to_disable):
        """
        Login and patch Content CR with given components.
        """
        try:
            component_mapping = {
                "content search services": "css",
                "content management interoperability services": "cmis",
                "ibm enterprise records": "ier",
                "ibm content collector for sap": "iccsap",
                "business automation insights": "bai",
                "task manager": "tm"
            }

            self.logger.logger.info(f"Patching the Content CR to disable: {components_to_disable}")
            print(f"Patching the Content CR to disable: {components_to_disable}")

            # Call login from Utils
            if not self.setup.ocp_login():
                self.logger.logger.error("Cluster login failed. Aborting patch.")
                print("Cluster login failed. Aborting patch.")
                return False

            if not components_to_disable:
                self.logger.logger.info("No components specified to disable.")
                print("No components specified to disable.")
                return True
            
            # Convert names to CRD keys (robust mapping)
            mapped_components = []
            for comp in components_to_disable:
                clean = comp.strip().lower()  #  trim spaces and lowercase

                #  accept both full names and already-abbreviated keys
                if clean in component_mapping:
                    mapped_components.append(component_mapping[clean])
                elif clean in component_mapping.values():
                    mapped_components.append(clean)  # already an abbreviation
                else:
                    self.logger.logger.warning(f"Component '{comp}' not recognized in mapping, skipping...")
                    print(f"Component '{comp}' not recognized in mapping, skipping...")

            if not mapped_components:
                self.logger.logger.info("No valid components to disable after mapping.")
                print("No valid components to disable after mapping.")
                return True

            print(f"Final mapped components (CR keys): {mapped_components}") 

            patch_list = [
                {
                    "op": "replace",
                    "path": f"/spec/content_optional_components/{component}",
                    "value": False
                }
                for component in mapped_components
            ]

            patch_payload = json.dumps(patch_list)

            patch_cmd = [
                "kubectl", "patch", "content", "content",
                "--type=json",
                "-p", patch_payload
            ]

            result = subprocess.run(patch_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                self.logger.logger.error(f"Failed to patch the content CR. Error: {result.stderr}")
                print(f"Failed to patch the content CR. Error: {result.stderr}")
                return False
            else:
                self.logger.logger.info(f"Successfully patched the content CR. Output: {result.stdout}")
                print(f"Successfully patched the content CR. Output: {result.stdout}")
                return True

        except Exception as e:
            self.logger.logger.error(f"Exception while patching the content CR: {e}")
            print(f"Exception while patching the content CR: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py '<json_string>'")
        sys.exit(1)

    try:
        # Parse the JSON string passed from Jenkins
        config_dict = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

    
    cluster_name = config_dict.get('cluster_name', '')
    cluster_pass = config_dict.get('cluster_pass', '')
    components_to_disable = config_dict.get('component_names', '')

    # If component_names is a comma-separated string, split it into a list
    if isinstance(components_to_disable, str):
        components_to_disable = components_to_disable.split(",") if components_to_disable else []

    obj = Optional_ComponentDeletion(cluster_name, cluster_pass)
    success = obj.patch_content_components_by_user_choice(components_to_disable)

    if success:
        print("Patching completed successfully.")
    else:
        print("Patching failed.")

