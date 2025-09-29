pipeline {
    agent any
    environment {
        PATH = "${env.PATH}:${HOME}/.local/bin"
        TESTRAIL_HOST = 'https://ibm.testrail.io'
    }
    
    parameters {
        base64File (name: 'REPORT', description: 'This is the junit XML report that contains the test cases of your execution.')
    }
    
    stages {
        stage('Copy xml report to server') {
          steps {
            withFileParameter('REPORT') {
                echo 'Copying uploaded report : '
                sh 'cp "$REPORT"  "${WORKSPACE}/report.xml"'
                echo 'Copied the uploaded report to report.xml file : '
                echo 'Printing the report.xml file : '
                sh 'cat "${WORKSPACE}/report.xml"'
            }
          }
        }

        stage('Setup trcli') {
            steps {
                sh '''
                    pip cache purge
                    pip install --user --break-system-packages trcli==1.10.1
                '''
            }
        }

        stage('Prepare trcli-config.yml') {
            steps {
                script {
                    // Retrieve credentials from Jenkins credentials store
                    withCredentials([usernamePassword(credentialsId: 'testrail-credentials',
                        usernameVariable: 'TESTRAIL_USERNAME',
                        passwordVariable: 'TESTRAIL_PASSWORD')]) {
                        echo " run id is ${params.TEST_RUN_ID}"
                        runids = params.TEST_RUN_ID.substring(1)
                        // Generate trcli-config.yml file with parameters
                        writeFile file: 'trcli-config.yml', text: """
                            host: ${TESTRAIL_HOST}
                            project: ${params.PROJECT_NAME}
                            username: ${TESTRAIL_USERNAME}
                            password: ${TESTRAIL_PASSWORD}
                            run_id: ${runids}
                        """
                    }
                }
            }
        }
        
        stage('Parse JUnit and Send to TestRail') {
            steps {
                script {
                    // Print the contents of the config file
                    echo 'Printing the config details : '
                    sh 'cat trcli-config.yml'
                    // Use the uploaded report.xml file from the workspace
                    def testCasesFilePath = "${WORKSPACE}/report.xml"
                    echo "Test cases file path : ${testCasesFilePath}"
                    sh """
                        trcli -y -c "trcli-config.yml" parse_junit -f "${testCasesFilePath}"
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed.'
        }
    }
}
