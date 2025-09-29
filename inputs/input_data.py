import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import configparser
import json
from tomlkit import parse,dumps
import utils.login as login
from utils.get_cr_config import get_db_ldap
import utils.oc_version as oc_version
from  utils.logger import logger


def initialize_input_data(): 

    logger.info("==========================================Starting execution of input_data.py==========================================")
    # Reading config.toml file
    logger.info("Reading config.toml file into input_data variable ...")
    try : 
        with open("./inputs/config.toml","r") as file : 
            input_data = parse(file.read())
    except Exception as e :
        logger.critical(f"An exception occured during reading the toml file : {e}")

    # Configurations from config.ini
    logger.info("Reading configurations from config.ini file")
    config = configparser.ConfigParser()
    config.read('config.ini')
    project_name = config.get('configurations', 'project_name')
    build = config.get('configurations', 'build')
    ifix_version = config.get('configurations', 'ifix_version')
    cluster = config.get('configurations', 'cluster')
    deployment_type = config.get('configurations', 'deployment_type')
    DB,LDAP = get_db_ldap(deployment_type,build)
    user = config.get('configurations','user')
    oc_verify = config.get('configurations','oc_verify')
    git_user = config.get('configurations','git_user')
    git_pwd = config.get('configurations','git_pwd')
    quick_kube_pwd = config.get('configurations','quick_burn_pwd',fallback=None)
    quick_fyre_pwd = config.get('configurations','quick_fyre_pwd',fallback=None)
    multildap = config.get('configurations','multildap')
    
    #fetching OCP version
    ocp_version = oc_version.fetch_oc_version()
    logger.info("Fetched OCP version.")

    # configurations
    logger.info("Setting configurations")
    input_data['configurations']['project_name'] = project_name
    input_data['configurations']['build'] = build
    input_data['configurations']['ifix_version'] = ifix_version
    input_data['configurations']['cluster'] = cluster
    input_data['configurations']['deployment_type'] = deployment_type
    input_data['configurations']['DB'] = DB
    input_data['configurations']['LDAP'] = LDAP
    input_data['configurations']['user'] = user
    input_data['configurations']['oc_verify'] = oc_verify
    input_data['configurations']['ocp_version'] = ocp_version
    input_data['configurations']['multildap'] = multildap

    # git
    logger.info("Setting git configurations")
    input_data['git']['git_user'] = git_user
    input_data['git']['git_pwd'] = git_pwd

    # cmod
    logger.info("Setting cmod configurations")
    input_data['cmod']['cmodrepositoryname'] = 'CMODAutomationRepo' #replace with another name if you are running the BVT for thr second time
    input_data['cmod']['cmod_desktop_name'] = 'CMODAutomationDesktop' #replace with another name if you are running the BVT for thr second time
    input_data['cmod']['u_cmodrepositoryname'] = 'CMODRepoAutomationUp'
    input_data['cmod']['u_cmod_desktop_name'] =  'CMODAutomationDesktopUp'
    input_data['cmod']['cmodreposervname'] = 'lilac1.fyre.ibm.com'
    input_data['cmod']['cmodusername'] = 'odadmin'
    input_data['cmod']['cmodpassword'] = 'Password1'
    
    #cm8
    logger.info("Setting cm8 configurations")
    input_data['cm8']['cm8repositoryname'] = 'CM8AutomationRepo' #replace with another name if you are running the BVT for thr second time
    input_data['cm8']['cm8_desktop_name'] = 'CM8AutomationDesktop' #replace with another name if you are running the BVT for thr second time
    input_data['cm8']['u_cm8repositoryname'] = 'CM8AutomationRepoUp'
    input_data['cm8']['u_cm8_desktop_name'] = 'CM8AutomationDesktopUp'
    input_data['cm8']['cm8_server'] = 'cm86server1'
    input_data['cm8']['cm8username'] = 'icmadmin'
    input_data['cm8']['cm8password'] = 'Password1'

    #App login credentials
    if user != 'admin' :
        if "MSAD" in LDAP:
            username = "testa1ecmuser01"
            password = "Filenet1Filenet1!"
        else :
            username = "group0001usr0002"
            password = "passw0rd"
    else :
        credentials = login.get_credentials(project_name)
        if multildap.lower() == "true":
            username,password = credentials.get("ldap2Username"),credentials.get("ldap2Password")
        else:
            username,password = credentials.get("appLoginUsername"),credentials.get("appLoginPassword")
    logger.info(f"Applogin credentials used : {username}/{password}")

    # paths
    base_path = os.getcwd() #Expected location is ../Cp4ba-Automation/CP4BA_Package/
    screenshot_path = os.path.join(base_path, 'screenshots')
    download_path = os.path.join(base_path, 'downloads')
    reports = os.path.join(base_path, 'reports')
    generated_reports_path = os.path.join(reports,'generated_reports')
    report_path = os.path.join(generated_reports_path, 'bvt_report.html')
    report_template_path = os.path.join(reports, 'templates', 'template.html')
    cluster_file = os.path.join(base_path, 'clusters.json')

    EXPECTED_DIR = os.path.normpath("/Cp4ba-Automation/CP4BA_Package/")
    if EXPECTED_DIR not in (os.path.normpath(base_path)) :
        logger.error("This script is not executed from the expected base directory.")
        logger.error(f"Current directory : {base_path}")
        logger.error(f"Expected directory : {EXPECTED_DIR}")
        logger.critical("Exiting BVT execution!!!")
        exit()
    else:
        logger.info(f"Running from directory : {base_path}")
    
    if quick_kube_pwd: 
        infra_node_pwd = quick_fyre_pwd
        kube_Admin_password = quick_kube_pwd
    else :
        f = open(f'{cluster_file}')
        cluster_data = json.load(f)
        cluster_found = 0
        for i in cluster_data :
            if str(i).lower() == cluster.lower() :
                cluster_found = 1
                infra_node_pwd = cluster_data[i]['root_pwd']
                kube_Admin_password = cluster_data[i]['kube_pwd']
        if cluster_found == 0 :
            logger.error("Add cluster details to cluster.json file!")
            logger.critical("Exiting BVT execution!!")
            exit()

    # credentials
    logger.info("Setting credentials")
    input_data['credentials']['infra_node_uname'] = 'root'
    input_data['credentials']['infra_node_pwd'] = infra_node_pwd
    input_data['credentials']['kube_admin_username'] = 'kubeadmin'
    input_data['credentials']['kube_admin_password'] = kube_Admin_password
    input_data['credentials']['app_login_username'] = username
    input_data['credentials']['app_login_password'] = password

    # ocp paths
    ocp = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/operators.coreos.com~v1alpha1~ClusterServiceVersion'
    config_maps = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/core~v1~ConfigMap?orderBy=desc&sortBy=Created'
    secrets = f'https://console-openshift-console.apps.{cluster}.cp.fyre.ibm.com/k8s/ns/{project_name}/secrets/secret_name'

    # paths
    logger.info("Setting paths")
    input_data['paths']['base_path'] = base_path
    input_data['paths']['screenshot_path'] = screenshot_path
    input_data['paths']['download_path'] = download_path
    input_data['paths']['reports'] = reports
    input_data['paths']['generated_reports_path'] = generated_reports_path
    input_data['paths']['report_path'] = report_path
    input_data['paths']['report_template_path'] = report_template_path
    input_data['paths']['cluster_file'] = cluster_file

    #ocp_paths
    logger.info("Setting ocp_paths")
    input_data['ocp_paths']['ocp'] = ocp
    input_data['ocp_paths']['config_maps'] = config_maps
    input_data['ocp_paths']['secrets'] = secrets

    logger.info("Writing required details for oc operations to testdata.config file")
    current_dir = os.getcwd()
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(current_dir + '/oc_operations/config/testdata.config')
    parser['INPUT']['namespace'] = project_name
    parser['INPUT']['cluster_name'] = cluster
    parser['INPUT']['cluster_password'] = kube_Admin_password
    parser['EXPECTED_RESULTS']['content_app_version'] = f"'{build}'"
    with open(f'{current_dir}/oc_operations/config/testdata.config', 'w') as configfile:
        parser.write(configfile)

    #graphql
    if deployment_type == 'post-upgrade' :
        graphql_folder_name = "Test_folder_upgrade"
        if user != "admin" :
            graphql_folder_name = "Test_folder_non_admin_upgrade"
    else :
        graphql_folder_name = "Test_folder_auto"
        if user != "admin" :
            graphql_folder_name = "Test_folder_non_admin"
    logger.info(f"Setting Graphql test folder name as : {graphql_folder_name}")

    graphqlcmd1 = '''{
    _apiInfo(repositoryIdentifier: "OS01") {
        buildDate
        implementationVersion
        buildNumber
        productVersion
        implementationTitle
        cpeInfo {
            cpeURL
            cpeUser
            repositoryName
        }
    }
}'''
    graphqlcmd2 = f'''
mutation {{
    createFolder (
        repositoryIdentifier: "OS01"
        folderProperties: {{
            name: "{graphql_folder_name}"
        }}
    ) 
    {{
        className
        id
        name
        creator
        dateCreated
        lastModifier
        dateLastModified
        pathName
        properties(includes: ["IsHiddenContainer", "DateCreated", "Creator"]) {{
            id
            label
            type
            cardinality
            value
        }}
    }}
}}'''
    graphqlcmd3 = f'''
mutation {{
    createDocument(repositoryIdentifier: "OS01"
    classIdentifier: "Document"
    documentProperties: {{
        name: "test_title"
    }}
    fileInFolderIdentifier: "/{graphql_folder_name}"
    checkinAction: {{autoClassify: false, checkinMinorVersion: false}}) {{
        className
        id
        name
        isReserved
        isCurrentVersion
        isFrozenVersion
        isVersioningEnabled
        majorVersionNumber
        minorVersionNumber
        versionStatus
        reservationType
        cmIsMarkedForDeletion
        updateSequenceNumber
        accessAllowed
        contentElementsPresent
        contentSize
        mimeType
        dateContentLastAccessed
        contentRetentionDate
        currentState
        isInExceptionState
        classificationStatus
        indexationId
        cmIndexingFailureCode
        compoundDocumentState
        cmRetentionDate
        properties(includes: ["DocumentTitle"]) {{
            id
            label
            type
            cardinality
            value
        }}
    }}
}}'''
    s_graphqlcmd1 = '''{
    _apiInfo(repositoryIdentifier: "CONTENT") {
        buildDate
        implementationVersion
        buildNumber
        productVersion
        implementationTitle
        cpeInfo {
            cpeURL
            cpeUser
            repositoryName
        }
    }
}'''
    s_graphqlcmd2 = f'''
mutation {{
    createFolder (
        repositoryIdentifier: "CONTENT"
        folderProperties: {{
            name: "{graphql_folder_name}"
        }}
    ) 
    {{
        className
        id
        name
        creator
        dateCreated
        lastModifier
        dateLastModified
        pathName
        properties(includes: ["IsHiddenContainer", "DateCreated", "Creator"]) {{
            id
            label
            type
            cardinality
            value
        }}
    }}
}}'''

    s_graphqlcmd3 = f'''
mutation {{
    createDocument(repositoryIdentifier: "CONTENT"
    classIdentifier: "Document"
    documentProperties: {{
        name: "test_title"
    }}
    fileInFolderIdentifier: "/{graphql_folder_name}"
    checkinAction: {{autoClassify: false, checkinMinorVersion: false}}) {{
        className
        id
        name
        isReserved
        isCurrentVersion
        isFrozenVersion
        isVersioningEnabled
        majorVersionNumber
        minorVersionNumber
        versionStatus
        reservationType
        cmIsMarkedForDeletion
        updateSequenceNumber
        accessAllowed
        contentElementsPresent
        contentSize
        mimeType
        dateContentLastAccessed
        contentRetentionDate
        currentState
        isInExceptionState
        classificationStatus
        indexationId
        cmIndexingFailureCode
        compoundDocumentState
        cmRetentionDate
        properties(includes: ["DocumentTitle"]) {{
            id
            label
            type
            cardinality
            value
        }}
    }}
}}'''
    
    # graphql
    logger.info("Setting graphql queries and folder name")
    input_data['graphql']['graphql_folder_name'] = graphql_folder_name
    input_data['graphql']['graphqlcmd1'] = graphqlcmd1
    input_data['graphql']['graphqlcmd2'] = graphqlcmd2
    input_data['graphql']['graphqlcmd3'] = graphqlcmd3
    input_data['graphql']['s_graphqlcmd1'] = s_graphqlcmd1
    input_data['graphql']['s_graphqlcmd2'] = s_graphqlcmd2
    input_data['graphql']['s_graphqlcmd3'] = s_graphqlcmd3

    
    # dumping the config values to config.tml file
    logger.info("Writing values to config.toml file ...")
    try : 
        with open("./inputs/config.toml","w") as file :
            file.write(dumps(input_data))
    except Exception as e :
        logger.error(f"An exception occured during writing input_data to config.toml file : {e}")
        logger.critical("Exiting BVT execution!!")
        exit()
    
    logger.info("==========================================Ended execution of input_data.py==========================================\n\n")

if __name__ == "__main__" :
    initialize_input_data()