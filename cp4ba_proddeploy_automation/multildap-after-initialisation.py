from utils.utils_class import Utils
import subprocess
from ruamel.yaml import YAML
import sys
import tempfile
import os

class MultildapPostInitialisation:

    def get_cr_from_ocp(self):
        """
        Method name: get_cr_data
        Author: Nusaiba
        Description: Get the CR content from cluster
        Parameters: None
        Returns:
            cr_content (yaml) : CR content
        """

        cr_content = subprocess.check_output(["oc", "get", "Content", "-o", "yaml"], universal_newlines=True)
        return cr_content

    def update_cr_with_additional_ldap_configurations(self, ldap):
        """
        Method name: update_cr_with_additional_ldap_configurations
        Author: Nusaiba
        Description: Add the LDAP configuration to the CR content under the 'spec' section
        Parameters: cr_content (yaml) - Current CR content in YAML format
        Returns:
            True/False - Whether the update was successful
        """
        try:
            print("started patching the CR from OCP...")
            # Load the CR content from the yaml string into a Python dictionary
            yaml = YAML()
            cr_content = self.get_cr_from_ocp()
            cr_data = yaml.load(cr_content)  # Load the YAML into a dictionary
            print("Loaded CR from OCP is:", cr_data)
            print("LDAP is:", ldap)

            content_to_be_added={}
            if ldap == "msad":
                print("selected LDAP is MSAD...")
                utils.delete_secret()
                utils.re_create_secret_for_msad_selected()
                # Set port and SSL values
                if utils.second_ldap_ssl_enabled == 'True':
                    lc_ldap_port = "636"
                    utils.create_ldap_ssl_secret_for_tds()
                    content_to_be_added=utils.update_ldap_configuration_for_TDS(lc_ldap_port, content_to_be_added)
                else:
                    lc_ldap_port = "389"
                    content_to_be_added=utils.update_ldap_configuration_for_TDS(lc_ldap_port, content_to_be_added)

            elif ldap == "sds":
                print("selected LDAP is TDS...")
                utils.delete_secret()
                utils.re_create_secret_for_tds_selected()

                # Set port and SSL values
                if utils.second_ldap_ssl_enabled == 'True':
                    lc_ldap_port = "636"
                    utils.create_ldap_ssl_secret_for_msad()
                    content_to_be_added=utils.update_ldap_configuration_for_MSAD(lc_ldap_port, content_to_be_added)
                else:
                    lc_ldap_port = "389"
                    content_to_be_added=utils.update_ldap_configuration_for_MSAD(lc_ldap_port, content_to_be_added)
            
            file_path = 'updated_cr.yaml'
            with open(file_path, 'w') as f:
                yaml.dump(content_to_be_added, f)
            print(f"Updated CR YAML content saved to: {file_path}")

            patch_command = f"oc patch content content -p \"$(cat {file_path})\" --type merge"


            # Apply the patch via 'oc patch' using the updated CR content
             # Execute the patch command to update the CR
            result = subprocess.run(patch_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = result.stdout.decode()
            stderr = result.stderr.decode()

            if result.returncode != 0:
                print(f"Error occurred: {stderr}")
            else:
                print(f"CR updated successfully: {stdout}")

            print(f'CR updated successfully with new LDAP configuration: {result}')
            
            return True

        except Exception as e:
            print(f'Failed to update CR with error: {e}')
            return False


if __name__ == "__main__":
    # Check the number of arguments passed
    arguments = sys.argv[1:]
    print(arguments)
    if len(arguments) != 18:
        print(f"Error: Expected 18 arguments, but got {len(arguments)}")
        sys.exit(1)
    db = arguments[0]
    ldap = arguments[1]
    project = arguments[2]
    branch = arguments[3]
    stage_prod = arguments[4]
    cluster_name = arguments[5]
    cluster_pass = arguments[6]
    separation_duty_on = arguments[7].lower()
    fips = arguments[8].lower()
    metastore_db = arguments[9].lower()
    extcrt = arguments[10].lower()
    git_branch = arguments[11]
    egress = arguments[12]
    tablespace_option = arguments[13]
    quick_burn = arguments[14].lower()
    multildap = arguments[15]
    second_ldap_ssl_enabled = arguments[16]
    multildap_post_init =arguments[17]

    
    config_dict ={'db': db, 
                  'ldap': ldap, 
                  'project':project, 
                  'branch': branch, 
                  'stage_prod':stage_prod, 
                  'cluster_name': cluster_name, 
                  'cluster_pass': cluster_pass, 
                  'separation_duty_on': separation_duty_on, 
                  'fips':fips, 
                  'metastore_db': metastore_db, 
                  'extcrt': extcrt, 
                  'git_branch': git_branch, 'egress':egress, 
                 'multildap':  multildap, 
                 'second_ldap_ssl_enabled': second_ldap_ssl_enabled, 
                 'multildap_post_init':multildap_post_init
                 }
    utils = Utils(config_dict}
    utils.ocp_login()
    multildap_post_init = MultildapPostInitialisation()
    multildap_post_init.update_cr_with_additional_ldap_configurations(utils.ldap)
