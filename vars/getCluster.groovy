/**
Name: getCluster
Desc: get the cluster data incliding username and password
Parameters:
    None
Returns:
    dictionary :  branch and clone repo
"""
*/
def call() {
    // URL to the JSON file
    sh('curl -u ${GITHUB_USER}:${GITHUB_PASS} -o /tmp/clusters_data.json https://raw.github.ibm.com/dkrishan/Cp4ba-Automation/main/CP4BA_Package/clusters.json')

    // Parse the JSON content
    def jsonSlurper = new groovy.json.JsonSlurper()
    def inputFile = new File("/tmp/clusters_data.json")
    def jsonString = inputFile.text
    def jsonData = jsonSlurper.parseText(jsonString)
    
    env.cluster = params.CLUSTER_NAME.toLowerCase()
    env.ROOT_PASSWORD = jsonData[cluster].root_pwd
    env.KUBE_PASS = jsonData[cluster].kube_pwd
    env.SSH_URL = "api.${cluster}.cp.fyre.ibm.com"
    env.git_branchss=params.BRANCH
    echo "BRANCH: ${params.BRANCH} - ${env.git_branchs}"
}