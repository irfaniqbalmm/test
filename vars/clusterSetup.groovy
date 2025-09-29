
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
                        echo " Gathering cluster data for setting up the new Cluster "
                        clusterName = params.CLUSTER_NAME.toLowerCase()
                        clusterPasssword = params.CLUSTER_PASSWORD
                        ROOT_PASSWORD = params.INFRANODE_PASSWORD
                        env.SSH_URL = "api.${clusterName}.cp.fyre.ibm.com"
                        fips = params.FIPS.toLowerCase()
                        icsp = params.ICSP.toLowerCase()
                        storageClass = params. STORAGE_CLASS.toLowerCase()
                        setupUser = params. SETUP_USER.toLowerCase()
                        pullSecret = params.PULL_SECRET.toLowerCase()
                        proxyTimeSet = params.PROXY_TIME.toLowerCase()
                        

                        stg_prod = 'Prod'
                        if (params.STAGE_OR_PROD == 'Stage') {
                            stg_prod = 'dev'
                        }

                        currentBuild.displayName = "Cluster Setup - ${clusterName}" 
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
                        oc login https://api.${clusterName}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${clusterPasssword} --insecure-skip-tls-verify && \
                        echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                        echo "@@ Running on \$(hostname)" && \
                        echo "@@ Cluster Name: ${clusterName}" && \
                        echo "@@ Fips: ${params.FIPS.toUpperCase()} " && \
                        ocpversion=\$(oc version | grep Server) && \
                        echo "@@ \${ocpversion} "  && \
                        echo "@@ Console link: https://console-openshift-console.apps.${clusterName}.cp.fyre.ibm.com" && \
                        echo "@@ Infra node: api.${clusterName}.cp.fyre.ibm.com" && \
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
        stage('Clone & Setup'){
            steps{
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                    script{
                        
                        env.entitlement = entitlement_key
                        echo """Entitlement Key ${env.entitlement}"""
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
                            yum install -y git  && \
                            yum install -y podman && \
                            echo "Before Git clone"
                            git clone --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            source /opt/automationenv/bin/activate && \
                            pip3 install -r requirements.txt && \
                            pip freeze && \
                            chmod +x * && \
                            cd config && \
                            sed -i "s/ENTITLEMENT_KEY=.*/ENTITLEMENT_KEY=${env.entitlement}/" data.config && \
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
        stage('Fresh Cluster Setup '){
            steps{
                script{
                    def message = "Cluster Setup started in  ${clusterName}"
                    env.message = message
                    def status = "success"
                    env.status = status
                    build job: 'slack-notify', parameters: [
                    string(name:'Status',value:status),
                    string(name:'MESSAGE',value:message)]
                    echo """Cluster setup initiated on ${clusterName}"""
                    sh """
                        sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                        source /opt/automationenv/bin/activate && \
                        cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation && \
                        python3 ./cluster_setup.py ${clusterName} ${clusterPasssword} ${fips} ${icsp} ${storageClass} ${setupUser} ${pullSecret} ${stg_prod} ${proxyTimeSet} && \
                        deactivate
                        '
                    """
                    echo """Cluster setup completed on ${clusterName}"""
                }
            }
        }
       
    }
    post {
        success {
            echo 'Cluster setup completed successfuly'
        }
        failure {
            echo 'Cluster setup failed'
        }
    }
}
