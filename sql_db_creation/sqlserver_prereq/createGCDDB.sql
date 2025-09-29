-- create Content Platform Engine GCD database, you could update FILENAME as your requirement.
-- Please make sure you change the drive and path to your MSSQL database.
CREATE DATABASE ANSIGCD
ON PRIMARY
(  NAME = ANSIGCD_DATA,
   FILENAME = 'C:\MSSQL_DATABASE\ANSIGCD_DATA.mdf',
   SIZE = 400MB,
   FILEGROWTH = 128MB ),

FILEGROUP ANSIGCDSA_DATA_FG
(  NAME = ANSIGCDSA_DATA,
   FILENAME = 'C:\MSSQL_DATABASE\ANSIGCDSA_DATA.ndf',
   SIZE = 300MB,
   FILEGROWTH = 128MB),

FILEGROUP ANSIGCDSA_IDX_FG
(  NAME = ANSIGCDSA_IDX,
   FILENAME = 'C:\MSSQL_DATABASE\ANSIGCDSA_IDX.ndf',
   SIZE = 300MB,
   FILEGROWTH = 128MB)

LOG ON
(  NAME = 'ANSIGCD_LOG',
   FILENAME = 'C:\MSSQL_DATABASE\ANSIGCD_LOG.ldf',
   SIZE = 160MB,
   FILEGROWTH = 50MB )
GO

ALTER DATABASE ANSIGCD SET RECOVERY SIMPLE
GO

ALTER DATABASE ANSIGCD SET AUTO_CREATE_STATISTICS ON
GO

ALTER DATABASE ANSIGCD SET AUTO_UPDATE_STATISTICS ON
GO

ALTER DATABASE ANSIGCD SET READ_COMMITTED_SNAPSHOT ON
GO

-- create a SQL Server login account for the database user of each of the databases and update the master database to grant permission for XA transactions for the login account

-- Creating users and schemas for Content Platform Engine GCD database
USE ANSIGCD
GO
CREATE USER fncmuser FOR LOGIN fncmuser WITH DEFAULT_SCHEMA=fncmuser
GO
CREATE SCHEMA fncmuser AUTHORIZATION fncmuser
GO
EXEC sp_addrolemember 'db_ddladmin', fncmuser;
EXEC sp_addrolemember 'db_datareader', fncmuser;
EXEC sp_addrolemember 'db_datawriter', fncmuser;

GO
