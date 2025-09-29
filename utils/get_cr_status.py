import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import subprocess
import yaml
import json
from tomlkit import parse
from utils.logger import logger

class DeploymentStatus():
    def __init__(self):
        """
        Method name: __init__
        Description: Initializes the class by fetching the config
        Parameters:
            None
        """
        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())

    def get_cr_content(self):
        """
        Method name: get_cr_content
        Description: Get CR from ocp cluster
        Parameters:
            None
        Returns:
            CR content / False (if failed to get CR)
        """
        logger.info("Getting CR from the cluster...")
        try:
            if self.config['configurations']['deployment_type'] == 'starter' or "21.0.3" in self.config['configurations']['build']:
                try:
                    CR_content = subprocess.check_output(["oc", "get", "ICP4ACluster", "-o", "yaml"], universal_newlines=True)
                except:
                    CR_content = subprocess.check_output(["oc", "get", "Content", "-o", "yaml"], universal_newlines=True)
            else:
                CR_content = subprocess.check_output(["oc", "get", "Content", "-o", "yaml"], universal_newlines=True)
            logger.info("CR fetched and returning.")
            return CR_content
        except Exception as e:
            logger.error(f"An exception occured during fetching the CR : {e}")
            return False
        
    def update_deployment_status(self, deployment_status):
        """
        Method name: update_deployment_status
        Description: Updates the status of each componnets from CR into a json file
        Parameters:
            deployment_status : status of the entire deployment
        Returns:
            None
        """
        status_file = f"{self.config['paths']['generated_reports_path']}/cp4ba_deployment_status.json"
        logger.info(f"Writing the deployment status to json file: {status_file}")
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        with open(status_file, 'w') as file:
            json.dump(deployment_status, file)

    def bai(self, status, component_status):
        """
        Method name: bai
        Description: Updates the status of bai into a dictionary
        Parameters:
            status : status of bai
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching BAI status")
        bai = status.get('components', {}).get('bai', {})
        bai_status = bai.get('bai_deploy_status')
        insights_status = bai.get('insightsEngine')
        component_status['bai']['bai_deploy_status'] = bai_status
        component_status['bai']['insightsEngine'] = insights_status
        bai_conditions = bai.get('conditions')
        if bai_conditions:
            message = bai_conditions.get('message')
            reason = bai_conditions.get('reason')
            if message:
                component_status['bai']['message'] = message
            if reason:
                component_status['bai']['reason'] = reason

    def cmis(self, status, component_status):
        """
        Method name: cmis
        Description: Updates the status of cmis into a dictionary
        Parameters:
            status : status of cmis
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching CMIS status")
        cmis = status['components']['cmis']
        deployment = cmis.get('cmisDeployment')
        route = cmis.get('cmisRoute')
        service = cmis.get('cmisService')
        storage = cmis.get('cmisStorage')
        zen = cmis.get('cmisZenIntegration')
        component_status['cmis']['cmisDeployment'] = deployment
        component_status['cmis']['cmisRoute'] = route
        component_status['cmis']['cmisService'] = service
        component_status['cmis']['cmisStorage'] = storage
        component_status['cmis']['cmisZenIntegration'] = zen
        cmis_conditions = cmis.get('conditions')
        if cmis_conditions:
            message = cmis_conditions.get('message')
            reason = cmis_conditions.get('reason')
            if message:
                component_status['cmis']['message'] = message
            if reason:
                component_status['cmis']['reason'] = reason

    def cpe(self, status, component_status):
        """
        Method name: cpe
        Description: Updates the status of cpe into a dictionary
        Parameters:
            status : status of cpe
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching CPE status")
        cpe = status['components']['cpe']
        deployment = cpe.get('cpeDeployment')
        route = cpe.get('cpeRoute')
        service = cpe.get('cpeService')
        storage = cpe.get('cpeStorage')
        zen = cpe.get('cpeZenIntegration')
        jdbc = cpe.get('cpeJDBCDriver')
        component_status['cpe']['cpeDeployment'] = deployment
        component_status['cpe']['cpeRoute'] = route
        component_status['cpe']['cpeService'] = service
        component_status['cpe']['cpeStorage'] = storage
        component_status['cpe']['cpeZenIntegration'] = zen
        component_status['cpe']['cpeJDBCDriver'] = jdbc
        cpe_conditions = cpe.get('conditions')
        if cpe_conditions:
            message = cpe_conditions.get('message')
            reason = cpe_conditions.get('reason')
            if message:
                component_status['cpe']['message'] = message
            if reason:
                component_status['cpe']['reason'] = reason

    def graphql(self, status, component_status):
        """
        Method name: graphql
        Description: Updates the status of graphql into a dictionary
        Parameters:
            status : status of graphql
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching GraphQL status")
        graphql = status['components']['graphql']
        deployment = graphql.get('graphqlDeployment')
        route = graphql.get('graphqlRoute')
        service = graphql.get('graphqlService')
        storage = graphql.get('graphqlStorage')
        component_status['graphql']['graphqlDeployment'] = deployment
        component_status['graphql']['graphqlRoute'] = route
        component_status['graphql']['graphqlService'] = service
        component_status['graphql']['graphqlStorage'] = storage
        graphql_conditions = graphql.get('conditions')
        if graphql_conditions:
            message = graphql_conditions.get('message')
            reason = graphql_conditions.get('reason')
            if message:
                component_status['graphql']['message'] = message
            if reason:
                component_status['graphql']['reason'] = reason

    def ier(self, status, component_status):
        """
        Method name: ier
        Description: Updates the status of ier into a dictionary
        Parameters:
            status : status of ier
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching IER status")
        ier = status['components']['ier']
        deployment = ier.get('ierDeployment')
        route = ier.get('ierRoute')
        service = ier.get('ierService')
        storage = ier.get('ierStorageCheck')
        component_status['ier']['ierDeployment'] = deployment
        component_status['ier']['ierRoute'] = route
        component_status['ier']['ierService'] = service
        component_status['ier']['ierStorageCheck'] = storage
        ier_conditions = ier.get('conditions')
        if ier_conditions:
            message = ier_conditions.get('message')
            reason = ier_conditions.get('reason')
            if message:
                component_status['ier']['message'] = message
            if reason:
                component_status['ier']['reason'] = reason

    def iccsap(self, status, component_status):
        """
        Method name: iccsap
        Description: Updates the status of iccsap into a dictionary
        Parameters:
            status : status of iccsap
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching ICCSAP status")
        iccsap = status['components']['iccsap']
        deployment = iccsap.get('iccsapDeployment')
        route = iccsap.get('iccsapRoute')
        service = iccsap.get('iccsapService')
        storage = iccsap.get('iccsapStorageCheck')
        component_status['iccsap']['iccsapDeployment'] = deployment
        component_status['iccsap']['iccsapRoute'] = route
        component_status['iccsap']['iccsapService'] = service
        component_status['iccsap']['iccsapStorageCheck'] = storage
        iccsap_conditions = iccsap.get('conditions')
        if iccsap_conditions:
            message = iccsap_conditions.get('message')
            reason = iccsap_conditions.get('reason')
            if message:
                component_status['iccsap']['message'] = message
            if reason:
                component_status['iccsap']['reason'] = reason

    def navigator(self, status, component_status):
        """
        Method name: navigator
        Description: Updates the status of navigator into a dictionary
        Parameters:
            status : status of navigator
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching Navigator status")
        navigator = status['components']['navigator']
        deployment = navigator.get('navigatorDeployment')
        service = navigator.get('navigatorService')
        storage = navigator.get('navigatorStorage')
        zen = navigator.get('navigatorZenIntegration')
        component_status['navigator']['navigatorDeployment'] = deployment
        component_status['navigator']['navigatorService'] = service
        component_status['navigator']['navigatorStorage'] = storage
        component_status['navigator']['navigatorZenIntegration'] = zen
        navigator_conditions = navigator.get('conditions')
        if navigator_conditions:
            message = navigator_conditions.get('message')
            reason = navigator_conditions.get('reason')
            if message:
                component_status['navigator']['message'] = message
            if reason:
                component_status['navigator']['reason'] = reason

    def tm(self, status, component_status):
        """
        Method name: tm
        Description: Updates the status of tm into a dictionary
        Parameters:
            status : status of tm
            component_status : status of each components
        Returns:
            None
        """
        logger.info("Fetching TM status")
        tm = status['components']['tm']
        deployment = tm.get('tmDeployment')
        route = tm.get('tmRoute')
        service = tm.get('tmService')
        storage = tm.get('tmStorage')
        component_status['tm']['tmDeployment'] = deployment
        component_status['tm']['tmRoute'] = route
        component_status['tm']['tmService'] = service
        component_status['tm']['tmStorage'] = storage
        tm_conditions = tm.get('conditions')
        if tm_conditions:
            message = tm_conditions.get('message')
            reason = tm_conditions.get('reason')
            if message:
                component_status['tm']['message'] = message
            if reason:
                component_status['tm']['reason'] = reason

    def check_cr(self):
        """
        Method name: check_cr_status
        Description: Get the status of the deployment from CR and updates them in a json file
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting fetching of CR status==========================================")
        cr = self.get_cr_content()
        component_status = {
            "bai": {},
            "cmis": {},
            "cpe": {},
            "graphql": {},
            "navigator": {},
            "ier": {},
            "iccsap": {},
            "tm": {}
        }
        if cr:
            cr_data = yaml.safe_load(cr)
            status = cr_data['items'][0]['status']
            # BAI
            self.bai(status, component_status)
            # CMIS
            self.cmis(status, component_status)
            # CPE
            self.cpe(status, component_status)
            # GRAPHQL
            self.graphql(status, component_status)
            # NAVIGATOR
            self.navigator(status, component_status)
            # IER
            self.ier(status, component_status)
            # ICCSAP
            self.iccsap(status, component_status)
            # TM
            self.tm(status, component_status)

            self.update_deployment_status(component_status)
        else:
            logger.error("Unable to retrieve CR.")
        logger.info("==========================================Completed fetching of CR status==========================================\n\n")


if __name__ == "__main__":
    deploy_status = DeploymentStatus()
    deploy_status.check_cr()
