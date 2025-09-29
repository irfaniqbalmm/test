#!/bin/bash
####################################################################################
# Pleast node that this script will clean up all CP4BA operator and instance,      #
# IAF operator instance, and CPFS operator and instance, including multi-instance. #
# If you have mutiple CP4BA and multi-instance CPFS, but you only want to uninstall#
# one CP4BA and CPFSS instance, or if you have multiple  cloud pak installed and   #
# if you want to only uninstall CP4BA, you CANNOT use this script for cleanup.     #
# This script is for IAF + CPFS + CP4BA only for one CFPS instance.                #
####################################################################################
echo "########################################## Patching the CRDs ##########################################"
oc patch customresourcedefinition.apiextensions.k8s.io zenservices.zen.cpd.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge &> /dev/null
echo "zenservices.zen.cpd.ibm.com Patched"
oc patch customresourcedefinition.apiextensions.k8s.io operandrequests.operator.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge &> /dev/null
echo "operandrequests.operator.ibm.com Patched"
oc patch customresourcedefinition.apiextensions.k8s.io clients.oidc.security.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge &> /dev/null
echo "clients.oidc.security.ibm.com Patched"
oc patch customresourcedefinition.apiextensions.k8s.io kafkatopics.ibmevents.ibm.com -p '{"metadata":{"finalizers": []}}' --type=merge &> /dev/null
echo "kafkatopics.ibmevents.ibm.com Patched"
echo "########################################## Patching the CRDs Done #####################################"
