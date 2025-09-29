#!/bin/bash
# Shell template for ibm-cp4a-db-ssl-cert-secret

if [[ -f "/opt/cp2103/cert-kubernetes/scripts/cp4ba-prerequisites/propertyfile/cert/db/sql/db-cert.crt" ]]; then
  kubectl delete secret generic "ibm-cp4ba-db-ssl-secret-for-sql" >/dev/null 2>&1
  kubectl create secret generic "ibm-cp4ba-db-ssl-secret-for-sql" --from-file=tls.crt="/opt/cp2103/cert-kubernetes/scripts/cp4ba-prerequisites/propertyfile/cert/db/sql/db-cert.crt"
else
  echo -e "\x1B[1;31m[FAILED]:\x1B[0m Please copy \"db-cert.crt\" into \"/opt/cp2103/cert-kubernetes/scripts/cp4ba-prerequisites/propertyfile/cert/db/sql\" firstly."
  exit 1
fi
