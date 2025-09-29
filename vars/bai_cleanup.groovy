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
                        def jsonSlurper = new groovy.json.JsonSlurper()
                        def inputFile = new File("/tmp/clusters_data.json")
                        def jsonString = inputFile.text
                        def jsonData = jsonSlurper.parseText(jsonString)
                        cluster = params.CLUSTER_NAME.toLowerCase()
                        ROOT_PASSWORD = jsonData[cluster].root_pwd
                        KUBE_PASS = jsonData[cluster].kube_pwd
                        env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
                        currentBuild.displayName = "${cluster}-${params.PROJECT_CLEAN}"
                        git_branch='main'
                        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes-bai.git"
                    }
                }
            }
        }
        stage('Clone & Setup'){
            steps{ 
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS'), string(credentialsId: 'entitlement_key', variable: 'entitlement_key'), string(credentialsId: 'entitlement_prod', variable: 'entitlement_prod'), string(credentialsId: 'pull_secret_token', variable: 'pull_secret_token')]) {
                    script{
                        git_clone=git_clone
                        pjt = params.PROJECT_CLEAN
                        sh """
                            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} ' \
                            cd /opt && \
                            rm -rf Cp4ba-Automation && \
                            yum install -y python3.12 && \
                            python3.12 -m venv /opt/automationenv && \
                            echo "Virtual env creation done." && \
                            echo "Running on \$(hostname)" && \
                            git clone -b main --depth 1 --recurse-submodules --shallow-submodules https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dkrishan/Cp4ba-Automation.git && \
                            cd /opt/Cp4ba-Automation/cp4ba_proddeploy_automation/ && \
                            source /opt/automationenv/bin/activate && \
                            pip3 install -r requirements.txt && \
                            pip freeze && \
                            chmod +x * && \
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
        stage('Clean up Project') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GITHUB_USER', passwordVariable: 'GITHUB_PASS')]) {
                    script {
                            pjt = params.PROJECT_CLEAN
                            echo """Cleaning the BAI Standalone deployment in project ${pjt} """

                                sh """
                                sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
                                    set -e
                                    echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                                    echo "Running on \$(hostname)" && \
                                    echo "Cluster Name: ${cluster}" && \
                                    echo "Project Name to clean : ${pjt}" && \
                                    echo "Clonning from  -b ${git_branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone} " && \
                                    echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
                                    cd /opt && \
                                    rm -rf cleanupdir/ && \
                                    mkdir cleanupdir/ && \
                                    cd cleanupdir/ && \
                                
                                    echo "Cloning cert-kubernetes-bai repository..." && \
                                    git clone -b ${git_branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone} && \
                                    cd /opt/cleanupdir/cert-kubernetes-bai/scripts/ && \
                                
                                    echo "Logging into cluster..." && \
                                    oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                                
                                    echo "Checking the project ${pjt} exists..." && \
                                    if ! oc get project ${pjt} >/dev/null 2>&1; then
                                        echo "ERROR: Project ${pjt} does not exist in the cluster ${cluster}."
                                        exit 1
                                    fi && \
                                    oc project ${pjt} && \
                                    echo "Project ${pjt} exists, continuing cleanup..." && \
                                
                                    echo "Running bai-deleteoperator.sh..." && \
                                    chmod +x bai-deleteoperator.sh && \
                                    ./bai-deleteoperator.sh -n ${pjt} && \
                                
                                    echo "Running bai-clean-up.sh..." && \
                                    chmod +x bai-clean-up.sh && \
                                    printf "2\\nNo\\ny\\n" | ./bai-clean-up.sh -a -n ${pjt} && \
                                
                                    echo "Deleting IBM CRDs..." && \
                                    crds=\$(kubectl get crds | grep -i "ibm" | awk "{print \\\$1}") && \
                                    if [ -n "\$crds" ]; then \
                                        set +e; \
                                        echo "\$crds" | xargs kubectl delete crds --force --timeout=30s; \
                                        if [ \$? -ne 0 ]; then \
                                            echo "Force delete failed or stuck, patching finalizers..."; \
                                            echo "\$crds" | xargs -I {} kubectl patch crds {} -p "{\\"metadata\\":{\\"finalizers\\":[]}}" --type=merge; \
                                            echo "\$crds" | xargs kubectl delete crds --force; \
                                        fi; \
                                        set -e; \
                                    else \
                                        echo "No IBM CRDs found."; \
                                    fi && \
                                
                                    oc get nodes -o=custom-columns=NAME:.metadata.name | grep "worker" | while read -r nodename; do
                                        echo "Cleaning images on \$nodename ..."
                                        oc debug node/\$nodename -- chroot /host sh -c '"'"'crictl images | grep -E "opencloudio|icr.io|devops.com" | awk "{print \$3}" | xargs -r crictl rmi || true'"'"'
                                    done && \
                                
                                    cd /opt && \
                                    rm -rf cleanupdir/ && \
                                    echo "Cleaned data folder" && \
                                    echo "Cleanup completed"
                                '
                                """
                        echo " Project cleaned."
                    }
                }
            }
        }   
    }
    post {
        success {
            echo 'BAI Standalone deployment cleanup is successful!'
        }
        failure {
            echo 'Failed to cleanup BAI Standalone deployment!'
        }
    }
}
