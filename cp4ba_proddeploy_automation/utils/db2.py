import pexpect
from utils.db_util import *
from utils.utils_class import Utils
import time
import re

def drop_db2_database(force_drop_db_script, db_names, db_user, directory_path, ssh_host, password, log):

    """
        Name: drop_db2_database
        Author: Dhanesh
        Desc: To delete the dbs present in the db2 server as per the db names provided
        Parameters:
            ssh_host (string ): The ssh host name eg: db2bang1.fyre.ibm.com
            password (string ): The ssh host password to make the ssh connection
            directory_path (string ): The path to the directory with the bash script files to execute.
            db_names (list ): The name of the databases to delete from the db2 server
            force_drop_db_script (string ): The script file name with complete path
            db_user (string ): The db2 user
        Returns:
            none
        Raises:
            Exception
    """

    process = grant_file_permission(directory_path, ssh_host, password, log)
    log.logger.info(f'List of databases to drop: {db_names}')
    print(f'List of databases to drop: {db_names}')

    try:
        process.sendline('su '+ db_user)
        process.expect('$', timeout=120)
        switch_user_output = process.before.decode('utf-8')
        log.logger.info('Switched to user: '+ db_user + switch_user_output)
        print('Switched to user: '+ db_user + switch_user_output)
    
        for db_name in db_names:
            try:
                process.sendline("db2 list db directory | grep alias | cut -d '=' -f2 | cut -d ' ' -f2")
                pattern = re.compile(r'.*' + re.escape(db_name) + r'.*')
                process.expect(pattern, timeout=10)
                drop_db_output = process.before.decode('utf-8')
                print(f'list dbs: {drop_db_output}')
                log.logger.debug(f'The database {db_name} is present in the directory')
                print(f'The database {db_name} is present in the directory')   

                try:
                    drop_db_command = force_drop_db_script + ' ' + db_name
                    log.logger.info('Dropping database '+ db_name)
                    print('Dropping database '+ db_name)
                    print(drop_db_command)
                    process.sendline(drop_db_command)
                    pattern = re.compile(r'.*' + re.escape('The DROP DATABASE command completed successfully') + r'.*')
                    process.expect(pattern, timeout=60)
                    drop_db_output = process.before.decode('utf-8')
                    log.logger.debug('DB drop output: '+ drop_db_output)
                    print('DB drop output: '+ drop_db_output)
                    time.sleep(2)
                    process.sendline("db2 list db directory | grep alias | cut -d '=' -f2 | cut -d ' ' -f2")
                    process.expect(r'^(?!(?=.*%s)).*$' % db_name, timeout=10)
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
                log.logger.info(f'The database {db_name} is not present in the directory')
                log.logger.info(f'Skipped dropping database {db_name}')
                print(f'The database {db_name} is not present in the directory {drop_db_output}')   
                print(f'Skipped dropping database {db_name}')
            except pexpect.exceptions.EOF as e:
                log.logger.error('Unexpected EOF.....'+ str(e))
                raise Exception('Unexpected EOF.....'+ str(e))      
        
    except pexpect.exceptions.TIMEOUT:
        log.logger.error('Process timed out. Error while switching user ' +db_user)
        raise Exception('Process timed out. Error while switching user ' +db_user)
    except pexpect.exceptions.EOF:
        log.logger.error('Unexpected EOF.....')
        raise Exception('Unexpected EOF.....')
    finally:
        process.close() 
        log.logger.info('SSH session closed.')      

def create_db2_database(create_db_script, db_file_names, ssh_host, password, db_user, log):

    """
        Name: create_db2_database
        Author: Dhanesh
        Desc: To create the dbs in the db2 server as per the db names provided
        Parameters:
            ssh_host (string ): The ssh host name eg: db2bang1.fyre.ibm.com
            password (string ): The ssh host password to make the ssh connection
            db_names (list ): The name of the databases to delete from the db2 server
            create_db_script (string ): The script file name with complete path
            db_file_names (dictionary ): The sql file names to create the databases
            db_user (string ): The db2 user
        Returns:
            none
        Raises:
            Exception
    """
        
    process = connect_to_ssh(ssh_host, password, log)
    log.logger.info(f'Creating databases: {db_file_names}')
    print(f'Creating databases: {db_file_names}')

    try:
        process.sendline('cd /home')
        process.expect('$', timeout=3)
        process.sendline('su '+ db_user)
        process.expect('$', timeout=120)
        switch_user_output = process.before.decode('utf-8')
        log.logger.info('Switched to user: '+ db_user + switch_user_output)
        print('Switched to user: '+ db_user + switch_user_output)
        
        for db_name, file_name in db_file_names.items():
            try:
                create_db_command = create_db_script + ' ' + file_name
                log.logger.info('Executing database script '+ file_name)
                print('Executing database script '+ file_name)
                print(create_db_command)
                process.sendline(create_db_command)
                pattern = re.compile(r'.*' + re.escape('Database creation completed') + r'.*')
                process.expect(pattern, timeout=300)
                db_creation_output = process.before.decode('utf-8')
                log.logger.debug(f'Database creation: {db_creation_output}')
                print(f'Database creation: {db_creation_output}')
                process.expect('$', timeout=300)
                process.sendline("db2 list db directory | grep alias | cut -d '=' -f2 | cut -d ' ' -f2")
                pattern = re.compile(r'.*' + re.escape(db_name) + r'.*')
                process.expect(pattern, timeout=10)
                output = process.before.decode('utf-8')
                print(f'List directories: {output}')
                log.logger.info(f'List directories: {output}')
                process.expect('$', timeout=30)

                
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


