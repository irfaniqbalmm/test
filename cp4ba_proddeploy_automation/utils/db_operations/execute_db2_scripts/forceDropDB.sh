#!/bin/bash

if [ $# -eq 0 ];
then
  echo "Script usage is ./forceDropDB.sh <database name>"
  echo
  exit 1
fi

DBNAME=$1

db2 connect to $DBNAME
db2 quiesce db immediate force connections
db2 connect reset
db2 deactivate db $DBNAME
db2 drop db $DBNAME

db2 connect to $DBNAME
db2 unquiesce db
db2 connect reset
db2 drop db $DBNAME