-- create user {dbuser}
CREATE ROLE {dbuser} WITH INHERIT LOGIN ENCRYPTED PASSWORD '{dbuserpwd}';

-- please modify location follow your requirement
create tablespace {tablespace} owner {dbuser} location '/pgsqldata/{dbname}';
grant create on tablespace {tablespace} to {dbuser};

-- create database {dbname}
create database {dbname} owner {dbuser} tablespace {tablespace} template template0 encoding UTF8 ;
-- Connect to your database and create schema
\c {dbname};
CREATE SCHEMA IF NOT EXISTS {dbschema} AUTHORIZATION {dbuser};
GRANT ALL ON schema {dbschema} to {dbuser};

-- create a schema for {dbname} and set the default
-- connect to the respective database before executing the below commands
SET ROLE {dbuser};
ALTER DATABASE {dbname} SET search_path TO {dbschema};
revoke connect on database {dbname} from public;