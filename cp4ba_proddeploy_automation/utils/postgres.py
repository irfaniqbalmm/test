import pexpect
import time
import re
from utils.db_util import *
from utils.utils_class import Utils

def drop_postgres_database(db_names, db_user, ssh_host, password, log, tablespace_dict):
    """
        Name: drop_postgres_database
        Author: Dhanesh
        Desc: To delete the dbs present in the postgres server as per the db names provided
        Parameters:
            ssh_host (string ): The ssh host name
            password (string ): The ssh host password to make the ssh connection
            db_file_names (dictionary ): The name of the databases to delete along with the file name to execute
            db_user (string ): The db2 user
            tablespace_dict (Dic): The optional tablespace option - Yes/No and tablespace values
        Returns:
            none
        Raises:
            Exception
    """

    process = connect_to_ssh(ssh_host, password, log)
    quit_command = "\q"
    log.logger.info(f'List of databases to drop: {db_names}')
    print(f'List of databases to drop: {db_names}')

    try:
        process.sendline('su - '+ db_user)
        process.expect('$', timeout=10)
        switch_user_output = process.before.decode('utf-8')
        log.logger.info('Switched to user: '+ db_user + switch_user_output)
        print('Switched to user: '+ db_user + switch_user_output)
        process.sendline('psql')
        process.expect('#', timeout=10)
        output = process.before.decode('utf-8')
        log.logger.info('Switched to psql terminal'+ output)
        print('Switched to psql terminal '+ output)
    
        for db_name in db_names:
            try:
                db_name = db_name.lower()
                row_pattern = re.compile(r'.*' + re.escape('1 row') + r'.*')
                process.sendline(f"SELECT datname FROM pg_database WHERE pg_database.datname = '{db_name}';")
                process.expect(row_pattern, timeout=5)
                dir_output = process.before.decode('utf-8')
                log.logger.debug(f'The database {db_name} is present in the directory {dir_output}')
                print(f'The database {db_name} is present in the directory {dir_output}')  
                time.sleep(2) 

                try:
                    drop_db_pattern = re.compile(r'.*' + re.escape('DROP DATABASE') + r'.*')
                    drop_db_command = 'drop database '+ db_name + ' with(force);'
                    log.logger.info('Dropping database '+ db_name)
                    log.logger.info(f'Dropping database {drop_db_command}')
                    print('Dropping database '+ db_name)
                    print(drop_db_command)
                    process.sendline(drop_db_command)
                    process.expect(drop_db_pattern, timeout=30)
                    drop_db_output = process.before.decode('utf-8')
                    log.logger.debug(f'Database {db_name} dropped successfully: '+ drop_db_output)
                    print(f'Database {db_name} dropped successfully: '+ drop_db_output)
                    time.sleep(2)
                    log.logger.debug(f'Calling the method drop_tablespace with database {db_name}')
                    drop_tablespace(process, db_name, log, tablespace_dict)
                    row_pattern = re.compile(r'.*' + re.escape('0 rows') + r'.*')
                    process.sendline(f"SELECT datname FROM pg_database WHERE pg_database.datname = '{db_name}';")
                    process.expect(row_pattern, timeout=5)
                    process.expect('#', timeout=5)
                    log.logger.debug(process.before.decode('utf-8'))
                    log.logger.info(f'The database {db_name} dropped successfully')
                    print(process.before.decode('utf-8'))
                    print(f'The database {db_name} dropped successfully')

                except pexpect.exceptions.TIMEOUT as e: 
                    drop_db_output = process.before.decode('utf-8')
                    log.logger.debug(f'DB drop output: {drop_db_output}'+ str(e))
                    print(f'DB drop output: {drop_db_output}')     
                    raise Exception(f'Error occured while dropping the database: {db_name}'+ str(e))
                except pexpect.exceptions.EOF as e:
                    log.logger.error(f'Unexpected EOF while dropping database {db_name}'+ str(e))
                    raise Exception(f'Unexpected EOF while dropping database {db_name}'+ str(e))
                
            except pexpect.exceptions.TIMEOUT as e:
                drop_db_output = process.before.decode('utf-8')
                log.logger.debug(f'The database {db_name} is not present in the directory {drop_db_output}'+ str(e))
                log.logger.info(f'Skipped dropping database {db_name}')
                print(f'The database {db_name} is not present in the directory {drop_db_output}')   
                print(f'Skipped dropping database {db_name}')
            except pexpect.exceptions.EOF as e:
                log.logger.error('Unexpected EOF.....'+ str(e))
                raise Exception('Unexpected EOF.....'+ str(e))      
        
        process.sendline(quit_command)
        process.expect('$', timeout=10)
        print('psql session closed')
        log.logger.info('psql session closed')

    except pexpect.exceptions.TIMEOUT as e:
        log.logger.error('Process timed out. Error while switching user ' +db_user)
        raise Exception('Process timed out. Error while switching user ' + db_user +"Error: " + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....')
        raise Exception('Unexpected EOF.....'+ str(e))
    finally:
        process.close() 
        log.logger.info('SSH session closed.')  

def create_postgres_database(db_file_names, ssh_host, password, db_user, log, tablespace_dict):
    """
        Name: create_postgres_database
        Author: Dhanesh
        Desc: To create the dbs in the postgres server as per the db names provided
        Parameters:
            ssh_host (string ): The ssh host name eg: db2bang1.fyre.ibm.com
            password (string ): The ssh host password to make the ssh connection
            db_file_names (dictionary ): The sql file names to create the databases
            db_user (string ): The pstgres user
            tablespace_dict (Dic): The optional tablespace option - Yes/No and tablespace values
        Returns:
            none
        Raises:
            Exception
    """
        
    process = connect_to_ssh(ssh_host, password, log)
    quit_command = "\q"
    insert_command = "\i "
    log.logger.info(f'Creating databases: {db_file_names}')
    print(f'Creating databases: {db_file_names}')

    try:
        process.sendline('su - '+ db_user)
        process.expect('$', timeout=10)
        switch_user_output = process.before.decode('utf-8')
        log.logger.info('Switched to user: '+ db_user + switch_user_output)
        print('Switched to user: '+ db_user + switch_user_output)
        
        for db_name, file_name in db_file_names.items():
            try:
                db_name = db_name.lower()
                process.sendline(f'mkdir /pgsqldata/{db_name}')
                process.expect('$', timeout=3)

                log.logger.info('Trying to create directory to store the data')
                if 'os1' in db_name and tablespace_dict['tablespace_option']:
                    for tbl_key, tbl_val in tablespace_dict.items():
                        if tbl_key == 'tablespace_option':
                            continue
                    log.logger.info(f'Creating directory /pgsqldata/{db_name}/{tbl_val}')
                    process.sendline(f'mkdir /pgsqldata/{db_name}/{tbl_val}')
                    process.expect('$', timeout=3)
                process.sendline('cd /pgsqldata/execute_postgres_scripts')
                process.expect('$', timeout=3)
                process.sendline('psql')
                process.expect('#', timeout=10)
                output = process.before.decode('utf-8')
                log.logger.info('Switched to psql terminal'+ output)
                print('Switched to psql terminal '+ output)
                create_db_pattern = re.compile(r'.*' + re.escape('You are now connected to database') + r'.*')
                create_db_command = insert_command + file_name
                log.logger.info('Executing create database script '+ file_name)
                print('Executing database script '+ file_name)
                print(create_db_command)
                process.sendline(create_db_command)
                process.expect(create_db_pattern, timeout=30)
                db_creation_output = process.before.decode('utf-8')
                log.logger.debug(f'Database creation: {db_creation_output}')
                print(f'Database creation: {db_creation_output}')
                process.expect('#', timeout=3)
                process.sendline(quit_command)
                process.expect('$', timeout=10)
                print('psql session closed')
                log.logger.info('psql session closed')
                process.sendline('psql')
                process.expect('#', timeout=10)
                output = process.before.decode('utf-8')
                log.logger.info('Switched to psql terminal'+ output)
                print('Switched to psql terminal '+ output)
                row_pattern = re.compile(r'.*' + re.escape('1 row') + r'.*')
                process.sendline(f"SELECT datname FROM pg_database WHERE pg_database.datname = '{db_name}';")
                process.expect(row_pattern, timeout=10)
                dir_output = process.before.decode('utf-8')
                log.logger.debug(f'The database {db_name} is present in the directory {dir_output}')
                log.logger.debug(f'The database {db_name} created successfully')
                print(f'The database {db_name} is present in the directory {dir_output}')  
                time.sleep(2) 
                process.sendline(quit_command)
                process.expect('$', timeout=10)
                print('psql session closed')
                log.logger.info('psql session closed')
                
            except pexpect.exceptions.TIMEOUT as e: 
                drop_db_output = process.before.decode('utf-8')
                log.logger.debug(f'DB creation output: {drop_db_output}'+ str(e))
                print(f'DB creation output: {drop_db_output}')     
                raise Exception('Error occured while creating the database: '+ file_name + str(e))
            except pexpect.exceptions.EOF as e:
                log.logger.error('Unexpected EOF.....'+ str(e))
                raise Exception('Unexpected EOF.....'+ str(e))     

    except pexpect.exceptions.TIMEOUT as e:
        log.logger.debug('Process timed out. Error while switching user ' +db_user + str(e))
        raise Exception('Process timed out. Error while switching user ' +db_user + str(e))
    except pexpect.exceptions.EOF:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))
    finally:
        process.close()      
        log.logger.info('SSH session closed.')  

def drop_tablespace(process, db_name, log, tablespace_dict):
    """
        Name: drop_tablespace
        Author: Dhanesh
        Desc: To drop the tablespaces before creating new databases and tablespaces
        Parameters:
            process (Process): The instance of the Process
            db_name (String): The name of the database
            log(Logger) : The instance of Logger to log
            tablespace_dict (Dic): The optional tablespace option - Yes/No and tablespace values
        Returns:
            none
        Raises:
            Exception
    """
    try:
        drop_tablespace_pattern = re.compile(r'.*' + re.escape('DROP TABLESPACE') + r'.*')
        tablespace_name = f'{db_name}_tbs'
        log.logger.info('Dropping tablespace '+ tablespace_name)
        print('Dropping tablespace '+ tablespace_name)
        drop_tablespace_command = f'drop tablespace {tablespace_name};'
        process.sendline(drop_tablespace_command)
        process.expect(drop_tablespace_pattern, timeout=30)
        drop_tablespace_output = process.before.decode('utf-8')
        log.logger.debug('Tablespace dropped successfully: '+ drop_tablespace_output)
        print('Tablespace dropped successfully: '+ drop_tablespace_output)
        print(f'Tablespace {tablespace_name} dropped successfully')
        if 'os1' in db_name and tablespace_dict['tablespace_option']:
            for tbl_key, tbl_val in tablespace_dict.items():
                if tbl_key == 'tablespace_option':
                    continue

                try:
                    log.logger.debug(f'Dropping the tablespace {tbl_val}')
                    process.sendline(f'drop tablespace {tbl_val};')
                    process.expect(drop_tablespace_pattern, timeout=30)
                    process.expect('#', timeout=10)
                    print(f'Tablespace {tbl_val} dropped successfully')
                    log.logger.debug(f'Tablespace {tbl_val} dropped successfully')
                except pexpect.exceptions.TIMEOUT as e:
                    drop_tablespace_pattern_error = re.compile(r'.*' + re.escape('ERROR:  tablespace') + r'.*')
                    process.expect(drop_tablespace_pattern_error, timeout=30)
                    drop_tablespace_output = process.before.decode('utf-8')
                    log.logger.debug(f'Drop_tablespace_output: {drop_tablespace_output}')
    except pexpect.exceptions.TIMEOUT as e: 
        drop_tablespace_output = process.before.decode('utf-8')
        log.logger.debug(f'Drop tablespace: {drop_tablespace_output}'+ str(e))
        print(f'Drop tablespace: {drop_tablespace_output}'+ str(e))     
        raise Exception('Error occured while dropping tablespaces')