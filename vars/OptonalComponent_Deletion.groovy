@Library(['git-clone']) _
def convertDbNameToSSL(dbName) {
    switch(dbName.toLowerCase()) {
        case 'db2':
            return 'DB2 SSL'
        case 'postgres':
            return 'POSTGRES SSL'
        case 'mssql':
            return 'MSSQL SSL'
        case 'oracle':
            return 'ORACLE SSL'
        case 'postgresedb':
            return 'PostgresEDB'
        default:
            error "Unsupported DB_NAME: ${dbName}"
    }
}
def convertLdapNameToSSL(ldapName) {
    switch(ldapName.toUpperCase()) {
        case 'MSAD':
            return 'MSAD SSL'
        case 'SDS':
            return 'TDS SSL'
        case 'PINGDIRECTORY':
            return 'PINGDIRECTORY SSL'
        default:
            return 'MSAD SSL'
    }
}
import groovy.json.JsonOutput
pipeline {
    agent any
    environment {
    PATH = "/usr/local/bin:$PATH"
    GITHUB_CREDS = credentials('github-credentials')
    }
    stages {
        stage('Get Cluster Data') {
            steps {
		        withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                        // URL to the JSON file
                        sh('curl -u ${GITHUB_USER}:${GITHUB_PASS} -o /tmp/clusters_data.json https://raw.github.ibm.com/dkrishan/Cp4ba-Automation/main/CP4BA_Package/clusters.json')

                        // Parse the JSON content
                        def jsonSlurper = new groovy.json.JsonSlurper()
                        def inputFile = new File("/tmp/clusters_data.json")
                        def jsonString = inputFile.text
                        def jsonData = jsonSlurper.parseText(jsonString)

                        component_names = params.SELECT_OPTIONAL_COMPONENTS_TO_DELETE.toLowerCase()
                        varProjectName=params.PROJECT_NAME
                        varClusterName=params.CLUSTER_NAME
                        varDatabase=params.DB
                        varLDAP=params.LDAP
                        
                        echo " componentNames =  ${component_names} "
                        echo " Project Name =  ${varProjectName} "
                        echo " ClusterNames =  ${varClusterName} "
                        echo " Database =  ${varClusterName} "

                    
                        
                        //multildap = params.Multildap
                        //second_ldap_ssl_enabled = params.second_ldap_ssl_enabled
                        //multildap_post_init = params.multildap_post_init
                        cluster = params.CLUSTER_NAME.toLowerCase()
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"

                        currentBuild.displayName = "${varClusterName}-${varProjectName}" 
                        
                    }
                }
            }
        }
        stage('Clone Automation Repo') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')
                ]) {
                    script {
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
                            git clone -b main --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git
                            '
                        """
                        echo "Automation repo cloned successfully on remote server."
                    }
                }
            }
        }

        stage('Deleting Optional Component'){
            steps{
                script{

                    def bvtDbName = convertDbNameToSSL(params.DATABASE)
                    env.bvtDbName = bvtDbName
                    def bvtLdapName = convertLdapNameToSSL(params.LDAP)
                    env.bvtLdapName = bvtLdapName
                    echo "ldap =  ${env.bvtLdapName}"

                    def message = "Deployment Started in ${cluster}.\nProject Name: ${params.PROJECT_NAME}\nConsole link : https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com\nConsole Creds: kubeadmin / ${KUBE_PASS}\nInfra node: api.${cluster}.cp.fyre.ibm.com"
                    
                    def myConfig = [
                        "cluster_name": cluster,
                        "cluster_pass": KUBE_PASS,
                        "component_names": component_names
                    ]

                    def jsonStr = JsonOutput.toJson(myConfig)
                    def escapedJsonStr = jsonStr.replace('"', '\\"')

                    echo "Passing JSON: ${jsonStr}"
                    echo """ ${jsonStr} """

                    def scriptstatus = sh(script: """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            set -e && \
                            source /opt/automationenv/bin/activate && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                            python3 ./Optional_Component_Deletion.py \"${escapedJsonStr}\" && \
                            deactivate
                        '
                    """)


                    echo """Component patching completed on ${cluster} for components: ${component_names}"""


                    // Delete specific pods
                    echo "Deleting ibm-content-operator pods in namespace ${varProjectName}..."
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            oc delete pod \$(oc get pods -n ${varProjectName} --no-headers | grep ibm-content-operator | cut -d" " -f1) -n ${varProjectName}
                        '
                    """
                    
                    // Wait before deleting pods
                    echo "Waiting for 5 minutes before deleting ibm-content-operator pods..."
                    sleep(time: 20, unit: 'MINUTES') 
                }
            }
        }

       stage('Running BVT'){
            steps{
                
                build job: 'BVT_Automation', parameters: [
                string(name: 'ProjectName', value: "${varProjectName}"),
                string(name: 'ClusterName', value: "${varClusterName}"),
                string(name: 'DeploymentType', value: 'post-upgrade'),
                string(name: 'LDAP', value: "${env.bvtLdapName}"),
                string(name: 'Build', value: "${params.Build}"),
                string(name: 'IFixVersion', value: "${params.IFixVersion}"),
                string(name: 'DB', value: "${env.bvtDbName}"),]
            }
        }           
    }
    post {
        success {
            echo 'Deployment Pipeline success!'
        }
        failure {
            echo 'Deployment Pipeline has failed!'
        }
    }
}