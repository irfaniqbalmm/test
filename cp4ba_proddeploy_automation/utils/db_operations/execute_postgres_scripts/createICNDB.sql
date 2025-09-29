-- create user dbuser1
CREATE ROLE dbuser1 WITH INHERIT LOGIN ENCRYPTED PASSWORD 'Password@1';

-- please modify location follow your requirement
create tablespace icndbind_tbs owner dbuser1 location '/pgsqldata/icndbind';
grant create on tablespace icndbind_tbs to dbuser1; 

-- create database icndbind
create database icndbind owner dbuser1 tablespace icndbind_tbs template template0 encoding UTF8 ;
\c icndbind;
grant all privileges on database icndbind to dbuser1;
grant connect, temp, create on database icndbind to dbuser1;

-- connect to the respective database before executing the below commands
SET ROLE dbuser1;
ALTER DATABASE icndbind SET search_path TO dbuser1;
revoke connect on database icndbind from public;
