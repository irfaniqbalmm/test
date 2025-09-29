import sys,os
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oc_operations import util
from oc_operations import log
import configparser

class TestCase:

    def __init__(self):
        self.log = log.Logs()
        self.parser = configparser.ConfigParser(interpolation=None)
        current_dir = os.getcwd()

        # Get the namespace and cluster details from the config file
        self.parser.read(current_dir + '\\oc_operations\\config\\testdata.config')
        self.namespace = self.parser.get('INPUT', 'namespace').strip()
        self.cluster = self.parser.get('INPUT', 'cluster_name').strip().lower()
        self.cluster_login_username = self.parser.get('INPUT', 'cluster_user_name').strip()
        self.cluster_login_password = self.parser.get('INPUT', 'cluster_password').strip()

    def verify_secrets(self):
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
        get_secret_command = self.parser.get('INPUT', 'get_secrets').strip()
        secrets = self.parser.get('EXPECTED_RESULTS', 'secrets').strip().split(',')
        get_secret_command = get_secret_command.replace("{namespace}", self.namespace)
        util.verify_partial_result(get_secret_command, secrets, self.log)

    def verify_fncm_username(self):
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
        get_fncm_username_command = self.parser.get('INPUT', 'get_fncm_username').strip()
        fncm_username = self.parser.get('EXPECTED_RESULTS', 'fncm_username').strip()
        util.verify_exact_result(get_fncm_username_command, fncm_username, self.log)

    def verify_fncm_password(self):
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
        get_fncm_password_command = self.parser.get('INPUT', 'get_fncm_password').strip()
        fncm_password = self.parser.get('EXPECTED_RESULTS', 'fncm_password').strip()
        util.verify_exact_result(get_fncm_password_command, fncm_password, self.log)

    def verify_fncm_secret_yaml(self):
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
        get_fncm_yaml_command = self.parser.get('INPUT', 'get_fncm_secret_yaml').strip()
        fncm_secret_yaml_contents = self.parser.get('EXPECTED_RESULTS', 'fncm_secret_yaml_contents').strip().split(',')
        util.verify_partial_result(get_fncm_yaml_command, fncm_secret_yaml_contents, self.log)

    def verify_iam_admin_username(self):
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
        get_iam_admin_username_command = self.parser.get('INPUT', 'get_iam_admin_username').strip()
        iam_admin_username = self.parser.get('EXPECTED_RESULTS', 'iam_admin_username').strip()
        util.verify_exact_result(get_iam_admin_username_command, iam_admin_username, self.log)

    def verify_iam_admin_password(self):
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
        get_iam_admin_password_command = self.parser.get('INPUT', 'get_iam_admin_password').strip()
        iam_admin_password = self.parser.get('EXPECTED_RESULTS', 'iam_admin_password').strip()
        util.verify_exact_result(get_iam_admin_password_command, iam_admin_password, self.log)

    def verify_content_app_version(self):
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
        get_content_app_version_command = self.parser.get('INPUT', 'get_content_app_version').strip()
        get_content_app_version_command = get_content_app_version_command.replace("{namespace}", self.namespace)
        content_app_version = self.parser.get('EXPECTED_RESULTS', 'content_app_version').strip()
        util.verify_exact_result(get_content_app_version_command, content_app_version, self.log)

    def verify_license_accepted(self):
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
        get_license_accepted_command = self.parser.get('INPUT', 'get_license_accepted').strip()
        get_license_accepted_command = get_license_accepted_command.replace("{namespace}", self.namespace)
        license_accepted = self.parser.get('EXPECTED_RESULTS', 'license_accepted').strip()
        util.verify_partial_result(get_license_accepted_command, license_accepted, self.log)

    def verify_cmis_status(self):
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
        get_cmis_status_command = self.parser.get('INPUT', 'get_cmis_status').strip()
        get_cmis_status_command = get_cmis_status_command.replace("{namespace}", self.namespace)
        cmis_status = self.parser.get('EXPECTED_RESULTS', 'cmis_status').strip().split(',')
        util.verify_partial_result(get_cmis_status_command, cmis_status, self.log)

    def verify_cdra_status(self):
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
        get_cdra_status_command = self.parser.get('INPUT', 'get_cdra_status').strip()
        get_cdra_status_command = get_cdra_status_command.replace("{namespace}", self.namespace)
        cdra_status = self.parser.get('EXPECTED_RESULTS', 'cdra_status').strip().split(',')
        util.verify_partial_result(get_cdra_status_command, cdra_status, self.log)

    def verify_cds_status(self):
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
        get_cds_status_command = self.parser.get('INPUT', 'get_cds_status').strip()
        get_cds_status_command = get_cds_status_command.replace("{namespace}", self.namespace)
        cds_status = self.parser.get('EXPECTED_RESULTS', 'cds_status').strip().split(',')
        util.verify_partial_result(get_cds_status_command, cds_status, self.log)

    def verify_cpds_status(self):
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
        get_cpds_status_command = self.parser.get('INPUT', 'get_cpds_status').strip()
        get_cpds_status_command = get_cpds_status_command.replace("{namespace}", self.namespace)
        cpds_status = self.parser.get('EXPECTED_RESULTS', 'cpds_status').strip().split(',')
        util.verify_partial_result(get_cpds_status_command, cpds_status, self.log)

    def verify_css_status(self):
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
        get_css_status_command = self.parser.get('INPUT', 'get_css_status').strip()
        get_css_status_command = get_css_status_command.replace("{namespace}", self.namespace)
        css_status = self.parser.get('EXPECTED_RESULTS', 'css_status').strip().split(',')
        util.verify_partial_result(get_css_status_command, css_status, self.log)

    def verify_cpe_status(self):
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
        get_cpe_status_command = self.parser.get('INPUT', 'get_cpe_status').strip()
        get_cpe_status_command = get_cpe_status_command.replace("{namespace}", self.namespace)
        cpe_status = self.parser.get('EXPECTED_RESULTS', 'cpe_status').strip().split(',')
        util.verify_partial_result(get_cpe_status_command, cpe_status, self.log)

    def verify_extshare_status(self):
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
        get_extshare_status_command = self.parser.get('INPUT', 'get_extshare_status').strip()
        get_extshare_status_command = get_extshare_status_command.replace("{namespace}", self.namespace)
        extshare_status = self.parser.get('EXPECTED_RESULTS', 'extshare_status').strip().split(',')
        util.verify_partial_result(get_extshare_status_command, extshare_status, self.log)

    def verify_graphql_status(self):
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
        get_graphql_status_command = self.parser.get('INPUT', 'get_graphql_status').strip()
        get_graphql_status_command = get_graphql_status_command.replace("{namespace}", self.namespace)
        graphql_status = self.parser.get('EXPECTED_RESULTS', 'graphql_status').strip().split(',')
        util.verify_partial_result(get_graphql_status_command, graphql_status, self.log)

    def verify_iccsap_status(self):
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
        get_iccsap_status_command = self.parser.get('INPUT', 'get_iccsap_status').strip()
        get_iccsap_status_command = get_iccsap_status_command.replace("{namespace}", self.namespace)
        iccsap_status = self.parser.get('EXPECTED_RESULTS', 'iccsap_status').strip().split(',')
        util.verify_partial_result(get_iccsap_status_command, iccsap_status, self.log)

    def verify_ier_status(self):
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
        get_ier_status_command = self.parser.get('INPUT', 'get_ier_status').strip()
        get_ier_status_command = get_ier_status_command.replace("{namespace}", self.namespace)
        ier_status = self.parser.get('EXPECTED_RESULTS', 'ier_status').strip().split(',')
        util.verify_partial_result(get_ier_status_command, ier_status, self.log)

    def verify_navigator_status(self):
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
        get_navigator_status_command = self.parser.get('INPUT', 'get_navigator_status').strip()
        get_navigator_status_command = get_navigator_status_command.replace("{namespace}", self.namespace)
        navigator_status = self.parser.get('EXPECTED_RESULTS', 'navigator_status').strip().split(',')
        util.verify_partial_result(get_navigator_status_command, navigator_status, self.log)

    def verify_gitgatewayService_status(self):
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
        get_gitgatewayService_status_command = self.parser.get('INPUT', 'get_gitgatewayService_status').strip()
        get_gitgatewayService_status_command = get_gitgatewayService_status_command.replace("{namespace}", self.namespace)
        gitgatewayService_status = self.parser.get('EXPECTED_RESULTS', 'gitgatewayService_status').strip().split(',')
        util.verify_partial_result(get_gitgatewayService_status_command, gitgatewayService_status, self.log)

    def verify_tm_status(self):
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
        get_tm_status_command = self.parser.get('INPUT', 'get_tm_status').strip()
        get_tm_status_command = get_tm_status_command.replace("{namespace}", self.namespace)
        tm_status = self.parser.get('EXPECTED_RESULTS', 'tm_status').strip().split(',')
        util.verify_partial_result(get_tm_status_command, tm_status, self.log)

    def verify_viewone_status(self):
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
        get_viewone_status_command = self.parser.get('INPUT', 'get_viewone_status').strip()
        get_viewone_status_command = get_viewone_status_command.replace("{namespace}", self.namespace)
        viewone_status = self.parser.get('EXPECTED_RESULTS', 'viewone_status').strip().split(',')
        util.verify_partial_result(get_viewone_status_command, viewone_status, self.log)

    def verify_content_operator_status(self):
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
        get_content_operator_status_command = self.parser.get('INPUT', 'get_content_operator_status').strip()
        get_content_operator_status_command = get_content_operator_status_command.replace("{namespace}", self.namespace)
        content_operator_status = self.parser.get('EXPECTED_RESULTS', 'content_operator_status').strip().split(',')
        util.verify_partial_result(get_content_operator_status_command, content_operator_status, self.log)

    def verify_all_end_points(self):
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
        get_all_end_points_command = self.parser.get('INPUT', 'get_all_end_points').strip()
        get_all_end_points_command = get_all_end_points_command.replace("{namespace}", self.namespace)
        all_end_points = self.parser.get('EXPECTED_RESULTS', 'all_end_points').strip().split(',')
        end_points = [value.replace("{namespace}", self.namespace).replace("{cluster_nam}", self.cluster) for value in all_end_points]
        util.verify_partial_result(get_all_end_points_command, end_points, self.log)

    def verify_events(self):
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
        get_events_command = self.parser.get('INPUT', 'get_events').strip()
        get_events_command = get_events_command.replace("{namespace}", self.namespace)
        events = self.parser.get('EXPECTED_RESULTS', 'events').strip().split(',')
        util.verify_partial_result(get_events_command, events, self.log)

    def verify_pods(self):
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
        get_pods_command = self.parser.get('INPUT', 'get_pods').strip()
        get_pods_command = get_pods_command.replace("{namespace}", self.namespace)
        pods = self.parser.get('EXPECTED_RESULTS', 'pods').strip().split(',')
        util.verify_partial_result(get_pods_command, pods, self.log)

    def verify_storage_class(self):
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
        get_storage_class_command = self.parser.get('INPUT', 'get_storage_class').strip()
        get_storage_class_command = get_storage_class_command.replace("{namespace}", self.namespace)
        storage_class = self.parser.get('EXPECTED_RESULTS', 'storage_class').strip().split(',')
        util.verify_partial_result(get_storage_class_command, storage_class, self.log)

    def verify_route_cpd(self):
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
        get_route_cpd_command = self.parser.get('INPUT', 'get_route_cpd').strip()
        get_route_cpd_command = get_route_cpd_command.replace("{namespace}", self.namespace)
        route_cpd = self.parser.get('EXPECTED_RESULTS', 'route_cpd').strip().split(',')
        for route in route_cpd:
            if '{namespace}' and '{cluster_name}' in route:
                route = route.replace('{namespace}', self.namespace).replace('{cluster_name}', self.cluster)
                routes.append(route)
            routes.append(route)
        util.verify_partial_result(get_route_cpd_command, routes, self.log)

    def verify_adm_top_nodes(self):
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
        get_adm_top_nodes_command = self.parser.get('INPUT', 'get_adm_top_nodes').strip()
        get_adm_top_nodes_command = get_adm_top_nodes_command.replace("{namespace}", self.namespace)
        adm_top_nodes = self.parser.get('EXPECTED_RESULTS', 'adm_top_nodes').strip().split(',')
        for node in adm_top_nodes:
            if '{cluster_name}' in node:
                node = node.replace('{cluster_name}', self.cluster)
                nodes.append(node)
            nodes.append(node)
        util.verify_partial_result(get_adm_top_nodes_command, nodes, self.log)

    def verify_pv(self):
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
        get_pv_command = self.parser.get('INPUT', 'get_pv').strip()
        pv = self.parser.get('EXPECTED_RESULTS', 'pv').strip().split(',')
        util.verify_partial_result(get_pv_command, pv, self.log)

    def verify_pvc(self):
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
        get_pvc_command = self.parser.get('INPUT', 'get_pvc').strip()
        pvc = self.parser.get('EXPECTED_RESULTS', 'pvc').strip().split(',')
        util.verify_partial_result(get_pvc_command, pvc, self.log)

    def verify_result(self):
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
        is_failed = util.validate(self.log)
        if is_failed:
            raise ValueError('*********************Some of the oc commands failed or expected results are missing in the actual result. Please check the logs for more details*******************')
        else:
            self.log.logger.info(f'*****************************************All OC commands executed successfully**********************************************')
            print(f'*****************************************All OC commands executed successfully**********************************************')

