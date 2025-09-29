import pexpect
import re
import sys
import time
from  ifixlog import IfixLogs

# logfile = open('ifix_upgradeOperator.log', 'wb')

class IfixUpgrade:
    def __init__(self, project_name):
        self.ifix_project = project_name
        self.ifix_logger = IfixLogs('ifixUpgrade')


    def ifix_upgradeOperator(self):
        """
            Method name: ifix_upgradeOperator
            Description: Perform ifix upgrade of operators
            Parameters:
                project: Namespace name
            Returns:
                True/False
        """
        print(self.ifix_project)
        try:
            script = f'/opt/ifix_upgrade/scripts/cp4a-deployment.sh -m upgradeOperator -n {self.ifix_project}'
            self.ifix_logger.logger.info(f'Executing the command {script} to upgrade the operator on the project name {self.ifix_project}')
            print(script)
            process = pexpect.spawn(script)
            print('pexpect.spawn(script)')

            print("######################### Checking CP4BA operator catalog pod ready or not in the project ##########################")
            operator_catalog = re.compile(r'.*' + re.escape('Checking CP4BA operator catalog pod ready or not in the project') + r'.*')
            process.expect(operator_catalog, timeout=1000)
            beforelog = process.before.decode('utf-8')
            self.ifix_logger.logger.info(beforelog)
            print(beforelog)
            afterlog = process.after.decode('utf-8')
            self.ifix_logger.logger.info(afterlog)
            print(afterlog)
            print("###########################################End#############################################")

            
            print("######################### Checking for IBM Cloud Pak foundational operator pod initializa##########################")
            pattern = re.compile(r'.*' + re.escape('Checking for IBM Cloud Pak foundational operator pod initializa') + r'.*')
            process.expect(pattern, timeout=1000)
            beforelog = process.before.decode('utf-8')
            self.ifix_logger.logger.info(beforelog)
            print(beforelog)
            afterlog = process.after.decode('utf-8')
            self.ifix_logger.logger.info(afterlog)
            print(afterlog)
            print("############################## End ##########################################################")
   
            print("######################### Completed to check the channel of subscription for CP4BA operators ##########################")
            pattern = re.compile(r'.*' + re.escape('Completed to check the channel of subscription for CP4BA operators') + r'.*')
            process.expect(pattern, timeout=1000)
            beforelog = process.before.decode('utf-8')
            self.ifix_logger.logger.info(beforelog)
            print(beforelog)
            afterlog = process.after.decode('utf-8')
            self.ifix_logger.logger.info(afterlog)
            print(afterlog)
            print("############################## End ##########################################################")

            #checking the status of the cp4ba deployment
            print("######################### cp4a-deployment.sh -m upgradeDeploymentStatus #########################")
            pattern = re.compile(r'.*' + re.escape('cp4a-deployment.sh -m upgradeDeploymentStatus') + r'.*')
            process.expect(pattern, timeout=1000)
            beforelog = process.before.decode('utf-8')
            self.ifix_logger.logger.info(beforelog)
            print(beforelog)
            afterlog = process.after.decode('utf-8')
            self.ifix_logger.logger.info(afterlog)
            print(afterlog)
            print("############################## End ##########################################################")
            process.expect(pexpect.EOF)

            #Checking the upgradeoperatorstatus
            upgradeOperatorStatus = f"./cp4a-deployment.sh -m upgradeOperatorStatus -n {self.ifix_project}"
            self.ifix_logger.logger.info(f"Checking the upgrade operator status using command {upgradeOperatorStatus}")
            print(f"Going to run ./cp4a-deployment.sh -m upgradeOperatorStatus -n {self.ifix_project} using the method ifix_upgradeOperatorStatus")
            operator_status = self.ifix_upgradeOperatorStatus()
            if operator_status:
                print("Upgrade Operator Status is successful.")
                self.ifix_logger.logger.info(f"Upgrade Operator Status is successful.")
            else:
                print("Upgrade Operator Status is failed.")
                self.ifix_logger.logger.error(f"Upgrade Operator Status is failed. Return False")
                return False

            #Checking the upgradeDeploymentStatus
            self.ifix_logger.logger.info(f"Checking the command available in the after log ./cp4a-deployment.sh -m upgradeDeploymentStatus -n {self.ifix_project}" )
            self.ifix_logger.logger.info(f"Going to run ./cp4a-deployment.sh -m upgradeDeploymentStatus -n {self.ifix_project}")
            deployment_status = self.ifix_upgradeDeploymentStatus()
            if deployment_status:
                print("Upgrade Deployment Status is successful.")
            else:
                print("Upgrade Deployment Status is failed.")
                self.ifix_logger.logger.error(f"Upgrade Deployment Status is failed.")
                return False
            process.expect(pexpect.EOF)
            return True
        except pexpect.exceptions.TIMEOUT as e :
            print("Timeout reached. Script execution took too long.")
            self.ifix_logger.logger.error(f"Timeout reached. Script execution took too long. With {e}")
            return False
        except Exception as e:
            self.ifix_logger.logger.error(f"Exception with {e}")
            return False

    def ifix_upgradeOperatorStatus(self):
        """
            Method name: ifix_upgradeOperatorStatus
            Description: Perform ifix upgrade operators status
            Parameters:
                self: object
            Returns:
                True/False
        """
        try:
            script = f'/opt/ifix_upgrade/scripts/cp4a-deployment.sh -m upgradeOperatorStatus -n {self.ifix_project}'
            self.ifix_logger.logger.info(script)
            process = pexpect.spawn(script)
            pattern = re.compile(r'.*' + re.escape('CP4BA operators upgraded successfully!') + r'.*')
            process.expect(pattern, timeout=600)
            beforelog = process.before.decode('utf-8')
            self.ifix_logger.logger.info(beforelog)
            print(beforelog)
            afterlog = process.after.decode('utf-8')
            self.ifix_logger.logger.info(afterlog)
            print(afterlog)
            process.expect(pexpect.EOF)
            return True
        except pexpect.exceptions.TIMEOUT as e:
            print("Timeout reached. Script execution took too long.")
            self.ifix_logger.logger.error(f"Timeout reached. Script execution took too long. {e}")
            return False
        except Exception as e:
            print(f"Timeout reached. Script execution took too long. {e}")
            self.ifix_logger.logger.error(f"Timeout reached. Script execution took too long. {e}")
            return False

    def ifix_upgradeDeploymentStatus(self):
        """
            Method name: ifix_upgradeDeploymentStatus
            Description: Perform ifix upgrade deployment status
            Parameters:
                self: object
            Returns:
                True/False
        """
        try:
            logfile = open('ifix_upgradeDeploymentStatus.log', 'wb')
            script = f'/opt/ifix_upgrade/scripts/cp4a-deployment.sh -m upgradeDeploymentStatus -n {self.ifix_project}'

            #Looping through the status to check the progress
            for count in range(0, 100):
                self.ifix_logger.logger.info(f'Using command {script} to check the deployment status')
                self.ifix_logger.logger.info(f'Total number of loop gone through {count}')
                process = pexpect.spawn(script)
                process.logfile = logfile

                pattern = re.compile(r'.*' + re.escape('zenService Progress') + r'.*')
                process.expect(pattern, timeout=600)
                beforelog = process.before.decode('utf-8')
                print(beforelog)
                self.ifix_logger.logger.info(beforelog)
                afterlog = process.after.decode('utf-8')
                print(afterlog)
                self.ifix_logger.logger.info(afterlog)

                pattern = re.compile(r'.*' + re.escape('BAI Service Upgrade Status') + r'.*')
                process.expect(pattern, timeout=7200)
                beforelog = process.before.decode('utf-8')
                print(beforelog)
                self.ifix_logger.logger.info(beforelog)
                afterlog = process.after.decode('utf-8')
                print(afterlog)
                self.ifix_logger.logger.info(afterlog)

                #Checking the status of the deployment
                matches = ["not ready", "in progress", "failed"]
                print(beforelog.lower())
                if any(x in beforelog.lower() for x in matches):
                    print('Upgrade deployment is in progress...')
                    self.ifix_logger.logger.info('Upgrade deployment is in progress...')
                    time.sleep(50)
                    process.close()
                else:
                    print('Upgrade deployment is Success...')
                    self.ifix_logger.logger.info('Upgrade deployment is Success...')
                    break
            
            return True
        except pexpect.exceptions.TIMEOUT:
            print("Timeout reached. Script execution took too long.")
            return False
        except Exception as e:
            return False

if __name__ == '__main__':
    project = sys.argv[1]
    upgrader = IfixUpgrade(project)
    operatorStatus = upgrader.ifix_upgradeOperator()
    if operatorStatus:
        print('Upgrade of the Operator is success.')
    else:
        print('Upgrade of the Operator is Failed.')
        sys.exit(-1)
