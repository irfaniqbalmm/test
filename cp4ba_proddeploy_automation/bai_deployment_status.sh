#!/bin/bash

# get bai.yaml from ocp
echo "$(TZ='Asia/Kolkata' date) :- Deployment has been started and checking the deployment status."
oc login https://api.$1.cp.fyre.ibm.com:6443 -u kubeadmin -p $2 --insecure-skip-tls-verify && \
echo "https://api.$1.cp.fyre.ibm.com:6443"
oc project $3
echo "project $3"
sleep 15m
oc get InsightsEngine -o yaml > bai.yaml

# call the python function
output=$(python3 validate_bai_deployment.py | tr -d '\n')
echo "Output is: $output"

#To loop for 30 times(5 minute interval 30 times means 2.5 hours)
start=30
while [[ $start -ge 1 ]]
    do
    if [[ $output -ne 1 ]]; then
        oc login https://api.$1.cp.fyre.ibm.com:6443 -u kubeadmin -p $2 --insecure-skip-tls-verify && \
        oc project $3
        echo "project $3"
        oc get InsightsEngine -o yaml > bai.yaml
        # call the python function
        output=$(python3 validate_bai_deployment.py | tr -d '\n')
        # remove content.yaml
        rm -rf bai.yaml

        #verify pull-secret error during the deployment
        python3 pull_secret.py
        if [[ $? -ne 0 ]]; then  # Check the exit code of the Python script
            echo "ImagePullBackOff error in pods. Terminating the pipeline execution"
            exit 1
        fi
        sleep 5m
    else
        echo "BAI deployment completed successfully."
        break
    fi
    echo "$(TZ='Asia/Kolkata' date) :- Deployment is in progress. $((start -= 1)) retries left. Next retry in 10 minutes"
    echo "#########################################################################################"
done
echo "$(TZ='Asia/Kolkata' date) :- BAI deployment completed. Waiting for further 5 minutes..."
sleep 5m
echo "$(TZ='Asia/Kolkata' date) :- BAI deployment completed."
