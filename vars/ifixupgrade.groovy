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
                        
                        cluster = params.CLUSTER_NAME.toLowerCase()
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        currentBuild.displayName = "${cluster}-${params.NEW_IFIX_VERSION}-${params.PROJECT_NAME}"

                        branch=params.NEW_IFIX_VERSION
                        def buildandifix = params.NEW_IFIX_VERSION.split('-')

                        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.com/icp4a/cert-kubernetes.git"
                        
                        if (branch == '24.0.1-IF001') {
                            branch = '24.0.1'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
                        }
                    }
                }
            }
        }
        stage('Clone ifix & Setup'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script{
                        echo """git clone -b ${branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone} /opt/ifix_upgrade """
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            database=\$(oc get configmap ibm-cp4ba-database-info-cm  -o yaml  | yq '.data.datasource_configuration' -o yaml  | yq '.dc_gcd_datasource.dc_database_type')
                            echo "\${database}"
                            
                            ldap=\$(oc get configmap ibm-cp4ba-ldap-info-cm -o yaml  | yq '.data.ldap_configuration' -o yaml | yq '.lc_selected_ldap_type')
                            echo "\${ldap}"
                            
                             if [[ "Microsoft Active Directory" == \${ldap} ]]
                            then
                                    ldap="MSAD SSL"
                            else
                                    ldap="SDS SSL"
                            fi
                            
                            echo "\${ldap}"
                            cd /opt && \
                            rm -rf ifix_upgrade && \
                            mkdir ifix_upgrade  && \
                            cd ifix_upgrade && \
                            git clone -b ${branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone} /opt/ifix_upgrade && \
                            cd /opt/ifix_upgrade/
                            '
                        """
                        echo """ Project clonning and setting up the configuration is done"""
                    }
                }
            }
        }
        stage('Clone ifix code'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script{
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf ifixcode && \
                            mkdir ifixcode  && \
                            git clone -b ifix --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git /opt/ifixcode/ && \
                            cd /opt/ifixcode/ && \
                            source /opt/automationenv/bin/activate && \
                            cd /opt/ifixcode/ && \
                            oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                            oc project ${params.PROJECT_NAME} && \
                            python ./ifix_upgrade/ifix_upgrade.py ${params.PROJECT_NAME}
                            cd /opt
                            deactivate
                            '
                        """
                        echo """Project ${params.PROJECT_NAME} deploying on ${cluster}"""

                        def message1 = "Upgrade Completed in ${cluster}.\nBuild:${params.NEW_IFIX_VERSION}\n"
                        env.message1 = message1
                        def status1 = "success"
                        env.status1 = status1
                        build job: 'slack-notify', parameters: [
                        string(name:'Status',value:status1),
                        string(name:'MESSAGE',value:message1)]

                    }
                }
            }
        } 
        stage('Running BVT'){
            steps{
                build job: 'BVT_Automation', parameters: [
                string(name: 'ProjectName', value: "${params.PROJECT_NAME}"),
                string(name: 'ClusterName', value: "${cluster}"),
                string(name: 'DeploymentType', value: 'post-upgrade'),
                string(name: 'Build', value: "${params.Build}"),
                string(name: 'IFixVersion', value: "${params.IFixVersion}"),
                string(name: 'OC_Verify', value: "False")]
            }
        }
    }
    post {
        success {
            echo 'Upgrade Pipeline success!'
        }
        failure {
            echo 'Upgrade Pipeline has failed!'
        }
    }
}