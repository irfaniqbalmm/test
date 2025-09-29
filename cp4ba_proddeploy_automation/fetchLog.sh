#!/bin/bash


cluster=$1
namespace=$2
kube_pwd=$3
components="$4"
log_dir=logs
tar_file=${log_dir}-${cluster}-${namespace}.tar.gz


#Removing and creating the log directory
rm -rf ${tar_file}
rm -rf ${log_dir}
mkdir -p ${log_dir}

# Logging into the cluster to get the logs
oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${kube_pwd}
oc project ${namespace}

get_log() {
chk=$1
location="/tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/"$(oc project -q)"/content/artifacts"
echo "Log file directory: " $location

echo "Here are all kinds of errors from ansible log!"
echo "Total number of Fatal error found:" >> ./logs/error.log

echo "Downloading the latest operator log file........"
oc cp $(oc get pods | grep content-operator | awk '{print $1}'):$location/$(oc exec -it $(oc get pods | grep content-operator | awk '{print $1}') -- bash -c "ls -t $location | awk '{print $1}' | head -1 | tr -d '\n'")/stdout ./logs/content_operator_log_latest.txt
echo "File download complete: /tmp/content_operator_log_latest.txt"

echo "Downloading the first operator cycle log file........."
oc cp $(oc get pods | grep content-operator | awk '{print $1}'):$location/$(oc exec -it $(oc get pods | grep content-operator | awk '{print $1}') -- bash -c "ls -tr $location | awk '{print $1}' | head -1 | tr -d '\n'")/stdout ./logs/content_operator_log_first.txt
echo "File download complete: /tmp/content_operator_log_first.txt"

foundationloc="/tmp/ansible-operator/runner/icp4a.ibm.com/v1/Foundation/"$(oc project -q)"/content/artifacts"
oc cp $(oc get pods | grep icp4a-foundation-operator | awk '{print $1}'):$foundationloc/$(oc exec -it $(oc get pods | grep icp4a-foundation-operator | awk '{print $1}') -- bash -c "ls -tr $foundationloc | awk '{print $1}' | head -1 | tr -d '\n'")/stdout ./logs/foundation_log_first.txt
echo "File download complete: ./logs/foundation_log_first.txt"

oc exec -it `oc get pod|grep ibm-content-operator |awk '{print $1}'` -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/*/*/artifacts/  -name stdout|xargs cat |grep '0;31m'|wc -l"  >> ./logs/error.log
    
oc exec -it `oc get pod|grep ibm-content-operator |awk '{print $1}'` -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/*/*/artifacts/  -name stdout|xargs cat |grep -B 4 '0;31m'" >> ./logs/error.log

echo "==================================================================================================================================================="

oc exec -it `oc get pod|grep ibm-content-operator |awk '{print $1}'` -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/Content/*/*/artifacts/  -name stdout|xargs cat |tail -30" >> ./logs/error.log

#Cluster info
echo -e "######################################### Cluster info ###################################################### " >> ./logs/systeminfo.log
echo -e "Cluster : ${cluster}" >> ./logs/systeminfo.log
echo "https://console-openshift-console.apps.${cluster}.cp.fyre.ibm.com" >> ./logs/systeminfo.log
echo "kubeadmin/ ${kube_pwd}" >> ./logs/systeminfo.log
oc version >> ./logs/systeminfo.log


# ibm-cp4a-operator
oc exec -it `oc get pod|grep ibm-cp4a-operator |awk '{print $1}'` -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/ICP4ACluster/*/*/artifacts/  -name stdout|xargs cat |tail -30" > ./logs/ibm-cp4a-operator.log
echo "===================================================================================================================================================" >> ./logs/ibm-cp4a-operator.log
echo "Here are all kinds of errors from ansible log!" >> ./logs/ibm-cp4a-operator.log
oc exec -it `oc get pod|grep ibm-cp4a-operator |awk '{print $1}'` -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/ICP4ACluster/*/*/artifacts/  -name stdout|xargs cat |grep '0;31m'|wc -l" >> ./logs/ibm-cp4a-operator.log
oc exec -it `oc get pod|grep ibm-cp4a-operator |awk '{print $1}'` -c operator -- sh -c "find /tmp/ansible-operator/runner/icp4a.ibm.com/v1/ICP4ACluster/*/*/artifacts/  -name stdout|xargs cat |grep -B 4 '0;31m'" >> ./logs/ibm-cp4a-operator.log 

# Pod error details
errorpods=$(oc get pod --no-headers | grep -E -v 'Running|Completed' |  awk '{print $1}')
echo "Error logs " > ./logs/pod-error.log
for pod in ${errorpods}
do
     echo "=============== Error in pod $pod ============= " >> ./logs/pod-error.log
     oc logs $pod  >> ./logs/pod-error.log
done


#Getting the version data
echo -e "######################################### Content ###################################################### " >> ./logs/systeminfo.log
oc exec -it `oc get pod|grep ibm-content-operator |awk '{print $1}'` -c operator -- sh -c "cat /opt/ibm/version.txt " >> ./logs/systeminfo.log


# Set , as the delimiter to fetch each component from the 4th parameter
    IFS=','

    # Read the split words into an array
    # based on space delimiter
    read -ra newarr <<< "$components"

    # Print each value of the array by using
    # the loop
    for component in "${newarr[@]}";
        do
            if [[ ${component}  != "systeminfo" ]]; then
                echo ""  >> ./logs/systeminfo.log
                echo -e "######################################### ${component} ###################################################### " >> ./logs/systeminfo.log
                echo " "  >> ./logs/systeminfo.log

                if [[ ${component}  == "iccsap" ]]; then
                    oc exec -it `oc get pod|grep ${component}-deploy |awk '{print $1}'` -- sh -c "cat /opt/IBM/imageVersion.txt" >> ./logs/systeminfo.log
                else
                    oc exec -it `oc get pod|grep ${component}-deploy |awk '{print $1}'` -- sh -c "cat /opt/ibm/version.txt" >> ./logs/systeminfo.log
                fi

                oc logs `oc get pod|grep ${component}-deploy  |awk '{print $1}'` > ${log_dir}/${component}.log
            fi
        done
    tar -czvf ./${tar_file} ./logs
}

get_log