alter pluggable database ANSIOS1 close IMMEDIATE;
DROP PLUGGABLE DATABASE ANSIOS1 INCLUDING DATAFILES;

CREATE PLUGGABLE DATABASE ANSIOS1 ADMIN USER ANSIOS1 IDENTIFIED BY WFQA20zz ROLES=(DBA);

ALTER PLUGGABLE DATABASE ALL OPEN READ WRITE;
alter pluggable database all save state;


ALTER SESSION SET CONTAINER=fncmuserEE;
-- create tablespace
-- Change DATAFILE/TEMPFILE as required by your configuration
CREATE TABLESPACE fncmuserDATATS DATAFILE '/u02/oradata/fncmuserDATATS.dbf' SIZE 200M REUSE AUTOEXTEND ON NEXT 20M EXTENT MANAGEMENT LOCAL SEGMENT SPACE MANAGEMENT AUTO ONLINE PERMANENT;
CREATE TEMPORARY TABLESPACE fncmuserDATATSTEMP TEMPFILE '/u02/oradata/fncmuserDATATSTEMP.dbf' SIZE 200M REUSE AUTOEXTEND ON NEXT 20M EXTENT MANAGEMENT LOCAL;

-- create a new user for fncmuser
CREATE USER fncmuser PROFILE DEFAULT IDENTIFIED BY WFQA20zz DEFAULT TABLESPACE fncmuserDATATS TEMPORARY TABLESPACE fncmuserDATATSTEMP ACCOUNT UNLOCK;

-- provide quota on all tablespaces with BPM tables
ALTER USER fncmuser QUOTA UNLIMITED ON fncmuserDATATS;
ALTER USER fncmuser DEFAULT TABLESPACE fncmuserDATATS;
ALTER USER fncmuser TEMPORARY TABLESPACE fncmuserDATATSTEMP;

-- allow the user to connect to the database
GRANT CONNECT TO fncmuser;
GRANT ALTER session TO fncmuser;

-- grant privileges to create database objects
GRANT CREATE SESSION to fncmuser;
GRANT CREATE TABLE to fncmuser;
GRANT CREATE VIEW to fncmuser;
GRANT CREATE SEQUENCE to fncmuser;
GRANT CREATE PROCEDURE TO fncmuser;

-- grant access rights to resolve XA related issues
GRANT SELECT on pending_trans$ to fncmuser;
GRANT SELECT on dba_2pc_pending to fncmuser;
GRANT SELECT on dba_pending_transactions to fncmuser;
GRANT SELECT on DUAL to fncmuser;
GRANT SELECT on product_component_version to fncmuser;
GRANT SELECT on USER_INDEXES to fncmuser;
GRANT EXECUTE ON DBMS_XA TO fncmuser;

