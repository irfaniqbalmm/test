-- create user dbuser1
CREATE ROLE dbuser1 WITH INHERIT LOGIN ENCRYPTED PASSWORD 'Password@1';

-- please modify location follow your requirement
create tablespace gcddbind_tbs owner dbuser1 location '/pgsqldata/gcddbind';
grant create on tablespace gcddbind_tbs to dbuser1;  

-- create database gcddbind
create database gcddbind owner dbuser1 tablespace gcddbind_tbs template template0 encoding UTF8 ;
\c gcddbind;
grant all privileges on database gcddbind to dbuser1;
grant connect, temp, create on database gcddbind to dbuser1;

-- connect to the respective database before executing the below commands
SET ROLE dbuser1;
ALTER DATABASE gcddbind SET search_path TO dbuser1;
revoke connect on database gcddbind from public;
