#!/bin/bash

# get content.yaml from ocp
oc login https://api.$1.cp.fyre.ibm.com:6443 -u kubeadmin -p $2 --insecure-skip-tls-verify && \
echo "https://api.$1.cp.fyre.ibm.com:6443"
oc project $3
echo "project $3"

#Patching the certificates belong to the namespace
for i in $(oc get certificate -n $3 --no-headers | awk '{print $1}'); do
    echo "oc patch certificate $i -n $3 -p '{"spec":{"renewBefore":"5m1s"}}' --type=merge" 
    oc patch certificate $i -n $3 -p '{"spec":{"renewBefore":"5m1s", "duration":"1h0m0s"}}' --type=merge
    sleep 1 
done

sleep 5
#Reconcile the pods ibm-content-operator
echo "oc delete pod $(oc get pods -n $3 --no-headers | awk '{print $1}' | grep ibm-content-operator)"
oc delete pod $(oc get pods -n $3 --no-headers | awk '{print $1}' | grep ibm-content-operator)

sleep 5
#Reconcile the pods ibm-cp4a-operator
echo "oc delete pod $(oc get pods -n $3 --no-headers | awk '{print $1}' | grep ibm-cp4a-operator | head -1)"
oc delete pod $(oc get pods -n $3 --no-headers | awk '{print $1}' | grep ibm-cp4a-operator | head -1)