-- create IBM CONTENT NAVIGATOR database
CREATE DATABASE ANSIICN;
ALTER DATABASE ANSIICN SET READ_COMMITTED_SNAPSHOT ON;

-- create a SQL Server login account for the database user of each of the databases and update the master database to grant permission for XA transactions for the login account
USE MASTER
GO

-- Creating users and schemas for IBM CONTENT NAVIGATOR database
USE ANSIICN
GO
CREATE USER fncmuser FOR LOGIN fncmuser WITH DEFAULT_SCHEMA=fncmuser
GO
CREATE SCHEMA fncmuser AUTHORIZATION fncmuser
GO
EXEC sp_addrolemember 'db_ddladmin', fncmuser;
EXEC sp_addrolemember 'db_datareader', fncmuser;
EXEC sp_addrolemember 'db_datawriter', fncmuser;
GO
