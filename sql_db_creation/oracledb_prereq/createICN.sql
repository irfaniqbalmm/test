alter pluggable database ANSIICN close IMMEDIATE;
DROP PLUGGABLE DATABASE ANSIICN INCLUDING DATAFILES;

CREATE PLUGGABLE DATABASE ANSIICN ADMIN USER ANSIICN IDENTIFIED BY WFQA20zz ROLES=(DBA);

ALTER PLUGGABLE DATABASE ALL OPEN READ WRITE;
alter pluggable database all save state;


ALTER SESSION SET CONTAINER=ANSIICN;

-- create a new user
CREATE USER fncmuser IDENTIFIED BY WFQA20zz;

-- allow the user to connect to the database
GRANT CONNECT TO fncmuser;

-- provide quota on all tablespaces with tables
GRANT UNLIMITED TABLESPACE TO fncmuser;

-- grant privileges to create database objects:
GRANT RESOURCE TO fncmuser;
GRANT CREATE VIEW TO fncmuser;

-- grant access rights to resolve lock issues
GRANT EXECUTE ON DBMS_LOCK TO fncmuser;

-- grant access rights to resolve XA related issues:
GRANT SELECT ON PENDING_TRANS$ TO fncmuser;
GRANT SELECT ON DBA_2PC_PENDING TO fncmuser;
GRANT SELECT ON DBA_PENDING_TRANSACTIONS TO fncmuser;
GRANT EXECUTE ON DBMS_XA TO fncmuser;

-- Create tablespaces
-- Please make sure you change the DATAFILE and TEMPFILE to your Oracle database.
CREATE TABLESPACE fncmuserTS
    DATAFILE '/u02/oradata/DHfncmuserTS.dbf' SIZE 200M REUSE
    AUTOEXTEND ON NEXT 20M
    EXTENT MANAGEMENT LOCAL
    SEGMENT SPACE MANAGEMENT AUTO
    ONLINE
    PERMANENT
;

CREATE TEMPORARY TABLESPACE fncmuserTSTEMP
    TEMPFILE '/u02/oradata/DHfncmuserTSTEMP.dbf' SIZE 200M REUSE
    AUTOEXTEND ON NEXT 20M
    EXTENT MANAGEMENT LOCAL
;


-- Alter existing schema

ALTER USER fncmuser
    DEFAULT TABLESPACE fncmuserTS 
    TEMPORARY TABLESPACE fncmuserTSTEMP;

GRANT CONNECT, RESOURCE to fncmuser;
GRANT UNLIMITED TABLESPACE TO fncmuser;


