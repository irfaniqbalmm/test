#!/bin/bash
# Shell template for ibm-cp4a-ldap-ssl-cert-secret.sh 
if [[ -f "/opt/cp2103/cert-kubernetes/scripts/cp4ba-prerequisites/propertyfile/cert/ldap/ldap-cert.crt" ]]; then
  kubectl delete secret generic "ibm-cp4ba-ldap-ssl-secret" >/dev/null 2>&1
  kubectl create secret generic "ibm-cp4ba-ldap-ssl-secret" --from-file=tls.crt="/opt/cp2103/cert-kubernetes/scripts/cp4ba-prerequisites/propertyfile/cert/ldap/ldap-cert.crt"
else
  echo -e "\x1B[1;31m[FAILED]:\x1B[0m Please copy \"ldap-cert.crt\" into \"/opt/cp2103/cert-kubernetes/scripts/cp4ba-prerequisites/propertyfile/cert/ldap\" firstly."
  exit 1
fi
