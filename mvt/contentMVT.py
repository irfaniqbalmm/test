import sys
import os
import json
import platform
import re
import subprocess
from datetime import date
from typing import Tuple

import urllib3
from tomlkit import parse

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kubernetes import client, config
from kubernetes.stream import stream

import mvt.parseMVT as parseMVT
import mvt.add_screenshots as add_screenshots
from utils.logger import logger

def get_operator_csv_version():
    """
    Method name : get_operator_csv_version
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description : Fetches the version of the Content or CP4A Operator from OpenShift.
    Returns:
        str: The version of the operator, or None if an error occurred.
    Raises:
        Exception: If an exception occurs while fetching the operator version.
    """
    try:
        if platform.system() == "Windows" :
            cmd = ["oc", "get", "csv", "--all-namespaces"]
        else : 
            cmd = ["oc", "get", "csv", "-A"]
        logger.info(f"Executing command : {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True) 
        if result.stderr :
            logger.error(f"An error occured while executing the command: {result.stderr}")
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "content-operator" in line or "cp4a-operator" in line:  
                    parts = line.split()
                    if len(parts) > 1:
                        namespace, csv_name = parts[0], parts[1]
                        version_cmd = f"oc get csv {csv_name} -n {namespace} -o jsonpath='{{.spec.version}}'"
                        version_result = subprocess.run(version_cmd, shell=True, capture_output=True, text=True)

                        if version_result.returncode == 0:
                            version = version_result.stdout.strip()
                            version = version.strip("'\"")
                            logger.info(f"Operator version  : {version}")
                            return version
                        else:
                            logger.error(f"Error fetching version for {csv_name}: {version_result.stderr}")
        else:
            logger.error(f"Error running the command: {result.stderr}")
        return None
    except Exception as e :
        logger.error(f'An exception occured while fetching the operator CSV version : {e}')

def get_version_from_operator(pod_obj, kubernetes_client, command, namespace, alternate_version_component=None):
    """
    Method name  :  get_version_from_operator
    Description  :  Returns the version details of a pod by running a command
    Parameters   :  
        pod_obj                     : Component pod object to run MVT on
        kubernetes_client           : Kubernetes client instance
        command                     : Command to be executed
        namespace                   : Namespace of deployment
        alternate_version_component : Alternate version components, defaults to None
    Return       :  Version
    """
    version = ""
    try:
        if "cpe" in pod_obj.metadata.name and ("21.0.3" not in release_version) and "starter" not in deployment_type.lower():
            try :
                version = stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace, container='content-cpe-deploy',
                            command=command, stderr=True, stdin=False, stdout=True, tty=False)
            except :
                version = stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace,
                            command=command, stderr=True, stdin=False, stdout=True, tty=False)
        elif alternate_version_component == 'flink':
            version = stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace, container='flink-kubernetes-operator',
                            command=command, stderr=True, stdin=False, stdout=True, tty=False)
        else :
            version = stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace,
                            command=command, stderr=True, stdin=False, stdout=True, tty=False)
    except Exception as e:
        logger.error(f"An exception has occured while fetching version from operator : {e}")
    return version

def k8s_optional_component_MVT(kubernetes_client, pod_obj, namespace, alternate_version_component=None) -> str:
    """
    Method name  :  k8s_optional_component_MVT
    Description  :  Returns the string output from the MVT test, which includes the version.txt, the Websphere version if applicable,
                    the java version, any product licenses, swidtags if applicable, and the product annotations from a given component pod
    Parameters   :  
        pod_obj  :  Component pod object to run MVT on
        namespace:  namespace of deployment
    Return       :  Formatted MVT string
    """
    try :
        retval = 'Component:\n'
        if alternate_version_component == 'Operator':
            retval += pod_obj.spec.service_account_name + '\n\n'
            operator_version = get_operator_csv_version()
            if operator_version :
                retval += f"version.txt: \nVersion: {operator_version}\n"
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ibm/version.txt']
        elif alternate_version_component in ['cpfs','flink','os','kafka'] :
            retval += pod_obj.metadata.labels.get('app.kubernetes.io/name') + '\n\n' 
        elif alternate_version_component == "zen" :
            retval += pod_obj.metadata.labels.get('app.kubernetes.io/name') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ansible/latest_release_version.yaml']   
        elif "iccsap" in str(pod_obj.metadata.labels.get('app')) :
            retval += pod_obj.metadata.labels.get('app') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/IBM/imageVersion.txt']
        elif "insights-engine" in str(pod_obj.metadata.labels.get('name')) :
            retval += pod_obj.metadata.labels.get('name') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ibm/version.txt']
        elif alternate_version_component == 'mongo':
            retval += pod_obj.metadata.labels.get('app') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'mongod --version']
        elif alternate_version_component == 'gitea':
            retval += pod_obj.metadata.labels.get('app') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'gitea -v']
        elif alternate_version_component == 'gitgateway':
            retval += pod_obj.metadata.labels.get('app.kubernetes.io/name') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'curl -k https://icp4adeploy-gitgateway-svc:9443/git-service/about']
        elif alternate_version_component == 'content_analyzer':
            retval += pod_obj.metadata.labels.get('app') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ibm/sp-version.json']
        elif alternate_version_component == 'home_versionInfo_appkubernetesio':
            retval += pod_obj.metadata.labels.get('app.kubernetes.io/name') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /home/versionInfo.txt']
        elif alternate_version_component == 'home_versionInfo_app_label':
            retval += pod_obj.metadata.labels.get('app') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /home/versionInfo.txt']
        elif alternate_version_component == 'home_versionInfo_instance_components':
            retval += pod_obj.metadata.labels.get('app.kubernetes.io/name') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /usr/home/solution-server/version.txt']
        elif alternate_version_component == 'ContentOperator':
            retval += pod_obj.spec.service_account_name + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ibm/version.txt']
        elif alternate_version_component == 'DPEOperator':
            retval += pod_obj.spec.service_account_name + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ibm/dpe-version.json']
        else:
            retval += pod_obj.metadata.labels.get('app') + '\n\n'
            command = [
                '/bin/sh',
                '-c',
                'cat /opt/ibm/version.txt']
        retval += 'version.txt:\n'
        if alternate_version_component in ['cpfs'] :
            retval += str(pod_obj.metadata.annotations.get('operatorVersion')) + '\n\n'
        elif alternate_version_component == 'os' :
            op = pod_obj.metadata.annotations.get('operatorframework.io/properties')
            data = json.loads(op)
            version = next((prop["value"]["version"] for prop in data["properties"] if prop["type"] == "olm.package"), None)
            retval += str(version)
        elif alternate_version_component == 'flink' :
            retval += str(pod_obj.metadata.annotations.get('productVersion')) + '\n\n'
        elif alternate_version_component == 'kafka' :
            retval += str(pod_obj.metadata.annotations.get('strimzi.io/kafka-version')) + '\n\n'
        elif alternate_version_component == 'mongo' :
            retval += stream(kubernetes_client.connect_post_namespaced_pod_exec,pod_obj.metadata.name,namespace,container='icp4adeploy-mongo-deploy',command=command,stderr=True,stdin=False,stdout=True,tty=False).rstrip('\n') + '\n\n'
        else :
            if "cpe" in str(pod_obj.metadata.name) :
                try :
                    retval += stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace, container='content-cpe-deploy', command=command, stderr=True, stdin=False, stdout=True, tty=False).rstrip('\n') + '\n\n'
                except :
                    retval += stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace, command=command, stderr=True, stdin=False, stdout=True, tty=False).rstrip('\n') + '\n\n'
            else :
                retval += stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace, command=command, stderr=True, stdin=False, stdout=True, tty=False).rstrip('\n') + '\n\n'
        # Liberty Version
        retval += 'Liberty Version:\n'
        command = [
            '/bin/sh',
            '-c',
            '/opt/ibm/wlp/bin/server version']
        try : 
            websphere_version = get_version_from_operator(pod_obj, kubernetes_client, command, namespace, alternate_version_component)
            if '/bin/sh: /opt/ibm/wlp/bin/server: No such file or directory' in websphere_version:
                retval += 'No Websphere version found \n\n'
            else:
                retval += websphere_version + '\n'
        except :
            retval += 'No Websphere version found \n\n'
        # Java version
        retval += 'Java Version:\n'
        command = [
            '/bin/sh',
            '-c',
            'java -version']
        try :
            java_version = get_version_from_operator(pod_obj, kubernetes_client, command, namespace, alternate_version_component)
            if not java_version or 'java: not found' in java_version or 'java: command not found' in java_version:
                retval += 'No java version found \n\n'
            else:
                retval += java_version + '\n'
        except :
            retval += 'No java version found \n\n'
        # UBI version
        retval += 'UBI Version:\n'
        command = [
            '/bin/sh',
            '-c',
            'cat /etc/redhat-release']
        try :
            ubi_version = get_version_from_operator(pod_obj, kubernetes_client, command, namespace, alternate_version_component)
            if 'Red Hat Enterprise Linux release' in ubi_version:
                retval += ubi_version + '\n'
            else:
                retval += 'No UBI version found \n\n'
        except :
            retval += 'No UBI version found \n\n'
        # Licenses
        retval += 'Licenses:\n'
        command = [
            '/bin/sh',
            '-c',
            'ls /licenses/ -la']
        try :
            retval += stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace,
                            command=command, stderr=True, stdin=False, stdout=True, tty=False) + '\n'
        except : 
            retval += 'No licenses found \n\n'
        retval += 'Swidtags:\n'
        command = [
            '/bin/sh',
            '-c',
            'ls /opt/ibm/swidtag/']
        try:
            swidtags = stream(kubernetes_client.connect_post_namespaced_pod_exec, pod_obj.metadata.name, namespace,
                            command=command, stderr=True, stdin=False, stdout=True, tty=False)
            if 'ls: cannot access \'/opt/ibm/swidtag/\': No such file or directory' in swidtags:
                retval += 'No swidtags found \n\n'
            else:
                retval += swidtags
        except :
            retval += 'No swidtags found \n\n'
        retval += 'Annotations:\n'
        if pod_obj.metadata.annotations.get('productVersion') is not None:
            retval += 'productVersion: ' + pod_obj.metadata.annotations.get('productVersion') + '\n\n'
        else:
            retval += 'productVersion: ' + 'N/A' + '\n'
        if pod_obj.metadata.annotations.get('productID') is not None:
            retval += 'productID: ' + pod_obj.metadata.annotations.get('productID') + '\n\n'
        else:
            retval += 'productID: ' + 'N/A' + '\n'
        if pod_obj.metadata.annotations.get('productName') is not None:
            retval += 'productName: ' + pod_obj.metadata.annotations.get('productName') + '\n\n'
        else:
            retval += 'productName: ' + 'N/A' + '\n'
        retval += '\n-----------------------------------------------------------------------------------------------------------------------\n'
        logger.info(f"Returning value : \n {retval}")
        return retval
    except Exception as e :
        logger.exception(f"An exception occured while fetching version : {e}")

def project_MVT(project, generated_reports_path, output_to_txt=False) -> Tuple[str, str, str]:
    """
    Method name         :   k8s_optional_component_MVT
    Description         :   Returns the MVT string by concatenating optional_component_string(pod_obj) called upon each CONTENT component pod in
                            the openshift project specified by the project parameter. Outputs to a txt file if the output_to_txt parameter is
                            set to true.
    Parameters          :  
        output_to_txt   :   boolean to output to a txt file, defaults to false
        project         :   The project namespace string to run MVT on
    Return              :   string
    """
    logger.info('------------------------ Getting versions from project: ' + project +' ------------------------')
    config.load_kube_config()
    v1 = client.CoreV1Api()
    retval = ''
    retval += ('Project: ' + project + '\n') 
    
    opt_ibm_version_components = {
        'operator': False,
        'content-cpe-deploy': False,
        'content-graphql-deploy': False,
        'content-navigator-deploy': False,
        'content-css-deploy-1': False,
        'content-cmis-deploy': False,
        'content-es-deploy': False,
        'content-tm-deploy': False,
        'content-ier-deploy': False,
        'content-iccsap-deploy': False,
        'ibm-insights-engine-operator': False,
        'ibm-bai-insights-engine-operator': False,
        'ibm-common-service-operator': False,
        'flink-kubernetes-operator': False,
        'ibm-zen-operator': False,
        'ibm-elasticsearch-operator': False,
        'ibm-opensearch-operator': False,
        'iaf-system-kafka': False,
        'icp4adeploy-cpe-deploy': False,
        'icp4adeploy-graphql-deploy': False,
        'icp4adeploy-navigator-deploy': False,
        'icp4adeploy-css-deploy-1': False,
        'icp4adeploy-cmis-deploy': False,
        'icp4adeploy-es-deploy': False,
        'icp4adeploy-tm-deploy': False,
        'icp4adeploy-ier-deploy': False,
        'icp4adeploy-iccsap-deploy': False,
        'icp4adeploy-cpds-deploy': False,
        'icp4adeploy-cdra-deploy': False,
        'icp4adeploy-cds-deploy': False,
        'icp4a-cp4a-operator': False,
        'icp4a-dpe-operator': False,
        'icp4a-content-operator': False

    }

    home_versionInfo_appkubernetesio_components = {
        'bastudio': False,

    }

    home_versionInfo_instance_components = {
        'icp4adeploy-workspace-aae': False,
        'icp4adeploy-pbk': False

    }
    home_versionInfo_app_label_components = {
        'icp4adeploy-viewone-deploy': False,
    }

    content_analyzer_components = {
        'ibm-dba-aca-prod': False,
        'icp4adeploy-spbackend': False,
        'icp4adeploy-classifyprocess-classify': False,
        'icp4adeploy-deep-learning': False,
        'icp4adeploy-webhook': False,
        'icp4adeploy-rabbitmq-ha': False,
        'icp4adeploy-ocr-extraction': False,
        'icp4adeploy-postprocessing': False,
        'icp4adeploy-processing-extraction': False,
        'icp4adeploy-setup': False,
        'icp4adeploy-natural-language-extractor': False,

    }

    git_components = {
        'icp4adeploy-gitea-deploy': False,
        'icp4adeploy-gitgateway-deploy': False
    }

    ret = v1.list_namespaced_pod(project, watch=False)

    # Sort the pods: Place "operator" pods first, then sort alphabetically
    sorted_pods = sorted(
        ret.items,
        key=lambda pod: (
            not any(op in pod.metadata.name for op in ["content-operator", "cp4a-operator"]),
            not ("ibm-bai-insights-engine-operator" in pod.metadata.name and all(op not in pod.metadata.name for op in ["content-operator", "cp4a-operator"])),
            pod.metadata.name
        )
    )

    for pod in sorted_pods:
        if pod.status.phase != "Running" and pod.status.phase != "Completed" and pod.metadata.labels.get('app.kubernetes.io/name') in opt_ibm_version_components.keys():
            logger.error(f"\n{pod.metadata.name} is not Runnning!")
            logger.error(f"STATUS of pod : {pod.status.phase}")
        elif pod.spec.service_account_name in ['ibm-content-operator', 'ibm-cp4a-operator'] and not opt_ibm_version_components['operator']:
            logger.info(f"Fetching version of operator, pod name  : {pod.spec.service_account_name}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'Operator')
            opt_ibm_version_components['operator'] = True
            if pod.spec.service_account_name in ['ibm-cp4a-operator']:
                CONTENT = False
        elif pod.spec.service_account_name in ['ibm-cp4a-content-operator'] and not \
                opt_ibm_version_components['icp4a-content-operator']:
            retval += k8s_optional_component_MVT(v1, pod, project, 'ContentOperator')
            opt_ibm_version_components['icp4a-content-operator'] = True
            operator_found = True
        elif pod.spec.service_account_name in ['ibm-cp4a-dpe-operator'] and not \
                opt_ibm_version_components['icp4a-dpe-operator']:
            retval += k8s_optional_component_MVT(v1, pod, project, 'DPEOperator')
            opt_ibm_version_components['icp4a-dpe-operator'] = True
            operator_found = True
        elif pod.metadata.labels.get('app.kubernetes.io/name') in opt_ibm_version_components.keys() and pod.metadata.labels.get('app.kubernetes.io/name') in ['ibm-common-service-operator']:
            logger.info(f"Fetching version of common services, pod name : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'cpfs')
            opt_ibm_version_components['ibm-common-service-operator'] = True
        elif pod.metadata.labels.get('app.kubernetes.io/name') in opt_ibm_version_components.keys() and pod.metadata.labels.get('app.kubernetes.io/name') in ['flink-kubernetes-operator']:
            logger.info(f"Fetching version of flink, pod name  : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'flink')
            opt_ibm_version_components['flink-kubernetes-operator'] = True
        elif "elasticsearch-operator" in str(pod.metadata.labels.get('app.kubernetes.io/name')) :
            logger.info(f"Fetching version of opensearch, pod name : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'os')
            opt_ibm_version_components['ibm-elasticsearch-operator'] = True
        elif "opensearch-operator" in str(pod.metadata.labels.get('app.kubernetes.io/name')) :
            logger.info(f"Fetching version of opensearch, pod name : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'os')
            opt_ibm_version_components['ibm-opensearch-operator'] = True
        elif ("kafka" == str(pod.metadata.labels.get('app.kubernetes.io/name'))) and (opt_ibm_version_components['iaf-system-kafka'] == False):
            logger.info(f"Fetching version of kafka, pod name : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'kafka')
            opt_ibm_version_components['iaf-system-kafka'] = True
        elif pod.metadata.labels.get('app.kubernetes.io/name') in opt_ibm_version_components.keys() and pod.metadata.labels.get('app.kubernetes.io/name') in ['ibm-zen-operator']:
            logger.info(f"Fetching version of zen operator, pod name : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'zen')
            opt_ibm_version_components['ibm-zen-operator'] = True
        elif pod.metadata.labels.get('app.kubernetes.io/name') in opt_ibm_version_components.keys() and not opt_ibm_version_components[pod.metadata.labels.get('app.kubernetes.io/name')]:
            logger.info(f"Fetching version pod : {pod.metadata.labels.get('app.kubernetes.io/name')}")
            retval += (k8s_optional_component_MVT(v1, pod, project))
            opt_ibm_version_components[pod.metadata.labels.get('app.kubernetes.io/name')] = True
        elif pod.metadata.labels.get('app') == 'icp4adeploy-mongo-deploy':
            logger.info(f"Fetching version of mongo, pod name : {pod.metadata.labels.get('app')}")
            retval += k8s_optional_component_MVT(v1, pod, project, 'mongo')
        elif pod.metadata.labels.get('app') == 'icp4adeploy-gitea-deploy' and not git_components[
            'icp4adeploy-gitea-deploy']:
            retval += k8s_optional_component_MVT(v1, pod, project, 'gitea')
            git_components['icp4adeploy-gitea-deploy'] = True
        elif pod.metadata.labels.get('app') == 'icp4adeploy-gitgateway-deploy' and not git_components[
            'icp4adeploy-gitgateway-deploy']:
            retval += k8s_optional_component_MVT(v1, pod, project, 'gitgateway')
            git_components['icp4adeploy-gitgateway-deploy'] = True
        elif str(pod.metadata.labels.get('name')) in ["ibm-insights-engine-operator", "ibm-bai-insights-engine-operator"]: 
            logger.info(f"Fetching version of insights engine, pod name : {str(pod.metadata.labels.get('name'))}")
            retval += (k8s_optional_component_MVT(v1, pod, project))
            opt_ibm_version_components['ibm-insights-engine-operator'] = True
            opt_ibm_version_components['ibm-bai-insights-engine-operator'] = True
        elif (pod.metadata.labels.get('app') in home_versionInfo_app_label_components.keys()
              and not home_versionInfo_app_label_components[pod.metadata.labels.get('app')]):
            retval += (k8s_optional_component_MVT(v1, pod, project))
            home_versionInfo_app_label_components[pod.metadata.labels.get('app')] = True

        elif (pod.metadata.labels.get('app.kubernetes.io/instance') in home_versionInfo_instance_components.keys() \
            and pod.metadata.labels.get('app.kubernetes.io/component') == 'deployment' \
            and not home_versionInfo_instance_components[pod.metadata.labels.get('app.kubernetes.io/instance')]):
            retval += (k8s_optional_component_MVT(v1, pod, project, 'home_versionInfo_instance_components'))
            home_versionInfo_instance_components[pod.metadata.labels.get('app.kubernetes.io/instance')] = True

        elif pod.metadata.labels.get('app.kubernetes.io/name') in home_versionInfo_appkubernetesio_components \
                and pod.metadata.labels.get('app.kubernetes.io/component') == 'deployment' \
                and not home_versionInfo_appkubernetesio_components[pod.metadata.labels.get('app.kubernetes.io/name')]:
            retval += (k8s_optional_component_MVT(v1, pod, project, 'home_versionInfo_appkubernetesio'))
            home_versionInfo_appkubernetesio_components[pod.metadata.labels.get('app.kubernetes.io/component')] = True

        elif pod.metadata.labels.get('app') in content_analyzer_components.keys() and not content_analyzer_components[
            pod.metadata.labels.get('app')]:
            retval += (k8s_optional_component_MVT(v1, pod, project, 'content_analyzer'))
            content_analyzer_components[pod.metadata.labels.get('app')] = True

    if output_to_txt:
        logger.info("Writing MVT details to text file.")
        file_path = os.path.join(generated_reports_path, f"{project}_MVT.txt")
        with open(file_path, 'w') as output:
            output.write(retval)
        output.close()
    return retval

def mvt_runner(product, output_to_txt=False):
    """
    Method name         :   mvt_runner
    Description         :   Executes the MVT on the given product
    Parameters          :  
        output_to_txt   :   boolean to output to a txt file, defaults to false
        product         :   The product for which MVT is executed
    Return              :   None
    """
    logger.info("==========================================Starting MVT execution==========================================")
    urllib3.disable_warnings()
    try:
        global deployment_type, release_version
        # Handling different product before MVT execution
        config_file = None
        is_content = False
        if product.upper() in ["CP4BA", "ADP"]:
            config_file = "./inputs/config.toml"
            if product.upper() == "ADP":
                product_text = "ADP"
            else:
                is_content = True
                product_text = "CP4BA Content Pattern"
        elif product.upper() == "BAIS":
            config_file = "./BAI_BVT/resources/config.toml"
            product_text = "BAI Standalone"

        # Reading project details from config file
        with open(config_file, "r") as file :
            input_data = parse(file.read())

        project_namespace = input_data['configurations']['project_name']
        deployment_type = input_data['configurations']['deployment_type']
        cluster = input_data['configurations']['cluster']
        gen_report_path = input_data['paths']['generated_reports_path']
        release_version = input_data['configurations']['build']

        # Getting projects
        projects = []
        possible_suffixes = ["operands", "pods"]
        for suffix in possible_suffixes:
            if suffix in project_namespace:
                operator_namespace = re.sub(fr'[-_]?{suffix}$', '', project_namespace)
                projects.append(operator_namespace)
        projects.append(project_namespace)
        logger.info(f"Project(s): {projects}\n")

        deployment_type_text = f'{product_text} {deployment_type} Deployment'
        logger.info(f"Deployment type : {deployment_type_text}")
        logger.info(f"Build : {release_version}")
        logger.info(f"MVT report will be generated in: {gen_report_path}")

        returns = ""
        for namespace in projects:
            mvt_return = project_MVT(namespace, gen_report_path, output_to_txt)
            returns += mvt_return

        mvt_return = (returns, release_version, deployment_type_text)
        logger.info(f"MVT return is: {mvt_return}")

        df = parseMVT.content2df(mvt_return[0])
        logger.info(f"Data frame returned: \n{df}")
        today = date.today()
        logger.info("Converting df to csv.")
        with open(f'{gen_report_path}/{project_namespace}_MVT.csv', 'w', newline='\n', encoding='utf-8') as file:
            df.to_csv(file, index=False)
        logger.info("Converting df to pdf.")
        parseMVT.df2pdf(product, mvt_return[1], mvt_return[2], today, df, gen_report_path, projects, deployment_type, cluster)
        if is_content:
            add_screenshots.add_screenshots_to_pdf(product)
        logger.info("MVT Execution Completed!")
    except Exception as e:
        logger.error(f"An exception occurred during MVT execution : {e}")


if __name__ == '__main__':
    # TESTER CODE
    product = "ADP"
    mvt_runner(product, True)
