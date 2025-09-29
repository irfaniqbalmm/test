-- create user fncmuser
CREATE ROLE fncmuser WITH INHERIT LOGIN ENCRYPTED PASSWORD 'WFQA20zz';

-- create database ANSIICN
create database ANSIICN owner fncmuser template template0 encoding UTF8 ;
revoke connect on database ANSIICN from public;
grant all privileges on database ANSIICN to fncmuser;
grant connect, temp, create on database ANSIICN to fncmuser;
