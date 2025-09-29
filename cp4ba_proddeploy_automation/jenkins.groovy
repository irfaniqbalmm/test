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
    switch(ldapName) {
        case 'MSAD':
            return 'MSAD SSL'
        case 'SDS':
            return 'TDS SSL'
        default:
            error "Unsupported LDAP_NAME: ${ldapName}"
    }
}


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
                        
                        dbname = params.DATABASE.toLowerCase()
                        ldapname = params.LDAP.toLowerCase()
                        cluster = params.CLUSTER_NAME.toLowerCase()
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"


                        stg_prod = 'Prod'
                        if (params.STAGE_OR_PROD == 'Stage') {
                            stg_prod = 'dev'
                        }
                        
                        git_branch=params.BRANCH
                        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.com/icp4a/cert-kubernetes.git"
                        
                        if (params.BRANCH == '2401') {
                            git_branch='master'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
                        }
                        
                        if (params.BRANCH == '24.0.0-IF003') {
                            git_branch = '24.0.0'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
                        }
                        
                        echo " git_clone path =  ${git_clone} "
                        
                        spd_on = 'no'
                        new_pjt_name = params.PROJECT_NAME
                        if (params.SEPARATION_DUTIES.toLowerCase() == 'yes') {
                        spd_on = 'yes'
                        new_pjt_name = new_pjt_name + 'pods'
                        }
                        currentBuild.displayName = "${cluster}-${params.BRANCH}-${params.IFixVersion}-${dbname}-${ldapname}"
                    }
                }
            }
        }
        stage('Install Packages') {
            steps {
                script {
                    echo "Installing the required  python packages "
                     sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
                        oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                        echo "@@ Running on \$(hostname)" && \
                        echo "@@ Cluster Name: ${cluster}" && \
                        echo "@@ Project Name: ${params.PROJECT_NAME}" && \
                        echo "@@ DB: ${dbname} " && \
                        echo "@@ LDAP: ${ldapname} " && \
                        echo "@@ Fips: ${params.FIPS.toUpperCase()} " && \
                        echo "@@ Egress: ${params.EGRESS.toUpperCase()} " && \
                        echo "@@ Separation of Duties: ${spd_on.toUpperCase()} " && \
                        echo "@@ Postgres DB for Metastore: ${params.EXTERNAL_DB_METASTORE.toUpperCase()} " && \
                        echo "@@ External Certificate: ${params.EXTERNAL_CERTIFICATE.toUpperCase()} " && \
                        ocpversion=\$(oc version | grep Server) && \
                        echo "@@ \${ocpversion} "  && \
                        echo "@@ Deployment type: ${params.STAGE_OR_PROD.toUpperCase()} " && \
                        echo "@@ Console link: https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com" && \
                        echo "@@ Infra node: api.${cluster}.cp.fyre.ibm.com" && \
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
			            yum install -y python3.12 && \
                        python3.12 -m venv /opt/automationenv && \
                        source /opt/automationenv/bin/activate && \
                        echo "Installation of basic packages is done." && \
                        echo "Running on \$(hostname)" && \
                        deactivate
                        '
                    """
                    echo " Install Packages Done."
                }
            }
        }
        stage('Clean Project') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                        if (params.CLEANUP =='YES'){
                            pjt = params.PROJECT_CLEAN
                            
                                echo """Cleaning the project ${pjt} using ${params.CLEANUPSCRIPT} script"""
                                if(params.CLEANUPSCRIPT == "DEREK") {
                                    sh """
                                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
                                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                                        echo "Running on \$(hostname)" && \
                                        echo "Cluster Name: ${cluster}" && \
                                        echo "Project Name to clean : ${pjt}" && \
                                        echo "DB: ${dbname} " && \
                                        echo "LDAP: ${ldapname} " && \
                                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                                        cd /opt/ADPDeploymentResources/HelperScripts/ && \
                                        curl -sSfL -u "${GITHUB_USER}:${GITHUB_PASS}" -o cleanup.sh https://raw.github.ibm.com/dba/derek-repo/main/CP4BA/scripts/uninstall-iaf-cpfs-cp4ba.sh && \
                                        curl -sSfL -u "${GITHUB_USER}:${GITHUB_PASS}" -o patch.sh https://raw.github.ibm.com/dkrishan/Cp4ba-Automation/main/cp4ba_proddeploy_automation/patch.sh && \
                                        chmod +x patch.sh  && \
                                        chmod +x cleanup.sh  && \
                                        oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                                        oc project ${pjt} && \
                                        ./patch.sh && \
                                        ./cleanup.sh -s && \
                                        cd /data && \
                                        echo "Moved to data directory"
                                        find /data/* ! -name "registry" -exec rm -rf {} +  >/dev/null 2>&1
                                        echo "Cleaned data folder"
                                        '
                                    """
                                }
                                else {
                                    sh """
                                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
                                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                                        echo "Running on \$(hostname)"  && \
                                        echo "Cluster Name: ${cluster}" && \
                                        echo "Project Name to clean : ${params.PROJECT_CLEAN}" && \
                                        echo "DB: ${dbname} " && \
                                        echo "LDAP: ${ldapname} " && \
                                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                                        cd /opt && \
                                        rm -rf cleanupdir/ && \
                                        mkdir cleanupdir/ && \
                                        cd cleanupdir/ && \
                                        git clone -b master --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes && \
                                        cd cert-kubernetes/scripts/ && \
                                        chmod +x cp4a-clean-up.sh && \
                                        oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                                        ./cp4a-clean-up.sh -n ${pjt} -s -a && \
                                        echo "Project ${pjt} cleaned."  && \
                                        cd /opt  && \
                                        rm -rf cleanupdir/ && \
                                        echo "Removed cleanupdir directory."  && \
                                        cd /data && \
                                        echo "Moved to data directory"
                                        find /data/* ! -name "registry" -exec rm -rf {} +  >/dev/null 2>&1
                                        echo "Cleaned data folder"
                                        ' 
                                    """
                                }
                         
                        }
                        echo " Project cleaned."
                    }
                }
            }
        }
        stage('Clone & Setup'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                    script{
                        git_clone=git_clone
                        env.entitlement = entitlement_key
                        if (stg_prod =='Prod'){
                            env.entitlement = entitlement_prod
                        }
                        echo """Entitlement Key ${env.entitlement}"""
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
                            git clone -b hotfix --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            source /opt/automationenv/bin/activate && \
                            pip3 install -r requirements.txt && \
                            pip freeze && \
                            chmod +x * && \
                            cd config && \
                            sed -i "s;CLONE_REPO=.*;CLONE_REPO=${git_clone};g" data.config && \
                            sed -i "s/ENTITLEMENT_KEY=.*/ENTITLEMENT_KEY=${env.entitlement}/" data.config && \
                            sed -i "s/cp_prod=.*/cp_prod=${entitlement_prod}/" data.config && \
                            sed -i "s/cp_stg=.*/cp_stg=${entitlement_key}/" data.config && \
                            sed -i "s/userandpass=.*/userandpass=${pull_secret_token}/" data.config && \
                            deactivate
                            '
                        """
                        echo """ Project clonning and setting up the configuration is done"""
                    }
                }
            }
        }
        stage('Production Deployment'){
            steps{
                script{
                    def message = "Deployment Started in ${cluster}.\nProject Name: ${params.PROJECT_NAME}\nProducts: CPE,ICN,CSS,GraphQL,CMIS,TM, BAI,IER\nDeployment type: ${params.STAGE_OR_PROD}\nFIPS: ${params.FIPS.toUpperCase()}\nEGRESS: ${params.EGRESS.toUpperCase()}\nSeparation of Duties: ${spd_on.toUpperCase()}\nPostgres DB for Metastore: ${params.EXTERNAL_DB_METASTORE.toUpperCase()}\nExternal Certificate: ${params.EXTERNAL_CERTIFICATE.toUpperCase()}\nDB: ${dbname}\nLDAP: ${ldapname}\nConsole link : https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com\nConsole Creds: kubeadmin / ${KUBE_PASS}\nInfra node: api.${cluster}.cp.fyre.ibm.com\nBuild: ${params.Build}\nIfix: ${params.IFixVersion}\nBuild_Url: ${env.BUILD_URL}"
                    env.message = message
                    def status = "success"
                    env.status = status
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    // slackSend (color: '#00FF00', message: "Deployment Started in  '${cluster}' (${env.BUILD_URL})")
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                        chmod +x ./utils/db_operations/execute_mssql_scripts/installDrivers.sh  && \
                        ./utils/db_operations/execute_mssql_scripts/installDrivers.sh  && \
                        ./prod_deployment.sh ${dbname} ${ldapname} ${params.PROJECT_NAME} ${params.BRANCH} ${stg_prod} ${cluster} ${KUBE_PASS} ${spd_on} ${params.FIPS} ${params.EXTERNAL_DB_METASTORE} ${params.EXTERNAL_CERTIFICATE} ${git_branch} ${params.EGRESS} && \
                        deactivate
                        '
                    """
                    echo """Project ${params.PROJECT_NAME} deploying on ${cluster}"""
                        
                }
            }
        }
        stage('Checking Deployment status'){
            steps{
                script{
                    def bvtDbName = convertDbNameToSSL(params.DATABASE)
                    env.bvtDbName = bvtDbName
                    def bvtLdapName = convertLdapNameToSSL(params.LDAP)
                    env.bvtLdapName = bvtLdapName
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        cd /opt && \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                        chmod +x * && \
                        ./check_status.sh ${cluster} ${KUBE_PASS} ${new_pjt_name} && \
                        cd /opt
                        deactivate
                        '
                    """
                    def message1 = "Deployment Completed in ${cluster}.\nBuild:${params.Build}\nIfix:${params.IFixVersion}\nBuild_Url:${env.BUILD_URL}"
                    env.message1 = message1
                    def status1 = "success"
                    env.status1 = status1
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status1),
                    string(name:'MESSAGE',value:message1)]
                    // slackSend (color: '#00FF00', message: "Starting BVT for '${cluster}' (${env.BUILD_URL}) \n DB: ${env.bvtDbName} \n LDAP: ${env.bvtLdapName} \n Branch : ${params.BRANCH}")
                    echo """ Starting BVT for ${cluster} (${env.BUILD_URL})"""
                }
            }
        }
        stage('Running BVT'){
            steps{
                
                build job: 'BVT_Automation', parameters: [
                string(name: 'ProjectName', value: "${new_pjt_name}"),
                string(name: 'ClusterName', value: "${cluster}"),
                string(name: 'DB', value: "${env.bvtDbName}"),
                string(name: 'LDAP', value: "${env.bvtLdapName}"),
                string(name: 'DeploymentType', value: 'production'),
                string(name: 'Build', value: "${params.Build}"),
                string(name: 'IFixVersion', value: "${params.IFixVersion}"),
                string(name: 'OC_Verify', value: "True")]
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
