/**
Name: cleanProject
Desc: cleaning the projects
Parameters:
    cluster, ROOT_PASSWORD, KUBE_PASS, git_branch, git_clone
Returns:
    None
"""
*/
def call(String cluster, String ROOT_PASSWORD, String KUBE_PASS, String git_branch, String git_clone) {
    if (params.CLEANUP.toUpperCase() =='YES') {
        pjt = params.PROJECT_CLEAN
        
        echo """Cleaning the project ${pjt} using KC script in ${cluster} """
        sh """
            sshpass -p '${ROOT_PASSWORD}' ssh -o StrictHostKeyChecking=no root@${env.SSH_URL} '
            echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
            echo "Running on \$(hostname)" && \
            echo "Cluster Name: ${cluster}" && \
            echo "Project Name to clean : ${pjt}" && \
            echo "Clonning from  -b ${git_branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone} " && \
            echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" && \
            if oc get project ${pjt} > /dev/null 2>&1; then
                echo "✅ Project '${pjt}' exists. Proceeding with cleanup..." && \
                cd /opt && \
                rm -rf cleanupdir/ && \
                mkdir cleanupdir/ && \
                cd cleanupdir/ && \
                git clone -b ${git_branch} --depth 1 --recurse-submodules --shallow-submodules ${git_clone} && \
                cd /opt/cleanupdir/cert-kubernetes/scripts/ && \
                chmod +x cp4a-clean-up.sh && \
                echo "Modifying the cp4a-clean-up.sh" && \
                sed -i "s/while true;/CLEAN_CRDS="true";\n while false;/g" /opt/cleanupdir/cert-kubernetes/scripts/cp4a-clean-up.sh
                echo "downloading kccleanup.sh" && \
                curl -sSfL -u "${GITHUB_USER}:${GITHUB_PASS}" -o kccleanup.sh https://raw.github.ibm.com/Cp4ba-auto/Cp4ba-Automation/main/cp4ba_proddeploy_automation/kccleanup.sh && \
                echo "Giving permission to kccleanup.sh" && \
                chmod +x kccleanup.sh && \
                oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${KUBE_PASS} --insecure-skip-tls-verify && \
                oc project ${pjt} && \
                echo "Running the kccleanup.sh" && \
                ./kccleanup.sh  ${cluster} ${KUBE_PASS} ${pjt} && \
                cd /opt && \
                rm -rf cleanupdir/ && \
                echo "Cleaned data folder"
            else
                echo "❌ Project '${pjt}' does not exist in cluster '${cluster}'. Skipping cleanup and exiting." && \
                exit 1
            fi && \
            echo "Done with Cleanup."
            '
        """
    }
    echo " Project cleaned."
}
