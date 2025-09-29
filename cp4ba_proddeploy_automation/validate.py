from datetime import datetime
import yaml
from yaml.loader import SafeLoader
import sys
import json
from utils.logs import *

def validate():
    """
    Name: validate
    Author: Irfan
    Desc: Verifying the optional and necessary components status
    Parameters: None
    Returns: 0/1 and prints detailed component statuses
    """
    try:
        logger = DeploymentLogs()
        logger.logger.info('Checking deployment status....')

        with open('content.yaml', 'r') as y_in:
            content = yaml.safe_load(y_in)

        items = content.get("items", [{}])[0]
        components = items.get("spec", {}).get("content_optional_components", {})
        components_check = items.get("status", {}).get("components", {})

        required_components = [name for name in ["bai", "cmis", "css", "iccsap", "ier", "tm"] if components.get(name)]

        if not required_components:
            logger.logger.info('No optional components require validation.')

        def print_and_log_status(name, status):
            readable = "Ready" if status == "Completed" else "Not Ready"
            message = f"{name.upper()} - {readable}"
            print(message)
            

        # BAI
        if "bai" in required_components:
            insights_engine = components_check.get("bai", {}).get("insightsEngine", "")
            if insights_engine == "Ready":
                bai_status = "Completed"
                logger.logger.info('BAI - Ready')
            else:
                bai_status = "Not Completed"
                logger.logger.info('BAI - Not Ready')
        else:
            bai_status = "Completed"
            logger.logger.info('BAI - Not Required')
        print_and_log_status("bai", bai_status)

        # Function to check status of each component
        def check_component(name):
            status = components_check.get(name, {}).get(f"{name}Deployment", "")
            if status == "Ready":
                logger.logger.info(f'{name.upper()} - Ready')
                result = "Completed"
            else:
                logger.logger.info(f'{name.upper()} - Not Ready')
                result = "Not Completed"

            print_and_log_status(name, result)
            return result

        # Check all optional components (except BAI)
        optional_statuses = {name: check_component(name) for name in required_components if name != "bai"}
        optional_statuses["bai"] = bai_status

        # Check necessary components
        def check_necessary_components():
            """
            Name: check_necessary_components
            Author: Irfan
            Desc: Checks the deployment status of necessary components (cpe, graphql, navigator)
            Returns: dict
            """
            necessary = ["cpe", "graphql", "navigator"]
            statuses = {}
            for name in necessary:
                status = components_check.get(name, {}).get(f"{name}Deployment", "")
                if status == "Ready":
                    logger.logger.info(f'{name.upper()} - Ready')
                    result = "Completed"
                else:
                    logger.logger.info(f'{name.upper()} - Not Ready')
                    result = "Not Completed"
                print_and_log_status(name, result)
                statuses[name] = result
            return statuses

        necessary_statuses = check_necessary_components()

        # Merge all statuses
        statuses = {**optional_statuses, **necessary_statuses}

        # Final check
        if all(status == "Completed" for status in statuses.values()):
            verification_status = items.get("status", {}).get("components", {}).get("content_verification", {}).get("conditions", {}).get("message", "")
            logger.logger.info(f"Verification message: {verification_status}")
            if verification_status == "Verification Done":
                logger.logger.info("Deployment SUCCESS")
                print("SUCCESS")
                return 1
            else:
                logger.logger.error("Deployment FAILED - Verification message not matched")
                print("FAILURE")
                return 0

        logger.logger.error("Deployment FAILED - One or more components not ready")
        print("FAILURE")
        return 0

    except Exception as e:
        logger.logger.error(f'Error occurred while checking deployment status: {e}')
        print("FAILURE")
        return 0

if __name__ == '__main__':
    result = validate()
    sys.exit(result)
