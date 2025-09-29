#!/bin/bash
# Shell template for ibm-cp4a-db-ssl-cert-secret
value_empty=`cat "$0" | grep "sslmode=\[require|verify-ca|verify-full\]" | wc -l`  >/dev/null 2>&1
if [ $value_empty -ne 0 ] ; then
  echo -e "\x1B[1;31mPlease change line 25# in above script, modify \"--from-literal=sslmode\" to use [require or verify-ca or verify-full].\x1B[0m\n"
  
  echo -e "######################### Example ###################################"
  echo -e "# If DATABASE_SSL_ENABLE=\"True\" and POSTGRESQL_SSL_CLIENT_SERVER=\"False\""
  echo -e "# set '--from-literal=sslmode=require'"
  echo -e "# If DATABASE_SSL_ENABLE=\"True\" and POSTGRESQL_SSL_CLIENT_SERVER=\"True\""
  echo -e "# set '--from-literal=sslmode=verify-ca'"
  echo -e "# or"
  echo -e "# set '--from-literal=sslmode=verify-full'"
  echo -e "######################### Example ###################################"
    
  exit 1
fi

if [[ -f "/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres/root.crt" && -f "/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres/client.crt" && -f "/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres/client.key" ]]; then
  kubectl delete secret generic "ibm-cp4ba-db-ssl-secret-for-db" >/dev/null 2>&1
  kubectl create secret generic "ibm-cp4ba-db-ssl-secret-for-db" \
  --from-file=tls.crt="/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres/client.crt" \
  --from-file=ca.crt="/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres/root.crt" \
  --from-file=tls.key="/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres/client.key" \
  --from-literal=sslmode=verify-ca
  # If DATABASE_SSL_ENABLE="True" and POSTGRESQL_SSL_CLIENT_SERVER="False"
  # set '--from-literal=sslmode=require'
  # If DATABASE_SSL_ENABLE="True" and POSTGRESQL_SSL_CLIENT_SERVER="True"
  # set '--from-literal=sslmode=verify-ca'
  # or
  # set '--from-literal=sslmode=verify-full'
else
  echo -e "\x1B[1;31m[FAILED]:\x1B[0m Please copy \"root.crt\" \"client.crt\" \"client.key\" into \"/opt/ibm-cp-automation/scripts/cp4ba-prerequisites/propertyfile/cert/db/postgres\" first."
  exit 1
fi
