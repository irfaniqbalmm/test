#!/bin/bash

FILENAME=$1

if [ -d "/home/db2inst1/execute_db2_scripts" ]
then
  echo "---------- Creating databases ----------"
  db2 -tvf "/home/db2inst1/execute_db2_scripts/$FILENAME"
else
  echo "---------- Skipping database creation ----------"
fi

echo "--------------------------------------------------"
echo "---------- Database creation completed! ----------"
echo "--------------------------------------------------"
echo
echo "Databases in your DB directory:"
echo
db2 list db directory | grep alias | cut -d '=' -f2 | cut -d ' ' -f2