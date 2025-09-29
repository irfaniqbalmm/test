-- create ANSIOS1 object store database, you could update FILENAME as your requirement.
-- Please make sure you change the drive and path to your MSSQL database.
CREATE DATABASE ANSIOS1
ON PRIMARY
(  NAME = ANSIOS1_DATA,
   FILENAME = 'C:\MSSQL_DATABASE\ANSIOS1_DATA.mdf',
   SIZE = 400MB,
   FILEGROWTH = 128MB ),

FILEGROUP ANSIOS1SA_DATA_FG
(  NAME = ANSIOS1SA_DATA,
   FILENAME = 'C:\MSSQL_DATABASE\ANSIOS1SA_DATA.ndf',
   SIZE = 300MB,
   FILEGROWTH = 128MB),

FILEGROUP ANSIOS1SA_IDX_FG
(  NAME = ANSIOS1SA_IDX,
   FILENAME = 'C:\MSSQL_DATABASE\ANSIOS1SA_IDX.ndf',
   SIZE = 300MB,
   FILEGROWTH = 128MB)

LOG ON
(  NAME = 'ANSIOS1_LOG',
   FILENAME = 'C:\MSSQL_DATABASE\ANSIOS1_LOG.ldf',
   SIZE = 160MB,
   FILEGROWTH = 50MB )
GO

ALTER DATABASE ANSIOS1 SET RECOVERY SIMPLE
GO

ALTER DATABASE ANSIOS1 SET AUTO_CREATE_STATISTICS ON
GO

ALTER DATABASE ANSIOS1 SET AUTO_UPDATE_STATISTICS ON
GO

ALTER DATABASE ANSIOS1 SET READ_COMMITTED_SNAPSHOT ON
GO

-- create a SQL Server login account for the database user of each of the databases and update the master database to grant permission for XA transactions for the login account

-- Creating users and schemas for object store database
USE ANSIOS1
GO
CREATE USER fncmuser FOR LOGIN fncmuser WITH DEFAULT_SCHEMA=fncmuser
GO
CREATE SCHEMA fncmuser AUTHORIZATION fncmuser
GO
EXEC sp_addrolemember 'db_ddladmin', fncmuser;
EXEC sp_addrolemember 'db_datareader', fncmuser;
EXEC sp_addrolemember 'db_datawriter', fncmuser;
EXEC sp_addrolemember 'db_securityadmin', fncmuser;
EXEC sp_addsrvrolemember fncmuser, 'bulkadmin';

GO
