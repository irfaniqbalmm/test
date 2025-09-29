#!/bin/bash
####################################################################################
# Pleast node that this script will clean up all CP4BA operator and instance,      #
# IAF operator instance, and CPFS operator and instance, including multi-instance. #
# If you have mutiple CP4BA and multi-instance CS, but you only want to uninstall  #
# one CP4BA and CS instance, or if you have multiple  cloud pak installed and if   #
# you want to only uninstall CP4BA, you CANNOT use this script for cleanup. This   #
# script is for IAF + CS + CP4BA only for one CS instance.                         #
####################################################################################
# This script was modified to be a silent install for automation pipeline.
IAF_PROJECT=`oc project -q`

            if [[ "$IAF_PROJECT" == openshift* ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'openshift' or start with 'openshift'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == kube* ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'kube' or start with 'kube'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "services" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'services'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "default" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'default'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "calico-system" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'calico-system'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "ibm-cert-store" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'ibm-cert-store'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "ibm-observe" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'ibm-observe'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "ibm-odf-validation-webhook" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'default'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            elif [[ "$IAF_PROJECT" == "ibm-system" ]]; then
                echo -e "\x1B[1;31mThe current namespace should not be 'ibm-system'. It should be the namespace where CP4BA is installed. The script aborted. \x1B[0m"
                exit 1
            fi

HELP="false"
SKIP_CONFIRM="false"

while getopts 'hs' OPTION; do
  case "$OPTION" in
    h)
      HELP="true"
      ;;
    s)
      SKIP_CONFIRM="true"
      ;;
    ?)
      HELP="true"
      ;;
  esac
done
shift "$(($OPTIND -1))"

if [[ $HELP == "true" ]]; then
  echo "This script completely uninstalls IBM Automation Foundation and IBM Common Services."
  echo "Usage: $0 -h -s"
  echo " -h prints this help message"
  echo " -s skips confirmation message"
  echo "The following prerequisites are checked:"
  echo "1. oc command must be installed and be logged in to your cluster."
  echo "2. Environment variable IAF_PROJECT must be set to the name of an existing project."
  exit 0
fi

if ! [ -x "$(command -v oc)" ]; then
  echo 'Error: oc is not installed.' >&2
  exit 1
fi

oc project
if [ $? -gt 0 ]; then
  echo "oc login required" && exit 1
fi

if [ -z $IAF_PROJECT ]; then
  echo "ERROR: no value for IAF_PROJECT" && exit 1
fi

# validate IAF_PROJECT env var is for existing project
if [ -z "$(oc get project ${IAF_PROJECT} 2>/dev/null)" ]; then
  echo "Error: project ${IAF_PROJECT} does not exist. Specify an existing project where IAF is installed." && exit 1
fi

echo
echo "Congratulations, you passed all the prereq checks!"
echo

if [[ $SKIP_CONFIRM == "false" ]]; then
  echo "This script will uninstall IBM Cloud Pak for Business Autmation,IBM Automation Foundation and IBM Common Services, including deleting the namespace where your CP4BA instance is installed, as well as deleting ibm-common-services namespaces for CS single instance, or cs-control namespace for CS multi-instance."
  echo "If you have mulitple IBM Cloud Pak installed in the same cluster, or you have multiple CP4BA with multiple CS instances, and you only want to uninstall one instance of CP4BA and CS, do not use this script for cleaning up."
  echo "Use -s option to skip this confirmation, -h for help."
  read -p "Enter Y or y to continue: " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "You chose to NOT continue.  Bye."
    exit 0
  fi
  echo "OK. Continuing...."
  sleep 2
  echo
fi

oc project ${IAF_PROJECT}

echo "CP4BA and IAF uninstallation is in progress..."
oc delete icp4acluster --all --ignore-not-found=true --wait=true
oc delete content --all --ignore-not-found=true --wait=true
oc delete foundation --all --ignore-not-found=true --wait=true

i=0
while [ $i -le 30 ]
do
oc get pod -n $IAF_PROJECT|grep -q "zen-metastoredb"
if [ $? -ne 0 ]; then
break
else
echo "Wait until zen-metastoredb is uninstalled."
sleep 20
let i++
fi
done

i=0
while [ $i -le 30 ]
do
oc get pod -n $IAF_PROJECT|grep -q "cpe-deploy"
if [ $? -ne 0 ]; then
break
else
echo "Wait until CPE is uninstalled..."
sleep 20
fi
done

for i in `oc get cartridgerequirements --no-headers|awk '{print $1}'`;do oc patch cartridgerequirements/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete cartridgerequirements $i --ignore-not-found=true --wait=true;done
for i in `oc get automationbase --no-headers|awk '{print $1}'`;do oc patch automationbase/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete automationbase $i --ignore-not-found=true --wait=true;done
oc delete kafka,elasticsearch --all --ignore-not-found=true --wait=true
oc delete zenservice --all --ignore-not-found=true --wait=true
for i in `oc get cartridge --no-headers|awk '{print $1}'`;do oc patch cartridge/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete cartridge $i --ignore-not-found=true --wait=true;done
for i in `oc get kafkaclaim --no-headers|awk '{print $1}'`;do oc patch kafkaclaim/$i -p '{"metadata":{"finalizers":[]}}' --type=merge; oc delete kafkaclaim $i --ignore-not-found=true --wait=true;done
for i in `oc get kafkacomposite --no-headers|awk '{print $1}'`;do oc patch kafkacomposite/$i -p '{"metadata":{"finalizers":[]}}' --type=merge; oc delete kafkacomposite $i --ignore-not-found=true --wait=true;done
for i in `oc get clients.oidc.security.ibm.com --no-headers|awk '{print $1}'`;do oc patch clients.oidc.security.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge; oc delete clients.oidc.security.ibm.com $i --ignore-not-found=true --wait=true;done
oc delete operandrequest --force --grace-period=0 --all --ignore-not-found=true --wait=true
oc delete commonservice,operandregistry,operandconfig --all --ignore-not-found=true --wait=true
oc delete nss --all --ignore-not-found=true --wait=true
oc delete csv,sub --all --ignore-not-found=true --wait=true
oc delete csv,sub -n openshift-operators --all --ignore-not-found=true --wait=true
oc get pv |grep "operator-shared-pv-.*"|grep -E "Available|Failed"|awk '{print $1}'|xargs oc delete pv
for i in `oc get authentications.operator.ibm.com --no-headers|awk '{print $1}'`;do oc patch authentications.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete authentications.operator.ibm.com $i --ignore-not-found=true --wait=true;done
for i in `oc get operandrequest --no-headers|awk '{print $1}'`;do oc patch operandrequest/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete operandrequest $i --ignore-not-found=true --wait=true;done
for i in `oc get namespacescope  --no-headers|awk '{print $1}'`;do oc patch namespacescope/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete namespacescope $i --ignore-not-found=true --wait=true ;done
for i in `oc get operandbindinfo  --no-headers|awk '{print $1}'`;do oc patch operandbindinfo/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete operandbindinfo $i --ignore-not-found=true --wait=true ;done
for i in `oc get policycontroller.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch policycontroller.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete policycontroller.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get authentications.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch authentications.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete authentications.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get nginxingresses.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch nginxingresses.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete nginxingresses.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get oidcclientwatcher.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch oidcclientwatcher.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete oidcclientwatcher.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get oidcclientwatchers.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch oidcclientwatchers.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete oidcclientwatchers.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get commonui.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch commonui.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete commonui.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get commonui1.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch commonui1.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete commonui1.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get commonwebuis.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch commonwebuis.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete commonwebuis.operator.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get commonwebuis.operators.ibm.com  --no-headers|awk '{print $1}'`;do oc patch commonwebuis.operators.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete commonwebuis.operators.ibm.com $i --ignore-not-found=true --wait=true ;done
for i in `oc get platformapis.operator.ibm.com  --no-headers|awk '{print $1}'`;do oc patch platformapis.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge ;oc delete platformapis.operator.ibm.com $i ;done
oc delete cluster --all --ignore-not-found=true --wait=true
oc delete deploy,sts,job,svc --all --ignore-not-found=true --wait=true


echo "Common Services uninstallation is in progress..."
oc delete operandrequest --all -n ibm-common-services --force --grace-period=0 --ignore-not-found=true --wait=true
oc delete commonservice,operandregistry,operandconfig --all -n ibm-common-services --ignore-not-found=true --wait=true
oc delete nss --all -n ibm-common-services --ignore-not-found=true --wait=true
oc delete sub,csv --all -n ibm-common-services --ignore-not-found=true --wait=true
oc delete deploy,sts,job,svc --all -n ibm-common-services --ignore-not-found=true --wait=true

oc delete operandrequest --all -n cs-control --force --grace-period=0 --ignore-not-found=true --wait=true
oc delete nss --all -n cs-control --ignore-not-found=true --wait=true
oc delete sub,csv --all -n cs-control --ignore-not-found=true --wait=true
oc delete deploy,sts,job,svc --all -n cs-control --ignore-not-found=true --wait=true

for i in `oc get operandrequest -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch operandrequest/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete operandrequest $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get namespacescope -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch namespacescope/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete namespacescope $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get operandbindinfo -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch operandbindinfo/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete operandbindinfo $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get policycontroller.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch policycontroller.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete policycontroller.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get authentications.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch authentications.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete authentications.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get nginxingresses.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch nginxingresses.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete nginxingresses.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get oidcclientwatcher.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch oidcclientwatcher.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete oidcclientwatcher.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get oidcclientwatchers.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch oidcclientwatchers.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete oidcclientwatchers.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get commonui.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch commonui.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete commonui.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get commonui1.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch commonui1.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete commonui1.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get commonwebuis.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch commonwebuis.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete commonwebuis.operator.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get commonwebuis.operators.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch commonwebuis.operators.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete commonwebuis.operators.ibm.com $i --ignore-not-found=true --wait=true -n ibm-common-services;done
for i in `oc get platformapis.operator.ibm.com -n ibm-common-services --no-headers|awk '{print $1}'`;do oc patch platformapis.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete platformapis.operator.ibm.com $i -n ibm-common-services;done

for i in `oc get operandrequest -n cs-control --no-headers|awk '{print $1}'`;do oc patch operandrequest/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control ;oc delete operandrequest $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get namespacescope -n cs-control --no-headers|awk '{print $1}'`;do oc patch namespacescope/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete namespacescope $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get operandbindinfo -n cs-control --no-headers|awk '{print $1}'`;do oc patch operandbindinfo/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete operandbindinfo $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get policycontroller.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch policycontroller.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete policycontroller.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get authentications.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch authentications.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete authentications.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get nginxingresses.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch nginxingresses.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete nginxingresses.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get oidcclientwatcher.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch oidcclientwatcher.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete oidcclientwatcher.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get oidcclientwatchers.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch oidcclientwatchers.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete oidcclientwatchers.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get commonui.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch commonui.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete commonui.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get commonui1.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch commonui1.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete commonui1.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get commonwebuis.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch commonwebuis.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete commonwebuis.operator.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get commonwebuis.operators.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch commonwebuis.operators.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete commonwebuis.operators.ibm.com $i --ignore-not-found=true --wait=true -n cs-control;done
for i in `oc get platformapis.operator.ibm.com -n cs-control --no-headers|awk '{print $1}'`;do oc patch platformapis.operator.ibm.com/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete platformapis.operator.ibm.com $i -n cs-control;done

echo "Deleting IAF subscriptions and CSVs"
IAF_OPERATORS=("iaf-demo-cartridge"
               "ibm-automation-eventprocessing"
               "ibm-automation-ai"
               "ibm-automation-core"
               "ibm-automation-flink"
               "ibm-automation"
               "ibm-cloud-databases-redis-operator"
               "ibm-common-service-operator"
               "ibm-automation-elastic")

SUBS=$(oc get subscriptions.operators.coreos.com -n ${IAF_PROJECT} -o jsonpath='{range .items[*]}{@.spec.name}{"|"}{@.metadata.name}{"|"}{@.status.currentCSV}{"\n"}')
for SUB in $SUBS
do
  SUB_DATA=($(echo $SUB | tr "|" "\n"))
  if [[ ${IAF_OPERATORS[*]} =~ "${SUB_DATA[0]}" ]]; then
     oc delete subscriptions.operators.coreos.com ${SUB_DATA[1]} -n ${IAF_PROJECT}
     oc delete csv ${SUB_DATA[2]} -n ${IAF_PROJECT}
  fi
done

echo "Delete catalog sources"
oc delete catalogsource ibm-db2u-operator -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource ibm-db2uoperator-catalog -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource abp-operators -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource iaf-operators -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource iaf-core-operators -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource abp-demo-cartridge -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource iaf-demo-cartridge -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource ibm-cp-data-operator-catalog -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource opencloud-operators -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource ibm-operator-catalog -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource ibm-cp4a-operator-catalog -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource bts-operator -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource cloud-native-postgresql-catalog  -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource ibm-automation-foundation-core-catalog -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource ibm-cp-automation-foundation-catalog -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource insight-engine-operator -n openshift-marketplace --ignore-not-found=true --wait=true
oc delete catalogsource insight-engine-operators -n openshift-marketplace --ignore-not-found=true --wait=true

oc get apiservice v1beta1.webhook.certmanager.k8s.io 2>/dev/null
if [ $? -eq 0 ]; then
  echo "delete apiservice v1beta1.webhook.certmanager.k8s.io"
  oc delete apiservice v1beta1.webhook.certmanager.k8s.io
fi

oc get apiservice v1.metering.ibm.com 2>/dev/null
if [ $? -eq 0 ]; then
  echo "delete apiservice v1.metering.ibm.com"
  oc delete apiservice v1.metering.ibm.com
fi

echo "Delete common service webhook"
oc delete ValidatingWebhookConfiguration cert-manager-webhook --ignore-not-found
oc delete MutatingWebhookConfiguration cert-manager-webhook ibm-common-service-webhook-configuration namespace-admission-config --ignore-not-found
oc delete validatingwebhookconfiguration ibm-cs-ns-mapping-webhook-configuration

echo "Delete configmaps from kube-public namespace"
oc delete cm common-service-maps ibm-common-services-status -n kube-public --ignore-not-found

echo "delete IAF CRDs"
for i in `oc get crd|grep -E "icp4a.ibm.com|automation.ibm.com|ai.ibm.com|zen.cpd.ibm.com"|awk '{print $1}'`;do oc patch crd/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete crd $i;done
for i in `oc get crd --no-headers | grep -i "crossplane\|kafka" | awk '{print $1}'`;do oc patch crd/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete crd $i;done

echo "cleaning up openshift-operators"
oc -n openshift-operators get cm |grep -E "iaf|ibm"|awk '{print $1}'|xargs oc delete cm -n openshift-operators   --ignore-not-found=true
oc -n openshift-operators get sa |grep -E "iaf|ibm"|awk '{print $1}'|xargs oc delete sa -n openshift-operators  --ignore-not-found=true
oc delete lease --all -n openshift-operators --ignore-not-found=true
oc delete pvc --all -n openshift-operators --ignore-not-found=true
oc delete role.rbac.authorization.k8s.io iaf-insights-engine-operator-leader-election-role -n openshift-operators
oc delete secret admin.registrykey -n openshift-operators
echo "final cleaning up all pods"
oc delete pod --all --grace-period=0 --force
oc delete pvc --all --ignore-not-found=true --wait=true
oc delete pod --all -n ibm-common-services --grace-period=0 --force
oc delete pod --all -n cs-control --grace-period=0 --force
for i in `oc get rolebindings.authorization.openshift.io|awk '{print $1}'`;do oc patch rolebindings.authorization.openshift.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete rolebindings.authorization.openshift.io $i;done
for i in `oc get rolebindings.rbac.authorization.k8s.io|awk '{print $1}'`;do oc patch rolebindings.rbac.authorization.k8s.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge;oc delete rolebindings.rbac.authorization.k8s.io $i;done
for i in `oc get rolebindings.authorization.openshift.io -n ibm-common-services|awk '{print $1}'`;do oc patch rolebindings.authorization.openshift.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge  -n ibm-common-services;oc delete rolebindings.authorization.openshift.io $i  -n ibm-common-services;done
for i in `oc get rolebindings.rbac.authorization.k8s.io -n ibm-common-services|awk '{print $1}'`;do oc patch rolebindings.rbac.authorization.k8s.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n ibm-common-services;oc delete rolebindings.rbac.authorization.k8s.io $i -n ibm-common-services;done
for i in `oc get rolebindings.authorization.openshift.io -n cs-control|awk '{print $1}'`;do oc patch rolebindings.authorization.openshift.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge  -n cs-control;oc delete rolebindings.authorization.openshift.io $i  -n cs-control;done
for i in `oc get rolebindings.rbac.authorization.k8s.io -n cs-control|awk '{print $1}'`;do oc patch rolebindings.rbac.authorization.k8s.io/$i -p '{"metadata":{"finalizers":[]}}' --type=merge -n cs-control;oc delete rolebindings.rbac.authorization.k8s.io $i -n cs-control;done
oc project default

if [[ ${IAF_PROJECT} != "openshift-operators" ]]; then

echo "Deleting project ${IAF_PROJECT}"
oc delete project ${IAF_PROJECT}

echo "Wait until project ${IAF_PROJECT} is completely deleted."
count=0
while :
do
  oc get project ${IAF_PROJECT} 2>/dev/null
  if [[ $?>0 ]]; then
    echo "Project ${IAF_PROJECT} deletion successful"
  break
  else
    ((count+=1))
  if (( count <= 36 )); then
    echo "Waiting for project ${IAF_PROJECT} to be terminated.  Recheck in 10 seconds"
    sleep 10
  else
    echo "Deleting project ${IAF_PROJECT} is taking too long and giving up"
      oc get project ${IAF_PROJECT} -o yaml
    exit 1
  fi
  fi
done

fi

echo "Deleting project ibm-common-services"
oc delete project ibm-common-services

echo "Wait until project ibm-common-services is completely deleted."
count=0
while :
do
  oc get project ibm-common-services 2>/dev/null
  if [[ $?>0 ]]; then
    echo "Project ibm-common-services deletion successful"
  break
  else
    ((count+=1))
  if (( count <= 36 )); then
    echo "Waiting for project ibm-common-services to be terminated.  Recheck in 10 seconds"
    sleep 10
  else
    echo "Deleting project ibm-common-services is taking too long and giving up"
      oc get project ibm-common-services -o yaml
    exit 1
  fi
  fi
done

echo "Deleting project cs-control"
oc delete project cs-control
echo "Wait until project cs-control is completely deleted."
count=0
while :
do
  oc get project cs-control 2>/dev/null
  if [[ $?>0 ]]; then
    echo "Project cs-control deletion successful"
  break
  else
    ((count+=1))
  if (( count <= 36 )); then
    echo "Waiting for project cs-control to be terminated.  Recheck in 10 seconds"
    sleep 10
  else
    echo "Deleting project cs-control is taking too long and giving up"
      oc get project cs-control -o yaml
    exit 1
  fi
  fi
done
echo "Done uninstalling CP4BA, IAF, and CS."