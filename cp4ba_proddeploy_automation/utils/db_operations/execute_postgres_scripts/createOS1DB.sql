-- create user dbuser1
CREATE ROLE dbuser1 WITH INHERIT LOGIN ENCRYPTED PASSWORD 'Password@1';

-- please modify location follow your requirement
create tablespace os1dbind_tbs owner dbuser1 location '/pgsqldata/os1dbind';
grant create on tablespace os1dbind_tbs to dbuser1;

-- create database os1dbind
create database os1dbind owner dbuser1 tablespace os1dbind_tbs template template0 encoding UTF8 ;
\c os1dbind;
grant all privileges on database os1dbind to dbuser1;
grant connect, temp, create on database os1dbind to dbuser1;

-- connect to the respective database before executing the below commands
SET ROLE dbuser1;
ALTER DATABASE os1dbind SET search_path TO dbuser1;
revoke connect on database os1dbind from public;
