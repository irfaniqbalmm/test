-- create user fncmuser
CREATE ROLE fncmuser WITH INHERIT LOGIN ENCRYPTED PASSWORD 'WFQA20zz';

-- create database GCDDB
create database ANSIGCD owner fncmuser template template0 encoding UTF8 ;
revoke connect on database ANSIGCD from public;
grant all privileges on database ANSIGCD to fncmuser;
grant connect, temp, create on database ANSIGCD to fncmuser;
