#!/bin/bash

#Checking the number of arguments are 14
echo $# arguments....
if [ "$#" -ne 3 ]
then
  echo "Incorrect number of arguments"
  exit 1
fi

cluster=$1
kube_pwd=$2
CP4BA_NAMESPACE=$3
OPTARG=$3

# Logging into the cluster to get the logs
oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${kube_pwd} --insecure-skip-tls-verify 
oc project ${CP4BA_NAMESPACE}

#Deleting the custom resource deployments for production
oc get content
oc delete content content --ignore-not-found=true

#Deleting the custom resource deployments for starter
oc get ICP4ACluster
oc delete ICP4ACluster icp4adeploy --ignore-not-found=true

oc get Client
oc get ZenExtension
cd  /opt/cleanupdir/cert-kubernetes/scripts/

./cp4a-uninstall-clean-up.sh -a -s -n $CP4BA_NAMESPACE
./deleteOperator.sh -n $CP4BA_NAMESPACE

pvcdelete() { 
    echo "###########################################"
    echo "Deleting persistent volume claims..............."
    oc get pvc -n $CP4BA_NAMESPACE --no-headers=true | while read each
    do
        pvc=`echo $each | awk '{ print $1 }'`
        echo "Deleting the PVC " $pvc    
        # oc delete pvc $pvc  --ignore-not-found=true 
    done
    echo "###########################################"
} 
pvcdelete 


pvdelete() {
    echo "###########################################"
    echo "Deleting persistent volumes ..............."
    oc get pv -n $CP4BA_NAMESPACE --no-headers=true | while read each
    do
        pv=`echo $each | awk '{ print $1 }'`
        echo "Deleting the PV " $pv
        #oc delete pv $pv --ignore-not-found=true
    done
    echo "###########################################"
}
pvdelete


crddelete() {
    echo "###########################################"
    echo "Deleting CustomResourceDefinitions ..............."

#Adding more crd into the list.
CRD_TYPES="authentications.operator.ibm.com
backups.postgresql.k8s.enterprisedb.io
businessautomationmachinelearnings.icp4a.ibm.com
businessteamsservices.operator.ibm.com
certificaterequests.cert-manager.io
certificates.cert-manager.io
certmanagerconfigs.operator.ibm.com
challenges.acme.cert-manager.io
clients.oidc.security.ibm.com
clusterissuers.cert-manager.io
clusters.postgresql.k8s.enterprisedb.io
commonservices.operator.ibm.com
commonwebuis.operators.ibm.com
contentrequests.icp4a.ibm.com
contents.icp4a.ibm.com
documentprocessingengines.dpe.ibm.com
elasticsearchclusters.elasticsearch.opencontent.ibm.com
federatedsystems.icp4a.ibm.com
foundationrequests.icp4a.ibm.com
foundations.icp4a.ibm.com
ibmlicensingdefinitions.operator.ibm.com
ibmlicensingmetadatas.operator.ibm.com
ibmlicensingquerysources.operator.ibm.com
ibmlicensings.operator.ibm.com
icp4aautomationdecisionservices.icp4a.ibm.com
icp4aclusters.icp4a.ibm.com
icp4adocumentprocessingengines.icp4a.ibm.com
icp4aoperationaldecisionmanagers.icp4a.ibm.com
insightsenginerequests.icp4a.ibm.com
insightsengines.icp4a.ibm.com
issuers.cert-manager.io
kafkabridges.ibmevents.ibm.com
kafkaconnectors.ibmevents.ibm.com
kafkaconnects.ibmevents.ibm.com
kafkamirrormaker2s.ibmevents.ibm.com
kafkamirrormakers.ibmevents.ibm.com
kafkanodepools.ibmevents.ibm.com
kafkarebalances.ibmevents.ibm.com
kafkas.ibmevents.ibm.com
kafkatopics.ibmevents.ibm.com
kafkausers.ibmevents.ibm.com
navconfigurations.foundation.ibm.com
operandbindinfos.operator.ibm.com
operandconfigs.operator.ibm.com
operandregistries.operator.ibm.com
operationaldecisionmanagers.decisions.ibm.com
operatorconfigs.operator.ibm.com
orders.acme.cert-manager.io
poolers.postgresql.k8s.enterprisedb.io
processfederationservers.icp4a.ibm.com
scheduledbackups.postgresql.k8s.enterprisedb.io
strimzipodsets.core.ibmevents.ibm.com
switcheritems.operators.ibm.com
wfpsruntimes.icp4a.ibm.com
workflowruntimes.icp4a.ibm.com
zenextensions.zen.cpd.ibm.com
zenservices.zen.cpd.ibm.com"

echo "########################################## Patching the CRDs ##########################################"
zenser=$(oc patch customresourcedefinition.apiextensions.k8s.io zenservices.zen.cpd.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1)
echo $zenser
opr=$(oc patch customresourcedefinition.apiextensions.k8s.io operandrequests.operator.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1)
echo $opr

crdclient=$(oc patch CustomResourceDefinition/clients.oidc.security.ibm.com -p '{"metadata":{"finalizers":[]}}' --type=merge 2>&1)
echo $crdclient

clientz=$(oc patch customresourcedefinition.apiextensions.k8s.io clients.oidc.security.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1)
echo $clientz
kafkatopics=$(oc patch customresourcedefinition.apiextensions.k8s.io kafkatopics.ibmevents.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1)
echo $kafkatopics
zenet=$(oc patch customresourcedefinition.apiextensions.k8s.io zenextensions.zen.cpd.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1)
echo $zenet


    for crd_type in ${CRD_TYPES}; do
        echo "oc patch customresourcedefinition.apiextensions.k8s.io $crd_type -p '{"metadata":{"finalizers": []}}' --type=merge"
    	oc patch customresourcedefinition.apiextensions.k8s.io $crd_type -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1
        echo "Deleting the crd " $crd_type
        echo "oc patch CustomResourceDefinition/$crd_type -p '{"metadata":{"finalizers": []}}' --type=merge"
        oc patch CustomResourceDefinition/$crd_type -p '{"metadata":{"finalizers": []}}' --type=merge 2>&1
        oc delete CustomResourceDefinition/$crd_type
    done
}

find /data/* ! -name "registry" -exec rm -rf {} +  >/dev/null 2>&1

cd /opt/cleanupdir/cert-kubernetes/scripts/

echo "####################Patching and deleting the zenextensions #######################"
RESOURCE_TYPES="
zenextension.zen.cpd.ibm.com/common-web-ui-zen-extension
zenextension.zen.cpd.ibm.com/content-ban-zen-extension
zenextension.zen.cpd.ibm.com/content-cmis-zen-extension
zenextension.zen.cpd.ibm.com/content-cp4ba-zen-extension
zenextension.zen.cpd.ibm.com/content-cpe-zen-extension
zenextension.zen.cpd.ibm.com/content-graphql-zen-extension
zenextension.zen.cpd.ibm.com/content-iccsap-zen-extension
zenextension.zen.cpd.ibm.com/content-ier-zen-extension
zenextension.zen.cpd.ibm.com/content-insights-engine-zen-apikey-frontdoor-extension
zenextension.zen.cpd.ibm.com/content-insights-engine-zen-extension-cr
zenextension.zen.cpd.ibm.com/content-rr-cp2400up-zen-ext
zenextension.zen.cpd.ibm.com/content-tm-zen-extension
zenextension.zen.cpd.ibm.com/ibm-bts-zen-frontdoor"


 for resource_type in ${RESOURCE_TYPES}; do
    echo oc patch $resource_type -p '{"metadata":{"finalizers":[]}}' --type=merge -n $CP4BA_NAMESPACE
    oc patch $resource_type -p '{"metadata":{"finalizers":[]}}' --type=merge -n $CP4BA_NAMESPACE
    echo oc delete $resource_type -n $CP4BA_NAMESPACE
    oc delete $resource_type -n $CP4BA_NAMESPACE
done

echo "####################Patching and deleting the zenextensions is done #######################"

echo "####################Patching and deleting the zenextensions is starting #######################"

for i in $(oc -n $CP4BA_NAMESPACE get zenextension --no-headers | awk '{print $1}'); do                                                                                                                                                                                                          
    oc -n $CP4BA_NAMESPACE patch zenextension/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    oc -n $CP4BA_NAMESPACE delete zenextension $i --ignore-not-found=true --wait=true
done
echo "####################Patching and deleting the zenextensions is done #######################"
echo "####################Patching and deleting the flinkdeployments #######################"

for i in $(oc -n $CP4BA_NAMESPACE get flinkdeployments.flink.ibm.com --no-headers| awk '{print $1}');do                                                                                                                                                                                          
    oc -n $CP4BA_NAMESPACE patch flinkdeployments.flink.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    oc -n $CP4BA_NAMESPACE delete flinkdeployments.flink.ibm.com $i --ignore-not-found=true --wait=true
done
echo "####################Patching and deleting the flinkdeployments is done #######################"
echo "####################Patching and deleting the clients is starting #######################"

for i in $(oc -n $CP4BA_NAMESPACE get clients.oidc.security.ibm.com --no-headers | awk '{print $1}'); do                                                                                                                                                                                         
    oc -n $CP4BA_NAMESPACE patch clients.oidc.security.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    oc -n $CP4BA_NAMESPACE delete clients.oidc.security.ibm.com $i --ignore-not-found=true --wait=true
done
echo "####################Patching and deleting the clients is done #######################"


crddelete

#oc patch flinkdeployments.flink.ibm.com/content-insights-engine-flink -p '{"metadata":{"finalizers":[]}}' --type=merge &> /dev/null
flinkerror=$(oc patch flinkdeployments.flink.ibm.com/content-insights-engine-flink -p '{"metadata":{"finalizers":[]}}' --type=merge 2>&1)
echo $flinkerror
zenext=$(oc patch customresourcedefinition.apiextensions.k8s.io/zenextensions.zen.cpd.ibm.com -p {metadata:{finalizers:[]}} --type=merge 2>&1)
echo $zenext
echo "########################################## Patching the CRDs Done #####################################"

#Adding patching for operandrequest
echo "########################################## Patching operandrequest ##########################################"
for i in $(oc get operandrequest --no-headers | awk '{print $1}'); do
    echo "oc patch operandrequest/$i"
	oc patch operandrequest/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete operandrequest $i "
	oc delete operandrequest $i --ignore-not-found=true --wait=true
done

#Adding patching for FlinkDeployment
echo "########################################## Patching FlinkDeployment ##########################################"
for i in $(oc get FlinkDeployment --no-headers | awk '{print $1}'); do
    echo "oc patch FlinkDeployment/$i "
	oc patch FlinkDeployment/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete FlinkDeployment $i "
	oc delete FlinkDeployment $i --ignore-not-found=true --wait=true
done

#Adding patching for authentications
echo "########################################## Patching authentications ##########################################"
for i in $(oc get authentications.operator.ibm.com --no-headers | awk '{print $1}'); do
    echo "oc patch authentications.operator.ibm.com/$i"
	oc patch authentications.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete authentications.operator.ibm.com $i"
	oc delete authentications.operator.ibm.com $i --ignore-not-found=true --wait=true
done

#Patching namespacescope
echo "########################################## Patching namespacescope ##########################################"
for i in $(oc get namespacescope --no-headers | awk '{print $1}'); do
    echo "oc patch namespacescope/$i"
	oc patch namespacescope/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete namespacescope $i"
	oc delete namespacescope $i --ignore-not-found=true --wait=true
done

#Patching operandbindinfo
echo "########################################## Patching operandbindinfo ##########################################"
for i in $(oc get operandbindinfo --no-headers | awk '{print $1}'); do
    echo "oc patch operandbindinfo/$i "
	oc patch operandbindinfo/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete operandbindinfo $i "
	oc delete operandbindinfo $i --ignore-not-found=true --wait=true
done

echo "########################################## Login to the cluster again ##########################################"
oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${kube_pwd} --insecure-skip-tls-verify
oc project ${CP4BA_NAMESPACE}

#Patching rolebindings
echo "########################################## Patching rolebindings ##########################################"
for i in $(oc get rolebindings.authorization.openshift.io --no-headers | awk '{print $1}'); do
    echo "oc patch rolebindings.authorization.openshift.io/$i"
	oc patch rolebindings.authorization.openshift.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete rolebindings.authorization.openshift.io $i"
    timeout 5s  oc delete rolebindings.authorization.openshift.io $i > output.txt 2>&1

done


#Patching client
echo "########################################## Patching client ##########################################"
for i in $(oc get clients.oidc.security.ibm.com --no-headers | awk '{print $1}'); do
    echo "oc patch clients.oidc.security.ibm.com/$i "
	oc patch clients.oidc.security.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete clients.oidc.security.ibm.com $i"
	oc delete clients.oidc.security.ibm.com $i --ignore-not-found=true --wait=true
done

#Patching zenextension
echo "########################################## Patching zenextension ##########################################"
for i in $(oc get zenextension --no-headers | awk '{print $1}'); do
    echo "oc patch zenextension/$i"
	oc patch zenextension/$i -p '{"metadata":{"finalizers":[]}}' --type=merge
    echo "oc delete zenextension $i"
	oc delete zenextension $i --ignore-not-found=true --wait=true
done

#Deleting configmap
echo "oc delete configmap common-service-maps -n kube-public"
oc delete configmap common-service-maps -n kube-public


echo "########################################## Login to the cluster again ##########################################"
oc login https://api.${cluster}.cp.fyre.ibm.com:6443 -u kubeadmin -p ${kube_pwd} --insecure-skip-tls-verify
oc project ${CP4BA_NAMESPACE}

#Deleting the image cache from the worker nodes
# oc get nodes -o=custom-columns=NAME:.metadata.name | grep 'worker' | while IFS= read -r nodename; do oc debug node/$nodename -- chroot /host sh -c "crictl images|grep -E 'opencloudio|icr.io|devops.com'|awk '{print $3}'|xargs crictl rmi" ; done
echo "##########################################  Deleting the image cache from the worker node ##########################################"
oc get nodes -o=custom-columns=NAME:.metadata.name | grep 'worker' | while IFS= read -r nodename; 
do 
oc debug node/$nodename -- chroot /host sh -c "crictl images|grep -E 'opencloudio|icr.io|devops.com'|awk '{print $3}'|xargs crictl rmi -q" ;
echo "Clened cache images from $nodename  ..."
done

./cp4a-clean-up.sh -a -n $CP4BA_NAMESPACE -s
oc delete project $CP4BA_NAMESPACE --ignore-not-found=true

echo "Deleting licensing ===== "
licensing=$(oc get csv  -n  ibm-licensing  | grep ibm-licensing-operator  | awk '{ print $1}') && \
oc delete csv $licensing -n ibm-licensing && \
oc delete project ibm-licensing 

echo "Deleting Cert manager ===== "
certmanager=$(oc get csv  -n  ibm-cert-manager  | grep ibm-cert-manager-operator | awk '{ print $1}') && \
oc delete csv $certmanager -n ibm-cert-manager && \
oc delete project ibm-cert-manager
