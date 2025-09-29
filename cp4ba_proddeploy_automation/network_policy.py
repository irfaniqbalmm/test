import sys, os
import configparser
import pexpect
from utils.logs import *

class NetworkPolicy:
    def __init__(self, namespace, scriptname='cp4a-'):
        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()
        self.logger = DeploymentLogs('network')
        self.parser.read(current_dir + '/config/data.config')
        self.script_folder = self.parser.get('PREREQUISITES', 'SCRIPT_FOLDER')
        self.network_script = self.script_folder + scriptname+"network-policies.sh"
        self.namespace = namespace

    def network_operation(self, operation='generate'):
        """
        Method name: network_operation
        Description: Running the network operations. values are generate, install and delete
        Parameters: None
        Returns:
            True/False
        """
        try:
            self.logger.logger.info(f'Network {operation} script is {self.network_script}')
            command = f"bash  {self.network_script}  -m {operation} -n {self.namespace}"
            process = pexpect.spawn(command)
            self.logger.logger.info(f'Command running is {command}.')
            process.sendline('Yes')
            process.expect(['#', pexpect.EOF], timeout=240) 
            output = process.before.decode('utf-8')
            self.logger.logger.info(f'network Operation {operation} :  {output}')
            return True
        except Exception as e:
            self.logger.logger.error(f'Network {operation} script is {self.network_script} failed with error = {e}')
            return False
        except:
            self.logger.logger.error(f'Network {operation} Failed with error. Please see the logs for more details.')
            return False


if __name__ == "__main__":
    # Check the number of arguments passed
    arguments = sys.argv[1:]
    print(arguments)
    if len(arguments) != 1:
        print(f"Error: Expected 1 arguments, but got {len(arguments)}")
        sys.exit(1)
    namespace = arguments[0]
    np = NetworkPolicy(namespace)
    print('generate', 100*'#')
    np.network_operation('generate')
    print('install', 100*'#')  
    np.network_operation('install')
    # print('delete',100*'#')
    # np.network_operation('delete')