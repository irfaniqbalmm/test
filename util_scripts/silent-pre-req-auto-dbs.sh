#!/bin/bash

#echo "Your current directory is: $(pwd)"
#echo
#echo "Is your current directory \".../cp4ba-prerequisites/dbscript\"? (y or n):"
#read DIRECTORY_Y_N
#
#if [[ "$DIRECTORY_Y_N" =~ ^(y|n)$ ]]
#then
#  if [ $DIRECTORY_Y_N = "y" ];
#  then
#    echo -e "Path verified by user. Continuing with creating databases..."
#  fi
#  if [ $DIRECTORY_Y_N = "n" ];
#  then
#    echo -e "Change your directory to the expected path. Exiting now."
#    exit 1
#  fi
#else
#  echo "Input only \"y\" or \"n\"! Exiting."
#  exit 1
#fi
#
#echo "Which DB server you using? (ex: DBSERVER1 or DBSERVER2...):"
#read DBSERVER

DBSERVER=$1

if [ -d "$(pwd)/fncm/db2/$DBSERVER" ]
then
  echo "---------- Creating FileNet Content Manager databases ----------"
  for DATABASE_SCRIPT in $(ls ./fncm/db2/$DBSERVER);
  do
    db2 -tvf "./fncm/db2/$DBSERVER/$DATABASE_SCRIPT"
  done
else
  echo "---------- Skipping Creating FileNet Content Manager databases ----------"
fi

if [ -d "$(pwd)/ban/db2/$DBSERVER" ]
then
  echo "---------- Creating Content Navigator database(s) ----------"
  db2 -tvf ./ban/db2/$DBSERVER/createICNDB.sql
else
  echo "---------- Skipping Creating Content Navigator database(s) ----------"
fi

if [ -d "$(pwd)/bas/db2/$DBSERVER" ]
then
  echo "---------- Creating Business Automation Studio database(s) ----------"
  db2 -tvf ./bas/db2/$DBSERVER/create_bas_studio_db.sql
else
  echo "---------- Skipping Creating Business Automation Studio database(s) ----------"
fi

if [ -d "$(pwd)/ae/db2/$DBSERVER" ]
then
  echo "---------- Creating Application Engine & Playback Engine databases ----------"
  db2 -tvf ./ae/db2/$DBSERVER/create_ae_playback_db.sql
  db2 -tvf ./ae/db2/$DBSERVER/create_app_engine_db.sql
else
  echo "---------- Skipping Creating Application Engine & Playback Engine databases ----------"
fi

if [ -d "$(pwd)/adp/db2/$DBSERVER" ]
then
  echo "---------- Creating Document Processing databases ----------"
  # Create base database
  db2 -tvf ./adp/db2/$DBSERVER/1_createADPBaseDB.sql
  # Populate base database tables
  db2 -tvf ./adp/db2/$DBSERVER/2_createADPBaseTable.sql

  # Create empty project databases
  for EMPTY_PROJECT_DATABASE in $(ls -l ./adp/db2/$DBSERVER | grep '3_createADPProject' | sort | awk '{print $9}');
  do
    db2 -tvf "./adp/db2/$DBSERVER/$EMPTY_PROJECT_DATABASE"
  done

  # Populate project databases' tables
  for PROJECT_DATABASE_TABLES in $(ls -l ./adp/db2/$DBSERVER | grep '4_createADPProject' | sort | awk '{print $9}');
  do
    db2 -tvf "./adp/db2/$DBSERVER/$PROJECT_DATABASE_TABLES"
  done

  # Adjust table permissions for project databases
  for PROJECT_DATABASE_PERMISSIONS in $(ls -l ./adp/db2/$DBSERVER | grep '5_createADPProject' | sort | awk '{print $9}');
  do
    db2 -tvf "./adp/db2/$DBSERVER/$PROJECT_DATABASE_PERMISSIONS"
  done

  # Insert project databases to base database as rows
  for INSERT_PROJECT_DATABASE in $(ls -l ./adp/db2/$DBSERVER | grep '6_insertADPProject' | sort | awk '{print $9}');
  do
    db2 -tvf "./adp/db2/$DBSERVER/$INSERT_PROJECT_DATABASE"
  done
else
  echo "---------- Skipping Creating Document Processing databases ----------"
fi


echo "--------------------------------------------------"
echo "---------- Database creation completed! ----------"
echo "--------------------------------------------------"
echo
echo "Databases in your DB directory:"
echo
db2 list db directory | grep alias | cut -d '=' -f2 | cut -d ' ' -f2