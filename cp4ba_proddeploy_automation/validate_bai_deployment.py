import yaml
from yaml.loader import SafeLoader
import json
from utils.logs import * 

def validate():
    try:
        logger = DeploymentLogs()
        logger.logger.info('Checking deployment status....')
        with open('bai.yaml','r') as y_in, open('bai.json','w') as j_out:
            yaml_object = yaml.safe_load(y_in) 
            json.dump(yaml_object, j_out)
            j_out.close()
        bai = json.load(open("bai.json",'r'))
        item = bai['items'][0]
        status = item['status']['insightsEngineStatus']
        logger.logger.info(f'Deployment CR status: {status}')
        if str(status) != 'Ready':
            logger.logger.info('Deployment status is not Ready yet')
            return 0
        logger.logger.info('Deployment status is Ready')
        return 1
    except Exception as e:
        logger.logger.info(f'Error occured while checking the depoyment CR status {e}')
        return 0

if __name__ == '__main__':
    result = validate()
    print(result)