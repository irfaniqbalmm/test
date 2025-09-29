alter pluggable database ANSIGCD close IMMEDIATE;
DROP PLUGGABLE DATABASE ANSIGCD INCLUDING DATAFILES;

CREATE PLUGGABLE DATABASE ANSIGCD ADMIN USER ANSIGCD IDENTIFIED BY WFQA20zz ROLES=(DBA);

ALTER PLUGGABLE DATABASE ALL OPEN READ WRITE;
alter pluggable database all save state;

ALTER SESSION SET CONTAINER=ANSIGCD;

-- create tablespace
-- Please make sure you change the DATAFILE and TEMPFILE to your Oracle database.
CREATE TABLESPACE fncmuserDATATS DATAFILE '/u02/oradata/fncmuserDATATS1.dbf' SIZE 200M REUSE AUTOEXTEND ON NEXT 20M EXTENT MANAGEMENT LOCAL SEGMENT SPACE MANAGEMENT AUTO ONLINE PERMANENT;
CREATE TEMPORARY TABLESPACE fncmuserDATATSTEMP TEMPFILE '/u02/oradata/fncmuserDATATSTEMP1.dbf' SIZE 200M REUSE AUTOEXTEND ON NEXT 20M EXTENT MANAGEMENT LOCAL;

-- create a new user for fncmuser
CREATE USER fncmuser PROFILE DEFAULT IDENTIFIED BY WFQA20zz DEFAULT TABLESPACE fncmuserDATATS TEMPORARY TABLESPACE fncmuserDATATSTEMP ACCOUNT UNLOCK;
-- provide quota on all tablespaces with GCD tables
ALTER USER fncmuser QUOTA UNLIMITED ON fncmuserDATATS;
ALTER USER fncmuser DEFAULT TABLESPACE fncmuserDATATS;
ALTER USER fncmuser TEMPORARY TABLESPACE fncmuserDATATSTEMP;

-- allow the user to connect to the database
GRANT CONNECT TO fncmuser;
GRANT ALTER session TO fncmuser;

-- grant privileges to create database objects
GRANT CREATE SESSION TO fncmuser;
GRANT CREATE TABLE TO fncmuser;
GRANT CREATE VIEW TO fncmuser;
GRANT CREATE SEQUENCE TO fncmuser;

-- grant access rights to resolve XA related issues
GRANT SELECT on pending_trans$ to fncmuser;
GRANT SELECT on dba_2pc_pending to fncmuser;
GRANT SELECT on dba_pending_transactions to fncmuser;
GRANT SELECT on DUAL to fncmuser;
GRANT SELECT on product_component_version to fncmuser;
GRANT SELECT on USER_INDEXES to fncmuser;
GRANT EXECUTE ON DBMS_XA TO fncmuser;

