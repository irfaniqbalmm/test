/**
Name: getClone
Desc: get the clone branch and git repo depend on the branch
Parameters:
    None
Returns:
    dictionary :  branch and clone repo
"""
*/
def call() {
    echo "Setting up the required parameters"
    git_branch=params.BRANCH
    echo "git_branch = ${git_branch}"
    echo "params.BRANCH = ${params.BRANCH}"
    git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.com/icp4a/cert-kubernetes.git"

    if (params.BRANCH == '24.0.1-IF005') {
        git_branch='24.0.1'
        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
        echo "Branch selected is 24.0.1-IF005, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
    }

    if (params.BRANCH == '25.0.1') {
        git_branch='master'
        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
        echo "Branch selected is 25.0.1, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
    }

    if (params.BRANCH == '24.0.0-IF007') {
        git_branch='24.0.0'
        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
        echo "Branch selected is 24.0.0-IF007, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
    }

    if (params.BRANCH == '25.0.0-IF002') {
        git_branch='25.0.0'
        git_clone = "https://${GITHUB_USER}:${GITHUB_PASS}@github.ibm.com/dba/cert-kubernetes.git"
        echo "Branch selected is 25.0.0-IF002, params.BRANCH = ${params.BRANCH} git_branch=${git_branch}, git_clone=${git_clone}"
    }
 
    echo "git_branch = ${git_branch}"
    echo "params.BRANCH = ${params.BRANCH}"
    echo "git_clone path = ${git_clone}"
     
    echo "Setting up the parameters git_clone = ${git_clone} branch is git_branch = ${git_branch}"
    def envMap = [
        branchs: git_branch,
        clones: git_clone]
    return envMap
}
