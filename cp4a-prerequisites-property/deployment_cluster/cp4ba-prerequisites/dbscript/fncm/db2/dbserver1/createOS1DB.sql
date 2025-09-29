-- create OS1bancp23 object store database, you could update FILENAME as your requirement.
-- Please make sure you change the drive and path to your MSSQL database.
CREATE DATABASE OS1bancp23
ON PRIMARY
(  NAME = OS1bancp23_DATA,
   FILENAME = 'C:\MSSQL_DATABASE\OS1bancp23_DATA.mdf',
   SIZE = 400MB,
   FILEGROWTH = 128MB ),

FILEGROUP OS1bancp23SA_DATA_FG
(  NAME = OS1bancp23SA_DATA,
   FILENAME = 'C:\MSSQL_DATABASE\OS1bancp23SA_DATA.ndf',
   SIZE = 300MB,
   FILEGROWTH = 128MB),

FILEGROUP OS1bancp23SA_IDX_FG
(  NAME = OS1bancp23SA_IDX,
   FILENAME = 'C:\MSSQL_DATABASE\OS1bancp23SA_IDX.ndf',
   SIZE = 300MB,
   FILEGROWTH = 128MB)

LOG ON
(  NAME = 'OS1bancp23_LOG',
   FILENAME = 'C:\MSSQL_DATABASE\OS1bancp23_LOG.ldf',
   SIZE = 160MB,
   FILEGROWTH = 50MB )
GO

ALTER DATABASE OS1bancp23 SET RECOVERY SIMPLE
GO

ALTER DATABASE OS1bancp23 SET AUTO_CREATE_STATISTICS ON
GO

ALTER DATABASE OS1bancp23 SET AUTO_UPDATE_STATISTICS ON
GO

ALTER DATABASE OS1bancp23 SET READ_COMMITTED_SNAPSHOT ON
GO

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

-- Creating users and schemas for object store database
USE OS1bancp23
GO
CREATE USER cpeadmin FOR LOGIN cpeadmin WITH DEFAULT_SCHEMA=cpeadmin
GO
CREATE SCHEMA cpeadmin AUTHORIZATION cpeadmin
GO
EXEC sp_addrolemember 'db_ddladmin', cpeadmin;
EXEC sp_addrolemember 'db_datareader', cpeadmin;
EXEC sp_addrolemember 'db_datawriter', cpeadmin;
GO
