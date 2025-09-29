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
                        
                        ldapname = params.LDAP.toLowerCase()
                        cluster = params.CLUSTER_NAME.toLowerCase()
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        spd_on = 'No'
                        external_db_metastore = 'No'
                        external_certificate = 'No'
                        globalCatalog = params.GLOBAL_CATALOG

                        stg_prod = 'Prod'
                        if (params.STAGE_OR_PROD == 'Stage') {
                            stg_prod = 'dev'
                        }
                        
                        git_branch=params.BRANCH
                        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.com/icp4a/cert-kubernetes-bai.git"
                        if (params.BRANCH == '24.0.1-IF005') {
                            git_branch='24.0.1'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes-bai.git"
                            echo "Branch selected is 24.0.1-IF005, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
                        }
                        if (params.BRANCH == '25.0.1') {
                            git_branch='main'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes-bai.git"
                            echo "Branch selected is 25.0.1, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
                        }
                        if (params.BRANCH == '24.0.0-IF005') {
                            git_branch='24.0.0'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes-bai.git"
                            echo "Branch selected is 24.0.0-IF005, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
                        }

                        if (params.BRANCH == '25.0.0-IF002') {
                            git_branch='25.0.0'
                            git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes-bai.git"
                            echo "Branch selected is 25.0.0-IF002, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
                        }
                        echo "git_clone path =  ${git_clone}"
                        echo "git clone branch = ${git_branch}"

                        //For seperation of duty
                        spd_on = 'no'
                        new_pjt_name = params.PROJECT_NAME
                        if (params.SEPARATION_DUTIES.toLowerCase() == 'yes') {
                        spd_on = 'yes'
                        new_pjt_name = new_pjt_name + 'operands'
                        }
                        currentBuild.displayName = "${cluster}-${params.BRANCH}-${ldapname}-${params.PROJECT_NAME}"
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
                        echo "@@ Proceed with Cleanup: ${params.CLEANUP}" && \
                        echo "@@ Project to clean: ${params.PROJECT_CLEAN}" && \
                        echo "@@ LDAP: ${ldapname} " && \
                        echo "@@ Egress: ${params.EGRESS.toUpperCase()} " && \
                        echo "@@ Separation of Duties: ${spd_on.toUpperCase()} " && \
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
                    echo " All packages installed successfully."
                }
            }
        }
        stage('Clone & Setup'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                    script{
                        env.entitlement = entitlement_key
                        if (stg_prod =='Prod'){
                            env.entitlement = entitlement_prod
                        }
                        echo """Entitlement Key ${env.entitlement}"""
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
                            git clone --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            source /opt/automationenv/bin/activate && \
                            pip3 install -r requirements.txt && \
                            pip freeze && \
                            chmod +x * && \
                            cd config && \
                            sed -i "s;CLONE_REPO=.*;CLONE_REPO=${git_clone};g" bai_data.config && \
                            sed -i "s/ENTITLEMENT_KEY=.*/ENTITLEMENT_KEY=${env.entitlement}/" bai_data.config && \
                            sed -i "s/cp_prod=.*/cp_prod=${entitlement_prod}/" data.config && \
                            sed -i "s/cp_stg=.*/cp_stg=${entitlement_key}/" data.config && \
                            sed -i "s/userandpass=.*/userandpass=${pull_secret_token}/" data.config && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            chmod +x install_java.sh && \
                            ./install_java.sh  && \
                            deactivate
                            '
                        """
                        echo """ Project clonning and setting up the configuration is done"""
                    }
                }
            }
        }
        stage('BAI Production Deployment'){
            steps{
                script{
                    def message = "Deployment Started in ${cluster}.\nProject Name: ${params.PROJECT_NAME}\nProduct: BAI Standalone \nBuild: ${params.BRANCH} \nDeployment type: ${params.STAGE_OR_PROD}\n EGRESS: ${params.EGRESS.toUpperCase()}\nSeparation of Duties: ${spd_on.toUpperCase()}\nLDAP: ${ldapname}\nConsole link : https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com\nConsole Creds: kubeadmin / ${KUBE_PASS}\nInfra node: api.${cluster}.cp.fyre.ibm.com\nBuild_Url: ${env.BUILD_URL}"
                    env.message = message
                    def status = "success"
                    env.status = status
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                        python3 bai_deployment.py ${ldapname} ${params.PROJECT_NAME} ${params.BRANCH} ${stg_prod} ${cluster} ${KUBE_PASS} ${spd_on} ${external_db_metastore} ${external_certificate} ${git_branch} ${params.EGRESS} ${globalCatalog} && \
                        deactivate
                        '
                    """
                    echo """Project ${params.PROJECT_NAME} deploying on ${cluster}"""
                        
                }
            }
        }  
        stage('Check BAI Deployment status'){
            steps{
                script{
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        cd /opt && \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                        oc project ${params.PROJECT_NAME} && \
                        chmod +x * && \
                        ./bai_deployment_status.sh ${cluster} ${KUBE_PASS} ${new_pjt_name} && \
                        cd /opt
                        deactivate
                        '
                    """
                    def message = "BAI Deployment Completed in ${cluster}.\nBuild:${params.BRANCH}"
                    env.message = message
                    def status = "success"
                    env.status = status
                    def consoleLink = "https://console-openshift-console.apps.${cluster.toLowerCase()}.cp.fyre.ibm.com"
                    consoleLink += " (kubeadmin/${KUBE_PASS})"
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    sh """ 
                        oc login https://${env.SSH_URL}:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify
                        oc project ${new_pjt_name}
                        name=\$(oc get configmap | grep access-info | awk \'{print \$1}\')
                        echo 'Configmap name: \$name'
                        oc get configmap \$name -o yaml > access.yaml 
                        ls
                        pwd
                    """
                    if (!fileExists('access.yaml')) {
                        error("access.yaml file not found!")
                    } else {
                        echo "The access.yaml file is present. Reading access.yaml..."
                    }
                    def yamlData = readYaml file: 'access.yaml'
                    def formattedString = ''
                        yamlData.data.each { key, value ->
                            formattedString += "*${key}*:\n```${value}```\n\n"
                        }
                    def hellomessage = "Hi All,\nHere is the Fresh Production deployment for BAI(Business Automation Insights) Standalone ${params.BRANCH}  Build"
                    def message2 = hellomessage + "\n\nOCP: " +consoleLink+"\nNamespace: "+params.PROJECT_NAME+"\nNetwork Policy: "+params.EGRESS+"\nLdap: "+params.LDAP+"\nSeperation of duty: ${spd_on}"+"\nExternal postgres for metastore IM/ZEN/BTS: ${external_db_metastore}"+"\nExternal certificate (root CA): ${external_certificate}"+"\n*Access URL*:\n\n"+formattedString
                    slackSend (color: '#00FF00', message: message2)
                }
            }
        }
        stage('Send data to FNCM Automation platform and trigger FNCM automation'){
            steps{
                script{
                    if (params.FNCM_INTEGRATION.toLowerCase() == 'yes') {
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                        python3 ./utils/bai_fncm_integration.py ${ldapname} ${new_pjt_name} ${params.BRANCH} ${stg_prod} ${cluster} ${KUBE_PASS} ${params.FNCM_VERSION} && \
                        deactivate
                        '
                    """
                    def message = "Sending data to FNCM Automation platform and trigger FNCM automation"
                    env.message = message
                    def status = "success"
                    env.status = status
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    echo "Data sent successfully to FNCM automation platform"  
                    } else {

                        echo "FNCM_INTEGRATION value is ${params.FNCM_INTEGRATION}. Skipping stage:- Send data to FNCM Automation platform and trigger FNCM automation"
                    }
                }
            }
        } 
    }
    post {
        success {
            echo 'BAI Deployment Pipeline success!'
        }
        failure {
            echo 'BAI Deployment Pipeline has failed!'
        }
    }
}
