-- create IBM CONTENT NAVIGATOR database
CREATE DATABASE ICNbancp23;
ALTER DATABASE ICNbancp23 SET READ_COMMITTED_SNAPSHOT ON;

-- create a SQL Server login account for the database user of each of the databases and update the master database to grant permission for XA transactions for the login account
USE MASTER
GO
-- when using SQL authentication
CREATE LOGIN cpeadmin WITH PASSWORD='Password1'
-- when using Windows authentication:
-- CREATE LOGIN [domain\user] FROM WINDOWS
GO
CREATE USER cpeadmin FOR LOGIN cpeadmin WITH DEFAULT_SCHEMA=cpeadmin
GO
EXEC sp_addrolemember N'SqlJDBCXAUser', N'cpeadmin';
GO

-- Creating users and schemas for IBM CONTENT NAVIGATOR database
USE ICNbancp23
GO
CREATE USER cpeadmin FOR LOGIN cpeadmin WITH DEFAULT_SCHEMA=cpeadmin
GO
CREATE SCHEMA cpeadmin AUTHORIZATION cpeadmin
GO
EXEC sp_addrolemember 'db_ddladmin', cpeadmin;
EXEC sp_addrolemember 'db_datareader', cpeadmin;
EXEC sp_addrolemember 'db_datawriter', cpeadmin;
GO
