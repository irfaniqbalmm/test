-- create user fncmuser
CREATE ROLE fncmuser WITH INHERIT LOGIN ENCRYPTED PASSWORD 'WFQA20zz';

-- create database ANSIOS1
create database ANSIOS1 owner fncmuser template template0 encoding UTF8 ;
revoke connect on database ANSIOS1 from public;
grant all privileges on database ANSIOS1 to fncmuser;
grant connect, temp, create on database ANSIOS1 to fncmuser;
