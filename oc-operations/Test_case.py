from util import *
from log import *
import configparser
import os

log = Logs()
parser = configparser.ConfigParser(interpolation=None)
current_dir = os.getcwd()

# Get the namespace and cluster details from the config file
parser.read(current_dir + '/config/testdata.config')
namespace = parser.get('INPUT', 'namespace').strip()
cluster = parser.get('INPUT', 'cluster_name').strip()
cluster_login_username = parser.get('INPUT', 'cluster_user_name').strip()
cluster_login_password = parser.get('INPUT', 'cluster_password').strip()

# OC login and switching to the namespace
try:
    login = f'oc login https://api.{cluster}.cp.fyre.ibm.com:6443 -u {cluster_login_username} -p {cluster_login_password}'
    login_output = run_oc_command(login, log)
    if 'Login successful' in login_output:
        log.logger.info(f'Successfully logged in to the cluster {cluster}')
        print(f'Successfully logged in to the cluster {cluster}')
    else:
        raise ValueError(f'Failed to logged in to the cluster {cluster}. Please check the logs for details.')
    switch_to_namespace = f'oc project {namespace}'
    expected_1 = f'Now using project "{namespace}" on server' 
    expected_2 = f'Already on project "{namespace}" on server'
    output = run_oc_command(switch_to_namespace, log)
    if output:
        if expected_1 in output or expected_2 in output:
              log.logger.info(f'Successfully swicthed to namespace {namespace}')
              print(f'Successfully swicthed to namespace {namespace}')
        else:
            raise ValueError(f'Failed to switch to namespace {namespace}. Please check the logs for details.')
    elif output is False:
        print(f'oc command {switch_to_namespace} failed')
        log.logger.info(f'oc command {switch_to_namespace} failed')
        raise Exception(f'Failed to switch to namespace {namespace}. Please check the logs for details.')
except:
    raise Exception(f'Failed to switch to namespace {namespace}. Please check the logs for details.')


def verify_secrets():
    """
        Name: verify_secrets
        Author: Dhanesh
        Desc: Test case to verify get_secrets: oc get secret -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_secret_command = parser.get('INPUT', 'get_secrets').strip()
    secrets = parser.get('EXPECTED_RESULTS', 'secrets').strip().split(',')
    get_secret_command = get_secret_command.replace("{namespace}", namespace)
    verify_partial_result(get_secret_command, secrets, log)

def verify_fncm_username():
    """
        Name: verify_fncm_username
        Author: Dhanesh
        Desc: Test case to verify get_fncm_username: oc get secret ibm-fncm-secret -o=jsonpath='{@.data.appLoginUsername}'| base64 --decode ;echo
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_fncm_username_command = parser.get('INPUT', 'get_fncm_username').strip()
    fncm_username = parser.get('EXPECTED_RESULTS', 'fncm_username').strip()
    verify_exact_result(get_fncm_username_command, fncm_username, log)

def verify_fncm_password():
    """
        Name: verify_fncm_password
        Author: Dhanesh
        Desc: Test case to verify get_fncm_password: oc get secret ibm-fncm-secret -o=jsonpath='{@.data.appLoginPassword}'| base64 --decode ;echo
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_fncm_password_command = parser.get('INPUT', 'get_fncm_password').strip()
    fncm_password = parser.get('EXPECTED_RESULTS', 'fncm_password').strip()
    verify_exact_result(get_fncm_password_command, fncm_password, log)

def verify_fncm_secret_yaml():
    """
        Name: verify_fncm_secret_yaml
        Author: Dhanesh
        Desc: Test case to verify get_fncm_secret_yaml: oc get secret ibm-fncm-secret -o=jsonpath='{@}'
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_fncm_yaml_command = parser.get('INPUT', 'get_fncm_secret_yaml').strip()
    fncm_secret_yaml_contents = parser.get('EXPECTED_RESULTS', 'fncm_secret_yaml_contents').strip().split(',')
    verify_partial_result(get_fncm_yaml_command, fncm_secret_yaml_contents, log)

def verify_iam_admin_username():
    """
        Name: verify_iam_admin_username
        Author: Dhanesh
        Desc:Test case to verify get_iam_admin_username: oc get secret ibm-iam-bindinfo-platform-auth-idp-credentials -o jsonpath='{.data.admin_username}' | base64 --decode; echo
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_iam_admin_username_command = parser.get('INPUT', 'get_iam_admin_username').strip()
    iam_admin_username = parser.get('EXPECTED_RESULTS', 'iam_admin_username').strip()
    verify_exact_result(get_iam_admin_username_command, iam_admin_username, log)

def verify_iam_admin_password():
    """
        Name: verify_iam_admin_password
        Author: Dhanesh
        Desc: Test case to verify get_iam_admin_password: oc get secret ibm-iam-bindinfo-platform-auth-idp-credentials -o 'jsonpath={.data.admin_password}'| base64 --decode ;echo
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_iam_admin_password_command = parser.get('INPUT', 'get_iam_admin_password').strip()
    iam_admin_password = parser.get('EXPECTED_RESULTS', 'iam_admin_password').strip()
    verify_exact_result(get_iam_admin_password_command, iam_admin_password, log)

def verify_content_app_version():
    """
        Name: verify_content_app_version
        Author: Dhanesh
        Desc: Test case to verify get_content_app_version: oc get Content -o=jsonpath='{.items[*].spec.appVersion}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_content_app_version_command = parser.get('INPUT', 'get_content_app_version').strip()
    get_content_app_version_command = get_content_app_version_command.replace("{namespace}", namespace)
    content_app_version = parser.get('EXPECTED_RESULTS', 'content_app_version').strip()
    verify_exact_result(get_content_app_version_command, content_app_version, log)

def verify_license_accepted():
    """
        Name: verify_license_accepted
        Author: Dhanesh
        Desc: Test case to verify get_license_accepted: oc get Content -o=jsonpath='{.items[*].spec.license}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_license_accepted_command = parser.get('INPUT', 'get_license_accepted').strip()
    get_license_accepted_command = get_license_accepted_command.replace("{namespace}", namespace)
    license_accepted = parser.get('EXPECTED_RESULTS', 'license_accepted').strip()
    verify_exact_result(get_license_accepted_command, license_accepted, log)

def verify_cmis_status():
    """
        Name: verify_cmis_status
        Author: Dhanesh
        Desc: Test case to verify get_cmis_status: oc get Content -o=jsonpath='{.items[*].status.components.cmis}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_cmis_status_command = parser.get('INPUT', 'get_cmis_status').strip()
    get_cmis_status_command = get_cmis_status_command.replace("{namespace}", namespace)
    cmis_status = parser.get('EXPECTED_RESULTS', 'cmis_status').strip().split(',')
    verify_partial_result(get_cmis_status_command, cmis_status, log)

def verify_cdra_status():
    """
        Name: verify_cdra_status
        Author: Dhanesh
        Desc: Test case to verify get_cdra_status: oc get Content -o=jsonpath='{.items[*].status.components.contentDesignerRepoAPI}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_cdra_status_command = parser.get('INPUT', 'get_cdra_status').strip()
    get_cdra_status_command = get_cdra_status_command.replace("{namespace}", namespace)
    cdra_status = parser.get('EXPECTED_RESULTS', 'cdra_status').strip().split(',')
    verify_partial_result(get_cdra_status_command, cdra_status, log)

def verify_cds_status():
    """
        Name: verify_cds_status
        Author: Dhanesh
        Desc: Test case to verify get_cds_status: oc get Content -o=jsonpath='{.items[*].status.components.contentDesignerService}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_cds_status_command = parser.get('INPUT', 'get_cds_status').strip()
    get_cds_status_command = get_cds_status_command.replace("{namespace}", namespace)
    cds_status = parser.get('EXPECTED_RESULTS', 'cds_status').strip().split(',')
    verify_partial_result(get_cds_status_command, cds_status, log)

def verify_cpds_status():
    """
        Name: verify_cpds_status
        Author: Dhanesh
        Desc: Test case to verify get_cpds_status: oc get Content -o=jsonpath='{.items[*].status.components.contentProjectDeploymentService}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_cpds_status_command = parser.get('INPUT', 'get_cpds_status').strip()
    get_cpds_status_command = get_cpds_status_command.replace("{namespace}", namespace)
    cpds_status = parser.get('EXPECTED_RESULTS', 'cpds_status').strip().split(',')
    verify_partial_result(get_cpds_status_command, cpds_status, log)

def verify_css_status():
    """
        Name: verify_css_status
        Author: Dhanesh
        Desc: Test case to verify get_css_status: oc get Content -o=jsonpath='{.items[*].status.components.css}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_css_status_command = parser.get('INPUT', 'get_css_status').strip()
    get_css_status_command = get_css_status_command.replace("{namespace}", namespace)
    css_status = parser.get('EXPECTED_RESULTS', 'css_status').strip().split(',')
    verify_partial_result(get_css_status_command, css_status, log)

def verify_cpe_status():
    """
        Name: verify_cpe_status
        Author: Dhanesh
        Desc: Test case to verify get_cpe_status: oc get Content -o=jsonpath='{.items[*].status.components.cpe}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_cpe_status_command = parser.get('INPUT', 'get_cpe_status').strip()
    get_cpe_status_command = get_cpe_status_command.replace("{namespace}", namespace)
    cpe_status = parser.get('EXPECTED_RESULTS', 'cpe_status').strip().split(',')
    verify_partial_result(get_cpe_status_command, cpe_status, log)

def verify_extshare_status():
    """
        Name: verify_extshare_status
        Author: Dhanesh
        Desc: Test case to verify get_extshare_status: oc get Content -o=jsonpath='{.items[*].status.components.extshare}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_extshare_status_command = parser.get('INPUT', 'get_extshare_status').strip()
    get_extshare_status_command = get_extshare_status_command.replace("{namespace}", namespace)
    extshare_status = parser.get('EXPECTED_RESULTS', 'extshare_status').strip().split(',')
    verify_partial_result(get_extshare_status_command, extshare_status, log)

def verify_graphql_status():
    """
        Name: verify_graphql_status
        Author: Dhanesh
        Desc: Test case to verify get_graphql_status: oc get Content -o=jsonpath='{.items[*].status.components.graphql}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_graphql_status_command = parser.get('INPUT', 'get_graphql_status').strip()
    get_graphql_status_command = get_graphql_status_command.replace("{namespace}", namespace)
    graphql_status = parser.get('EXPECTED_RESULTS', 'graphql_status').strip().split(',')
    verify_partial_result(get_graphql_status_command, graphql_status, log)

def verify_iccsap_status():
    """
        Name: verify_iccsap_status
        Author: Dhanesh
        Desc: Test case to verify get_iccsap_status: oc get Content -o=jsonpath='{.items[*].status.components.iccsap}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_iccsap_status_command = parser.get('INPUT', 'get_iccsap_status').strip()
    get_iccsap_status_command = get_iccsap_status_command.replace("{namespace}", namespace)
    iccsap_status = parser.get('EXPECTED_RESULTS', 'iccsap_status').strip().split(',')
    verify_partial_result(get_iccsap_status_command, iccsap_status, log)

def verify_ier_status():
    """
        Name: verify_ier_status
        Author: Dhanesh
        Desc: Test case to verify get_ier_status: oc get Content -o=jsonpath='{.items[*].status.components.ier}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_ier_status_command = parser.get('INPUT', 'get_ier_status').strip()
    get_ier_status_command = get_ier_status_command.replace("{namespace}", namespace)
    ier_status = parser.get('EXPECTED_RESULTS', 'ier_status').strip().split(',')
    verify_partial_result(get_ier_status_command, ier_status, log)

def verify_navigator_status():
    """
        Name: verify_navigator_status
        Author: Dhanesh
        Desc: Test case to verify get_navigator_status: oc get Content -o=jsonpath='{.items[*].status.components.navigator}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_navigator_status_command = parser.get('INPUT', 'get_navigator_status').strip()
    get_navigator_status_command = get_navigator_status_command.replace("{namespace}", namespace)
    navigator_status = parser.get('EXPECTED_RESULTS', 'navigator_status').strip().split(',')
    verify_partial_result(get_navigator_status_command, navigator_status, log)

def verify_gitgatewayService_status():
    """
        Name: verify_gitgatewayService_status
        Author: Dhanesh
        Desc: Test case to verify get_gitgatewayService_status: oc get Content -o=jsonpath='{.items[*].status.components.gitgatewayService}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_gitgatewayService_status_command = parser.get('INPUT', 'get_gitgatewayService_status').strip()
    get_gitgatewayService_status_command = get_gitgatewayService_status_command.replace("{namespace}", namespace)
    gitgatewayService_status = parser.get('EXPECTED_RESULTS', 'gitgatewayService_status').strip().split(',')
    verify_partial_result(get_gitgatewayService_status_command, gitgatewayService_status, log)

def verify_tm_status():
    """
        Name: verify_tm_status
        Author: Dhanesh
        Desc: Test case to verify get_tm_status: oc get Content -o=jsonpath='{.items[*].status.components.tm}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_tm_status_command = parser.get('INPUT', 'get_tm_status').strip()
    get_tm_status_command = get_tm_status_command.replace("{namespace}", namespace)
    tm_status = parser.get('EXPECTED_RESULTS', 'tm_status').strip().split(',')
    verify_partial_result(get_tm_status_command, tm_status, log)

def verify_viewone_status():
    """
        Name: verify_viewone_status
        Author: Dhanesh
        Desc: Test case to verify get_viewone_status: oc get Content -o=jsonpath='{.items[*].status.components.viewone}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_viewone_status_command = parser.get('INPUT', 'get_viewone_status').strip()
    get_viewone_status_command = get_viewone_status_command.replace("{namespace}", namespace)
    viewone_status = parser.get('EXPECTED_RESULTS', 'viewone_status').strip().split(',')
    verify_partial_result(get_viewone_status_command, viewone_status, log)

def verify_content_operator_status():
    """
        Name: verify_content_operator_status
        Author: Dhanesh
        Desc: Test case to verify get_content_operator_status: oc get Content -o=jsonpath='{.items[*].status.conditions}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_content_operator_status_command = parser.get('INPUT', 'get_content_operator_status').strip()
    get_content_operator_status_command = get_content_operator_status_command.replace("{namespace}", namespace)
    content_operator_status = parser.get('EXPECTED_RESULTS', 'content_operator_status').strip().split(',')
    verify_partial_result(get_content_operator_status_command, content_operator_status, log)

def verify_all_end_points():
    """
        Name: verify_all_end_points
        Author: Dhanesh
        Desc: Test case to verify get_content_operator_status: oc get Content -o=jsonpath='{.items[*].status.endpoints[*]}' -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    end_points =[]
    get_all_end_points_command = parser.get('INPUT', 'get_all_end_points').strip()
    get_all_end_points_command = get_all_end_points_command.replace("{namespace}", namespace)
    all_end_points = parser.get('EXPECTED_RESULTS', 'all_end_points').strip().split(',')
    end_points = [value.replace("{namespace}", namespace).replace("{cluster_nam}", cluster) for value in all_end_points]
    verify_partial_result(get_all_end_points_command, end_points, log)

def verify_events():
    """
        Name: verify_events
        Author: Dhanesh
        Desc: Test case to verify get_events:  oc get events
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_events_command = parser.get('INPUT', 'get_events').strip()
    get_events_command = get_events_command.replace("{namespace}", namespace)
    events = parser.get('EXPECTED_RESULTS', 'events').strip().split(',')
    verify_partial_result(get_events_command, events, log)

def verify_pods():
    """
        Name: verify_pods
        Author: Dhanesh
        Desc: Test case to verify get_pods: oc get pod -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_pods_command = parser.get('INPUT', 'get_pods').strip()
    get_pods_command = get_pods_command.replace("{namespace}", namespace)
    pods = parser.get('EXPECTED_RESULTS', 'pods').strip().split(',')
    verify_partial_result(get_pods_command, pods, log)

def verify_storage_class():
    """
        Name: verify_storage_class
        Author: Dhanesh
        Desc: Test case to verify get_storage_class: oc get storageclass
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_storage_class_command = parser.get('INPUT', 'get_storage_class').strip()
    get_storage_class_command = get_storage_class_command.replace("{namespace}", namespace)
    storage_class = parser.get('EXPECTED_RESULTS', 'storage_class').strip().split(',')
    verify_partial_result(get_storage_class_command, storage_class, log)

def verify_route_cpd():
    """
        Name: verify_route_cpd
        Author: Dhanesh
        Desc: Test case to verify get_route_cpd: oc get route cpd -n {namespace}
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    routes = []
    get_route_cpd_command = parser.get('INPUT', 'get_route_cpd').strip()
    get_route_cpd_command = get_route_cpd_command.replace("{namespace}", namespace)
    route_cpd = parser.get('EXPECTED_RESULTS', 'route_cpd').strip().split(',')
    for route in route_cpd:
        if '{namespace}' and '{cluster_name}' in route:
            route = route.replace('{namespace}', namespace).replace('{cluster_name}', cluster)
            routes.append(route)
        routes.append(route)
    verify_partial_result(get_route_cpd_command, routes, log)

def verify_adm_top_nodes():
    """
        Name: verify_adm_top_nodes
        Author: Dhanesh
        Desc: Test case to verify get_adm_top_nodes: oc adm top nodes
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    nodes =[]
    get_adm_top_nodes_command = parser.get('INPUT', 'get_adm_top_nodes').strip()
    get_adm_top_nodes_command = get_adm_top_nodes_command.replace("{namespace}", namespace)
    adm_top_nodes = parser.get('EXPECTED_RESULTS', 'adm_top_nodes').strip().split(',')
    for node in adm_top_nodes:
        if '{cluster_name}' in node:
            node = node.replace('{cluster_name}', cluster)
            nodes.append(node)
        nodes.append(node)
    verify_partial_result(get_adm_top_nodes_command, nodes, log)

def verify_pv():
    """
        Name: verify_pv
        Author: Dhanesh
        Desc: Test case to verify get_pv: oc get pv
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_pv_command = parser.get('INPUT', 'get_pv').strip()
    pv = parser.get('EXPECTED_RESULTS', 'pv').strip().split(',')
    verify_partial_result(get_pv_command, pv, log)

def verify_pvc():
    """
        Name: verify_pvc
        Author: Dhanesh
        Desc: Test case to verify get_pvc: oc get pvc
        Parameters:
            none
        Returns:
            none
        Raises:
            none
    """
    get_pvc_command = parser.get('INPUT', 'get_pvc').strip()
    pvc = parser.get('EXPECTED_RESULTS', 'pvc').strip().split(',')
    verify_partial_result(get_pvc_command, pvc, log)

def verify_result():
    """
        Name: verify_result
        Author: Dhanesh
        Desc: Verify all the commands executed successfully
        Parameters:
            none
        Returns:
            none
        Raises:
            ValueError
    """
    is_failed = validate(log)
    if is_failed:
        raise ValueError('*********************Some of the oc commands failed or expected results are missing in the actual result. Please check the logs for more details*******************')
    else:
        log.logger.info(f'*****************************************All OC commands executed successfully**********************************************')
        print(f'*****************************************All OC commands executed successfully**********************************************')

if __name__=='__main__':
    verify_secrets()
    verify_fncm_username()
    verify_fncm_password()
    verify_fncm_secret_yaml()
    verify_iam_admin_username()
    verify_iam_admin_password()
    verify_content_app_version()
    verify_license_accepted()
    verify_cmis_status()
    verify_cdra_status()
    verify_cds_status()
    verify_cpds_status()
    verify_css_status()
    verify_cpe_status()
    verify_extshare_status()
    verify_graphql_status()
    verify_iccsap_status()
    verify_ier_status()
    verify_navigator_status()
    verify_gitgatewayService_status()
    verify_tm_status()
    verify_viewone_status()
    verify_content_operator_status()
    verify_all_end_points()
    verify_events()
    verify_pods()
    verify_storage_class()
    verify_route_cpd()
    verify_adm_top_nodes()
    verify_pv()
    verify_pvc()
    verify_result()