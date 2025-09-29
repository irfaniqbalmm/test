from utils.utils_class import *
from pull_secret import *
from utils.common import *
import re


class ClusterSetup():
    def __init__(self, cluster_name, cluster_pass, cluster_stage_prod):
        """
        Method name: __init__
        Description: Initializes a ClusterSetup instance with the given parameters.
        Parameters:
            cluster_name: The name of the cluster.
            cluster_pass: The password for the cluster.
            cluster_stage_prod: The production stage of the cluster 
        Returns:None
        """
   
        config_dict = {"stage_prod":cluster_stage_prod, "cluster_name":cluster_name, "cluster_pass":cluster_pass}
        self.setup = Utils(config_dict)
        self.exception_list = [] 
        self.cluster_name = cluster_name

    def setup_icsp(self):
        """
        Method name: setup_icsp
        Description: Setting up Image Content Source Policy for RTP/SVL machine .
        Parameters:
            None
        Returns:True/False
        Raises:
            Exception
        """
        try:
            self.setup.logger.logger.info(f'Setting up ICSP initiated in cluster.............!!')
            print(f'Setting up ICSP initiated in cluster.............!!')
            #To check if the machine is SVL or RTP 
            is_svl =svl_machine(self.cluster_name) 
            if not is_svl:
                mirror_command = ["oc", "apply", "-f", "./config/mirror-rtp.yaml"]  
                check = self.setup.check_resource(mirror_command,'created')
                if not check:
                    print(f'ICSP setup failed in the RTP Machine ......!!')
                    self.exception_list.append(f'ICSP Setup failed') 
                else :
                    print(f'ICSP is updated in the RTP Machine ......!!')
                    self.setup.logger.logger.info(f'ICSP is updated in the RTP Machine ......!!')
            else:
                mirror_command = ["oc", "apply", "-f", "./config/mirror.yaml"]  
                check = self.setup.check_resource(mirror_command,'created')
                if not check:
                    print(f'ICSP setup failed in the SVL Machine ......!!')
                    self.exception_list.append(f'ICSP Setup failed') 
                else :
                    print(f'ICSP is updated in SVL Machine ......!!')
                    self.setup.logger.logger.info(f'ICSP is updated in the SVL Machine ......!!')
        except Exception as e:
            self.setup.logger.logger.error(f'Setting up ICSP failed with error:  {e}.')
            print(f'Setting up ICSP failed with error:  {e}.')
            self.exception_list.append(f'ICSP Setup failed') 

    def setup_user(self):
        """
        Method name: setup_user
        Description: Setting up dba user 
        Parameters:
            None
        Returns:
            none
        """
        try:
            self.setup.logger.logger.info(f'Creating new dbauser.....')
            print(f'Creating new dbauser.....')
            self.setup.create_user()
        except Exception as e:
            self.setup.logger.logger.error(f'Creating new dbauser failed. with error {e}')
            print(f'Creating new dbauser failed. with error {e}')
            self.exception_list.append(f'User Creation failed')

    def setup_storage_class(self):
        """
        Method name: setup_storage_class
        Description: Setting up storage class.
        Parameters:
            None
        Returns:
                none
            Raises:
                Exception
        """
        try:
            self.setup.logger.logger.info(f'Creating new storage class: managed-nfs-storage.....')
            print(f'Creating new storage class: managed-nfs-storage.....')
            self.setup.create_storage_class()
        except Exception as e:
            self.setup.logger.logger.error(f'Creating new storage class: managed-nfs-storage failed. with error {e}')
            print(f'Creating new storage class: managed-nfs-storage failed. with error {e}')
            self.exception_list.append(f'Setup Storage Class failed')

    def setup_pull_secret(self):
        """
        Method name: setup_pull_secret
        Description:  To setup pull-secrets in cluster 
        Parameters:
            None
        Returns:
            True/False
        Raises:
            Exception
        """
        try:
            self.setup.logger.logger.info(f'Setting up pull secrets is initiated ..... ')
            print(f'Setting up pull secrets is initiated ..... ')
            result = self.setup.check_pullsecret()
            if result:
                self.setup.logger.logger.info(f'Setting up pull secrets is Successfull! ..... ')
                print(f'Setting pullsecret success!')
            else:
                self.setup.logger.logger.info(f'Setting up pull secrets is Not Successfull! ..... ')
                print(f'Setting pullsecret Failed!')
                self.exception_list.append(f'Setup Storage Class failed')
        except Exception as e:
            self.setup.logger.logger.error(f'Creating pullsecret failed. with error {e}')
            print(f'Creating pullsecret failed. with error {e}')
            self.exception_list.append(f'Setup Storage Class failed')
        
 #FIPS wall enable Functions :
    
    def checknode_fips_enabled(self):
        """
        Method name: checknode_fips_enabled
        Description: Verify the fips are enabled in the nodes.
        Parameters:
            None
        Returns:
                none
            Raises:
                Exception
        """
        try:
            self.setup.ocp_login()
            verify_ipsec_command = ['oc', 'get', 'nodes', '--no-headers']
            result = subprocess.run(verify_ipsec_command, capture_output=True, text=True, check=True)
            node_names = [line.split()[0] for line in result.stdout.splitlines()]
            print(node_names)
            for nodevalue in node_names:
                command = ['oc', 'debug', f'node/{nodevalue}', '--', 'chroot', '/host', 'sh', '-c', 'cat /proc/sys/crypto/fips_enabled']
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                is_node_fips_enabled_result = result.stdout.strip()
                if is_node_fips_enabled_result == '0':
                    print(f"The fips status of node {nodevalue}: {result.stdout.strip()}")
                    print("Unable to proceed as fips enabled status of node is 0 ")
                    raise Exception(f"Unable to proceed with cluster setup, node {nodevalue} does not have FIPS enabled")
                print(f"The fips status of node {nodevalue}: {is_node_fips_enabled_result}") 
            #If all nodes are FIPS enabled, continue without raising an exception
            print("All nodes are FIPS enabled.")  
        except Exception as e:
            self.setup.logger.logger.error(f'Node is not fips enabled , failed with error : {e}')
            print(f'Nodes are not fips enabled ')
            raise Exception ("Verifying if fips is enabled in the nodes Failed")
        
    def node_ipsec_enabling(self):
        """
        Method name: node_ipsec_enabling
        Description:  Enabling IPSec for nodes
        Parameters:
            None
        Returns:
            none
        Raises:
            Exception
        """
        try:
            self.setup.logger.logger.info(f'Enabling IPSEC initiated .....')
            print(f'Enabling IPSEC initiated .....')
            ipsec_command = ["oc", "patch", "networks.operator.openshift.io", "cluster","--type=merge","-p", '{"spec":{"defaultNetwork":{"ovnKubernetesConfig":{"ipsecConfig":{ }}}}}']
            ipsec_result = self.setup.check_resource(ipsec_command, 'patched') 
            if ipsec_result:
                self.setup.logger.logger.info(f'Enabling IPSec success ')
                print(f'Enabling  IPSec encryption success')
            else :
                self.setup.logger.logger.info(f'Enabling IPSec not success ')
                print(f'Enabling IPSec encryption not success')
                raise Exception(f'Enabling IPSec encryption not success')
        except Exception as e:
            self.setup.logger.logger.error(f'IPSec encryption not success , failed with error {e}')
            print(f'Enabling IPSec encryption not success')
            raise Exception(f'Enabling IPSec encryption not success') 
   
    def checkipsec_node_enabled(self):
        """
        Method name: checkipsec_node_enabled
        Description:  Verify IPSec enabled status in OVN-Kubernetes data plane pods
        Parameters:
            None
        Returns:
            none
        Raises:
            Exception
        """
        try:
            # Finding the names of the OVN-Kubernetes data plane pods using below command 
            self.setup.logger.logger.info(f'Checking IPSec enabled in OVN-Kubernetes data plane pods...')
            print(f'Checking if IPSec is enabled for OVN-Kubernetes data plane pods...')
            self.setup.ocp_login()
            verify_ipsec_command = ["oc", "get", "pods", "-n", "openshift-ovn-kubernetes", "-l=app=ovnkube-node", "-o", "custom-columns=:metadata.name"]
            result = subprocess.run(verify_ipsec_command, capture_output=True, text=True, check=True)
            pod_names = result.stdout.strip().split('\n') 
            print("The pod names is ", pod_names)
            #verify ipsec enabled in OVN-Kubernetes data plane pods obtained in above query 
            for podvalue in pod_names:
                command = f"oc -n openshift-ovn-kubernetes rsh {podvalue} ovn-nbctl --no-leader-only get nb_global . ipsec"
                result = subprocess.run(command, shell=True, text=True, capture_output=True)
                if  "true" not in result.stdout.strip():
                    print(f'ipsec not enabled in  the OVN-Kubernetes data plane pods ending with podvalue ',podvalue)
                else:
                     print(f'ipsec  enabled in  the OVN-Kubernetes data plane pods ending with podvalue ',podvalue)
        except Exception as e:
            self.setup.logger.logger.error(f'Failed with error {e}')
            print(f'Failed with error {e}')
            raise Exception(f'ipsec not enabled in some pods , Unable to proceed with cluster setup') 
    
    def encrypt_etct(self):
        """
        Method name: encrypt_etct
        Description:  Encrypt etcd data, enabling etcd encryption is done in  cluster to provide an additional layer of data security.
        Parameters:
            None
        Returns:
            True/False
        Raises:
            Exception
        """
        try:
            self.setup.logger.logger.info(f'Encrypt etct data initiated ...')
            print(f'Encryt etct data initiated ...')
            etcd_commmand = ["oc", "patch", "APIServer", "cluster", "-p", '{"spec":{"encryption":{"type":"aescbc"}}}', "--type=merge"]
            response = self.setup.check_resource(etcd_commmand, 'patched') 
            if response:
                self.setup.logger.logger.info(f'Encrypt etct success ')
                print("Encrypt etct success")
                self.check_until_success()
            else:
                self.setup.logger.logger.info(f'Encrypt etct not success ')
                print(f'Encrypt etct not success ')
                raise Exception(f'Encrypt etct not successful')
        except Exception as e:
                self.setup.logger.logger.error(f'etct Failed with error {e}')
                print(f'etct Failed with error {e}')
                raise Exception(f'Encrypt etct not successful') 
                
    def etct_success_openshift(self):
        """
        Method name: etct_success_openshift
        Description:  Review the Encrypted status condition for the OpenShift API server to verify that its resources were successfully encrypted:
        Parameters:
            None
        Returns:
            True/False
        """
        try:
            self.setup.logger.logger.info(f'Checking if etcd encryption was successful for OpenShift API... ')
            print(f'Checking if etcd encryption was successful for OpenShift API... ')
            etctoc_success_command = ['oc', 'get', 'openshiftapiserver', '-o=jsonpath={range .items[0].status.conditions[?(@.type=="Encrypted")]}{.reason}{"\\n"}{.message}{"\\n"}']
            response = self.setup.check_resource(etctoc_success_command,'EncryptionCompleted')
            print(response)
            if response:
                self.setup.logger.logger.info(f'OpenShift API server Resources were successfully encrypted ')
                print(f'OpenShift API resorces were successfully encrypted')
                return True 
            else:
                self.setup.logger.logger.info(f'OpenShift API server Resources were not  successfully encrypted ')
                print(f'OpenShift API server Resources  encryption was not  successfull ')
                raise Exception(f'OpenShift API server Resources  encryption was not  successfull')
        except Exception as e:
            self.setup.logger.logger.error(f'Failed with error {e}')
            return False 
            
    def etct_success_k8s(self):
        """
        Method name: etct_success_k8s
        Description:  Review the Encrypted status condition for the Kubernetes API server to verify that its resources were successfully encrypted
        Parameters:
            None
        Returns:
            True/False
        """
        try:
            self.setup.logger.logger.info(f'Checking if etcd encryption was successful for Kubernetes API... ')
            print(f'Checking if etcd encryption was successful for Kubernetes API... ')
            etctk8_success_command =  ['oc', 'get', 'kubeapiserver', '-o=jsonpath={range .items[0].status.conditions[?(@.type=="Encrypted")]}{.reason}{"\\n"}{.message}{"\\n"}']
            response = self.setup.check_resource(etctk8_success_command,'EncryptionCompleted')
            if response:
                self.setup.logger.logger.info(f'Kubernetes API server resorces  were successfully encrypted ')
                print(f'Kubernetes API  resources were successfully encrypted')
                return True
            else:
                self.setup.logger.logger.info(f'Kubernetes API server Resources were not  successfully encrypted ')
                print(f'Kubernetes API server Resources  encryption was not  successfull ')
                raise Exception(f'Kubernetes API server Resources  encryption was not  successfull')
        except Exception as e:
            self.setup.logger.logger.error(f'Failed with error {e}')
            return False
            
    def etct_success_os_oauth(self): 
        """
        Method name: etct_success_os_oauth
        Description:  Review the Encrypted status condition for the OpenShift OAuth API server to verify that its resources were successfully encrypted:
        Parameters:
            None
        Returns:
            True/False
        Raises:
            Exception
        """
        try:
            self.setup.logger.logger.info(f'Checking if etcd encryption was successful for OpenShift OAuth  API... ')
            print(f'Checking if etcd encryption was successful for OpenShift OAuth  API... ')
            etctOAuth_success_command =  ['oc', 'get', 'authentication.operator.openshift.io','-o=jsonpath={range .items[0].status.conditions[?(@.type=="Encrypted")]}{.reason}{"\\n"}{.message}{"\\n"}']
            response = self.setup.check_resource(etctOAuth_success_command,'EncryptionCompleted')
            if response:
                    self.setup.logger.logger.info(f'OpenShift OAuth API server resorces  were successfully encrypted ')
                    print(f'OpenShift OAuth API resources were successfully encrypted')
                    return True
            else:
                    self.setup.logger.logger.info(f'OpenShift OAuth API server Resources were not  successfully encrypted ')
                    print(f'OpenShift OAuth API server Resources  encryption was not  successfull ')
                    raise Exception(f'OpenShift OAuth API server Resources  encryption was not  successfull')
        except Exception as e:
                self.setup.logger.logger.error(f'Failed with error {e}')
                return False
  
    def execute_fips_functions(self):       
        """
        Method name: execute_fips_functions
        Description:  To call all Fips wall enable functions in a single function ,
        Parameters:
            None
        Returns:
            True/False
        Raises:
            Exception
        """
        try:
            self.checknode_fips_enabled()
            self.node_ipsec_enabling()
            self.checkipsec_node_enabled()
            self.encrypt_etct()
        # If an exception is raised in any function above , stop execution and don't call the next function      
        except Exception as e:
            print(f"An error occurred, Unable to proceed with cluster setup , Reason : {e}")
            self.exception_list.append(f'FIPS wall Setup Failed')
            raise Exception(f"An error occurred, Unable to proceed with cluster setup , Reason : {e}")
        
    def check_all_functions(self):   
        """
        Method name: check_all_functions
        Description:  To check the response of functions etct_success_openshift(),etct_success_k8s(),etct_success_os_oauth()
        Parameters:
            None
        Returns:
            The return type of this statement is a tuple with three elements ie etct status of OpenShify,K8s, oauth
        Raises:
            Exception
        """
        return self.etct_success_openshift(), self.etct_success_k8s(), self.etct_success_os_oauth()

    def check_until_success(self):
        """
        Method name: check_until_success
        Description:  To check the status of OpenShift,k8s and oauth Encryption status ( until those are "Encryption Completed)
        Parameters:
            None
        Returns:
            None
        Raises:
            None
        """
        while True:
            # Call the check_all_functions function to get the results of the three checks
            success_open_shift, success_k8s, success_os_oauth = self.check_all_functions()
        
        # Check if all three functions returned True
            if success_open_shift and success_k8s and success_os_oauth:
                print("Openshift , Kubernetes & OpenShift OAuth  API Encryption is successfull !!")
                print("FIPS wall enabling is success!!")
                break
            else:
                # If not, wait for 2 minutes and try again
                print("Not all conditions are met yet, waiting 2 minutes...")
                time.sleep(120)  # Wait for 2 minutes

    def check_exception_list(self): 
        """
        Method name: check_exception_list
        Description: Checks if the exception list is empty, and if not, prints each item in the list.
        Parameters:
            None
        Returns:
            None
        Raised:
            Exception
        """
        if not self.exception_list:
            print("Cluster Setup Completed Successfully in the cluster !!")
        else:
            print("Cluster setup failed in cluster with below issues :")
            raise Exception(self.exception_list)
    
    def update_haproxy_config(self):  #new added FUNCTION to CHNAGE PROXY TIMEOUTS
        """
        Method name: update_haproxy_config
        Author: Ann Maria Manuel
        Description:  Update the  proxy timeout values in Cluster
        Parameters:
            None
        Returns:
            None
        Raises:
            Exception
        """
        try:
            self.setup.logger.logger.info(f'Updating proxy timeouts in Cluster has initiated....!! ')
            print(f'Updating proxy timeouts in Cluster has initiated...!! ')
            config_file = '/etc/haproxy/haproxy.cfg'
            replacements = {
                r'^\s*option\s+redispatch\s*$': 'no option redispatch',
                r'^\s*timeout\s+http-request\s+\S+': 'timeout http-request 30s',
                r'^\s*timeout\s+client\s+\S+': 'timeout client 5m',
                r'^\s*timeout\s+server\s+\S+': 'timeout server 5m',
                r'^\s*timeout\s+http-keep-alive\s+\S+': 'timeout http-keep-alive 120s',
            }
            # Opening the  config file in read mode to read the contents and save to a list 
            with open(config_file, 'r') as file:
                lines = file.readlines()

            #Iterating through the list created which has the config file content and compares with patterns given in replacements dictionary 
            # and if matches  ,replacing the line  with new value mentioned in replacements dict  

            for idx, line in enumerate(lines):
                for pattern, replacement in replacements.items():
                    if re.match(pattern, line):
                        indent = re.match(r'^(\s*)', line).group(1) # added to correct indentation while updating 
                        lines[idx] = indent + replacement + '\n'
                        print(f"Updated: {line.strip()} -> {replacement}")
            
            # Opening config file in write mode to write the updated contents from list to config file 

            with open(config_file, 'w') as file:
                file.writelines(lines)
            print("Configuration updated successfully.")

            # Validate the config file and reload
            valid_success_msg = "Configuration file is valid"
            result = subprocess.run(['sudo', 'haproxy', '-c', '-f', config_file],capture_output=True, text=True)
            if result.returncode != 0:
                print("Config validation failed:\n", result.stderr)
                raise Exception(f'Config validation failed')
            if valid_success_msg in result.stderr + result.stdout:
                print("Configuration file is valid.")
                subprocess.run(['sudo', 'systemctl', 'reload', 'haproxy'], check=True)
                print("HAProxy reloaded successfully.")
            else:
                print("Unexpected output Found:\n", result.stderr, result.stdout)
                raise Exception(f'Config validation failed')
        except Exception as e:
            print("An error occurred in the proxy settings :", e)
            self.exception_list.append(f'proxy time Updates Failed')
            raise Exception(f'Configuring proxy settings in cluster not success') 
        
if __name__ == "__main__":
    cluster_name = sys.argv[1]  
    cluster_pass = sys.argv[2]  
    cluster_fips = sys.argv[3]  
    cluster_icsp = sys.argv[4] 
    cluster_storageClass = sys.argv[5]
    cluster_setupUser = sys.argv[6]
    cluster_pullSecret = sys.argv[7]
    cluster_stage_prod = sys.argv[8]
    cluster_proxy = sys.argv[9] 
    csobject = ClusterSetup(cluster_name, cluster_pass, cluster_stage_prod)
    if cluster_icsp == 'yes':
        csobject.setup_icsp()
    if cluster_storageClass == 'yes':
        csobject.setup_storage_class()
    if cluster_pullSecret == 'yes':
        csobject.setup_pull_secret()
    if cluster_setupUser == 'yes':
        csobject.setup_user()
    if cluster_fips == 'yes':
        csobject.execute_fips_functions()
    if cluster_proxy == 'yes':
        csobject.update_haproxy_config() 
    csobject.check_exception_list()
    

    
   
   


    
   
    
