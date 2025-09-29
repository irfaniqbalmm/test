import configparser
from utils.utils_class import *
from utils.common import run_cmd
from utils.logs import * 
import sys
import json
import os

class CustomResources(Utils):

    def __init__(self, config_dict):
        """
       Desc: To create __init__ 
        Parameters:
            dict: config_dict
        Returns:
            none
        """

        self.logger = DeploymentLogs()
        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.parser.read(current_dir + '/config/data.config')
        self.certs_dir = self.parser.get('PREREQUISITES', 'CUSTOM_CERTS')
        self.custom_host = self.parser.get('PREREQUISITES', 'CUSTOM_HOST')
        self.logger.logger.info(f"The custom certificate directory is {self.certs_dir}")
        self.project_name = config_dict.get('project', 'cp')
        self.cluster_name = config_dict.get('cluster_name', 'cp')
        self.cluster_pass = config_dict.get('cluster_pass', 'cp')
        self.logger.logger.info(f"Project is : {self.project_name}")
        super().ocp_login()
        super().switch_namespace()

    def create_route_certificate(self):
        """
        Name: create_route_certificate
        Desc: To create custom route, hostname and certificate
        Parameters:
            none
        Returns:
            True/False
        Raises:
            Exception, ValueError
        """
        try:

            # Directory where certs are stored
            self.logger.logger.info("In the create_route_certificate to create the cusomt rout , hostname and certificate.")

            self.logger.logger.info(f"# Step 1: Create a folder inside {self.certs_dir}")
            run_cmd(f"mkdir {self.certs_dir}")

            self.logger.logger.info(f"# Step 2: Generate CA private key")
            run_cmd("openssl genrsa -out ca.key 2048", cwd=self.certs_dir)

            self.logger.logger.info(f"# Step 3: Generate CA certificate")
            run_cmd('openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt -subj "/CN=MyCA"', cwd=self.certs_dir)

            self.logger.logger.info(f"# Step 4: Generate TLS private key")
            run_cmd("openssl genrsa -out tls.key 2048", cwd=self.certs_dir)

            self.logger.logger.info(f"# Step 5: Create CSR with SAN")
            run_cmd('openssl req -new -key tls.key -out server.csr -subj "/CN=test.apps.antman.cp.fyre.ibm.com" -addext "subjectAltName=DNS:test.apps.antman.cp.fyre.ibm.com"', cwd=self.certs_dir)

            openssl_san_content = f"""[req]
            distinguished_name = req_distinguished_name
            req_extensions = v3_req
            [req_distinguished_name]
            [v3_req]
            subjectAltName = DNS:test.apps.{self.cluster_name}.cp.fyre.ibm.com
            """

            self.logger.logger.info(f"# Define the file path")
            file_path = self.certs_dir+"/openssl-san.cnf"  # Adjust path as needed

            self.logger.logger.info(f"# Write the content to the file")
            with open(file_path, "w") as f:
                f.write(openssl_san_content)

            self.logger.logger.info(f"Created {file_path} with SAN configuration.")

            self.logger.logger.info(f"# Step 6: Sign CSR with CA to generate TLS certificate")
            run_cmd("openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out tls.crt -days 365 -sha256 -extfile openssl-san.cnf -extensions v3_req", cwd=self.certs_dir)

            self.logger.logger.info(f"# Step 7: Inspect the certificate")
            run_cmd("openssl x509 -in tls.crt -text -noout", cwd=self.certs_dir)

            self.logger.logger.info(f"# Step 8: Create OpenShift TLS secret")
            run_cmd(f"oc -n {self.project_name} create secret generic cpd-route-tls-secret "
                    "--from-file=tls.crt=tls.crt "
                    "--from-file=tls.key=tls.key "
                    "--from-file=ca.crt=ca.crt "
                    "--dry-run=client -o yaml | oc apply -f -", cwd=self.certs_dir)
            return True
        except Exception as e:
            self.logger.logger.error(f'Certificate creation failed with error {e}')
            return False

    def patch_zenservice(self):
        """
        Name: patch_zenservice
        Desc: To create custom route, hostname and certificate
        Parameters:
            none
        Returns:
            True/False
        Raises:
            Exception, ValueError
        """
        try:
            # Define your custom host and namespace
            custom_host = f"{self.custom_host}.apps.{self.cluster_name}.cp.fyre.ibm.com"
            self.logger.logger.info(f"Define your custom host {custom_host} and namespace {self.project_name}")

            # Construct the JSON patch payload
            patch_payload = [
                {"op": "add", "path": "/spec/zenCustomRoute/route_host", "value": custom_host},
                {"op": "add", "path": "/spec/zenCustomRoute/route_secret", "value": "cpd-route-tls-secret"},
                {"op": "add", "path": "/spec/zenCustomRoute/route_reencrypt", "value": True}
            ]
            self.logger.logger.info(f"Payload follows {patch_payload}")

            # Convert to JSON string
            patch_str = json.dumps(patch_payload)

            # Build the oc patch command
            cmd = [
                "oc", "patch", "ZenService", "iaf-zen-cpdservice",
                "--type=json",
                f"--patch={patch_str}",
                "-n", self.project_name
            ]
            self.logger.logger.info(f"Patch command is {cmd}")

            # Execute the command
            result = run_cmd(cmd, shell=False)

            # Output result
            if result:
                self.logger.logger.info("Patch applied successfully:")
                return True
            else:
                self.logger.logger.error("Error applying zenservice patch")
                return True
        except Exception as e:
            self.logger.logger.error(f'Patching of the zenservice is failed with error {e}')
            return False
        
    def check_zenservice(self):
        """
        Name: check_zenservice
        Desc: To Check zenservice is available or not
        Parameters:
            none
        Returns:
            True/False
        """
        try:
            cmd = "oc get ZenService -A --no-headers | grep iaf-zen-cpdservice | wc -l"
            self.logger.logger.info(f"Running the zenservice check using {cmd}")
            result = run_cmd(cmd, return_output=True)
            self.logger.logger.info(f"Status of the zenservice check is {result}")
            return result
        except Exception as e:
            self.logger.logger.error(f'Status of the zenservice check is failed with error {e}')
            return False
        
if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(len(sys.argv))
            raise Exception("Supplied arguments count is less than expected. Exiting...")

        #Getting the passed value from the dictiory
        config_dict = json.loads(sys.argv[1])
        project = config_dict.get('project', 'cp')
        cluster_name = config_dict.get('cluster_name', 'cp')
        print(f'Project={project} \n cluster_name={cluster_name}')
        print(f'Received parameters are {config_dict}')
        custom_status = CustomResources(config_dict)

        # Checking the zenservice status. Exiting if zenservice is available
        max_attempts = 15
        interval_seconds = 60
        for attempt in range(1, max_attempts + 1):
            zenstatus= custom_status.check_zenservice()
            if zenstatus:
                break
            else:
                # Wait before retrying
                time.sleep(interval_seconds)
        else:
            print(f"ZenService did not become available after {max_attempts} attempts.")
            raise Exception(f"ZenService did not become available after {max_attempts} attempts.")

        # If zen available the update the custom host and certificates
        if zenstatus:
            status = custom_status.create_route_certificate()
            if status:
                custom_status.patch_zenservice()

    except Exception as e:
        print(f"Creation of the custom hostname and certificate failed. Error as : {e}")
        raise Exception(f"Creation of the custom hostname and certificate failed. Error as : {e}")
