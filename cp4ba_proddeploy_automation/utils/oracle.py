import pexpect
import re
import os
import sys
current_dir = os.getcwd()
print(current_dir)
sys.path.insert(0, current_dir + '/utils')
from db_util import *

def drop_tablespace(process, tablespace_name, log):
    """
        Name: drop_tablespace
        Author: Dhanesh
        Desc: To drop the tablespace present in the server if present else skip
        Parameters:
            process (pexpect ): The instance of the pexpect process
            tablespace_name (string ): The tablespace name to delete
            log (logging ): The logging intance to log the outputs
        Returns:
            none
        Raises:
            Exception, ValueError
    """

    try:
        drop_tablespace_pattern = re.compile(r'.*' + re.escape('Tablespace dropped') + r'.*')

        #Check if the tablespace is present in the directory
        is_present = is_tablespace_present(process, tablespace_name, log)

        #Selete tablespace if present
        if is_present:
            log.logger.info(f'Dropping tablespace {tablespace_name}')
            print(f'Dropping tablespace {tablespace_name}')
            drop_temp_tablespace_query = f'DROP TABLESPACE {tablespace_name} INCLUDING CONTENTS AND DATAFILES;'
            log.logger.info(f' {drop_temp_tablespace_query}')
            process.sendline(drop_temp_tablespace_query)
            index = process.expect([drop_tablespace_pattern, pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            if index != 0:

                process.expect('SQL>', timeout=10)
                output = process.before.decode('utf-8')
                log.logger.info(f'Error dropping tablespace {tablespace_name} : {output}')
                raise ValueError(f'Error dropping tablespace {tablespace_name} : {output}')
            else:

                #Verifying tablespace deleted successfully
                is_present = is_tablespace_present(process, tablespace_name, log)
                if not is_present:

                    log.logger.info(f'The tablespace {tablespace_name} dropped successfully')
                    print(f'The tablespace {tablespace_name} dropped successfully')
                else:
                    log.logger.info(f'Error dropping tablespace {tablespace_name} : {output}')
                    raise ValueError(f'Error dropping tablespace {tablespace_name} : {output}')

        else:
            log.logger.info(f'Skipped dropping tablespace {tablespace_name}')
            print(f'Skipped dropping tablespace {tablespace_name}')

    except pexpect.exceptions.TIMEOUT as e: 
        drop_tablepsace_output = process.before.decode('utf-8')
        log.logger.debug(f'Drop tablespace output: {drop_tablepsace_output}'+ str(e))
        print(f'Drop tablespace output: {drop_tablepsace_output}')     
        raise Exception('Error occured while dropping the tablespace: '+ tablespace_name + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))  


def create_oracle_database(db_file_names, ssh_host, host_password, login_user, login_password, port, service_name, log):
    """
        Name: create_oracle_database
        Author: Dhanesh
        Desc: To create the dbs in the postgres server as per the db names provided
        Parameters:
            db_file_names (dictionary ): The user names along with the file names
            ssh_host (string ): The ssh host name
            host_password (string ): The ssh host password to make the ssh connection
            login_user (string ): The login user name
            login_password (string ): The login password
            port (string ): The connection port number
            service_name (string ): The service name to establish connection
            log (logging ): The logging intance to log the outputs
        Returns:
            none
        Raises:
            Exception
    """

    #connect to the ssh client to login to oracle server    
    process = connect_to_ssh(ssh_host, host_password, log)
    log.logger.info(f'Creating databases: {db_file_names}')
    print(f'Creating databases: {db_file_names}')
    process.sendline('cd /home')
    process.expect('#', timeout=10)

    #log in as oracle user to execute sql queries
    login_to_oracle(process, ssh_host, login_user, login_password, port, service_name, log)

    #Loop to get the username and file to create the databases
    try:
        for user_name, file in db_file_names.items():

            #Create new database
            create_db_command = f'@{file}'
            log.logger.info('Executing database script '+ create_db_command)
            print('Executing database script '+ file)
            process.sendline(create_db_command)
            pattern = re.compile(r'.*' + re.escape('Version') + r'.*')
            process.expect(pattern, timeout=10)
            db_creation_output = process.before.decode('utf-8')
            process.expect('#', timeout=10)

            #Verify the output is correct
            if 'Tablespace created' in db_creation_output and 'User created' in db_creation_output and 'Grant succeeded' in db_creation_output and 'ERROR' not in db_creation_output:
                log.logger.info(f'Database creation command executed successfully')
                log.logger.debug(f'Database creation: {db_creation_output}')
                print(f'Database creation: {db_creation_output}')
                if user_name.startswith('ICN'):
                    tablespace_name = f'{user_name}TS'
                    temp_tablespace_name = f'{user_name}TSTEMP'
                else:
                    tablespace_name = f'{user_name}DATATS'
                    temp_tablespace_name = f'{user_name}DATATSTEMP'
                
                #log in as oracle user
                login_to_oracle(process, ssh_host, login_user, login_password, port, service_name, log)
                
                #Verify that the temp tablespace is created
                is_tempts_present = is_tablespace_present(process, temp_tablespace_name, log)
                if not is_tempts_present:
                    log.logger.info(f'The temp tablespace {temp_tablespace_name} is not created properly')
                    raise ValueError(f'The temp tablespace {temp_tablespace_name} is not created properly')
                else:
                    log.logger.info(f'The temp tablespace {temp_tablespace_name} created properly')
                    print(f'The temp tablespace {temp_tablespace_name} created properly')
                
                #Verify that the tablespace is created
                is_ts_present = is_tablespace_present(process, tablespace_name, log)
                if not is_ts_present:
                    log.logger.info(f'The tablespace {tablespace_name} is not created properly')
                    raise ValueError(f'The tablespace {tablespace_name} is not created properly')
                else:
                    log.logger.info(f'The temp tablespace {tablespace_name} created properly')
                    print(f'The temp tablespace {tablespace_name} created properly')
                
                #Verify that the user is created
                is_usr_present = is_user_present(process, user_name, log)
                if not is_usr_present:
                    log.logger.info(f'The user {user_name} is not created properly')
                    raise ValueError(f'The user {user_name} is not created properly')
                else:
                    log.logger.info(f'The user tablespace {user_name} created properly')
                    print(f'The user {user_name} created properly')
            else:
                log.logger.info(f'Database creation is not successful: {user_name} {file}')
                log.logger.debug(f'Database creation: {db_creation_output}')
                print(f'Database creation: {db_creation_output}')
                raise ValueError(f'Database creation is not successful: {user_name} {file}')
            
    except pexpect.exceptions.TIMEOUT as e: 
            drop_db_output = process.before.decode('utf-8')
            log.logger.debug(f'DB creation output: {drop_db_output}'+ str(e))
            print(f'DB creation output: {drop_db_output}')     
            raise Exception('Error occured while creating the database: '+ file + str(e))
    except pexpect.exceptions.EOF as e:
            log.logger.error('Unexpected EOF.....'+ str(e))
            raise Exception('Unexpected EOF.....'+ str(e))   
    finally:
            process.close()      
            log.logger.info('SSH session closed.') 


def drop_oracle_database(user_names, ssh_host, host_password, login_user, login_password, port, service_name, log, tablespace_dict):
    """
        Name: drop_oracle_database
        Author: Dhanesh
        Desc: To drop the dbs in the oracle server as per the user names provided
        Parameters:
            user_names (list ): The list of user names
            ssh_host (string ): The ssh host name
            host_password (string ): The ssh host password to make the ssh connection
            login_user (string ): The login user name
            login_password (string ): The login password
            port (string ): The connection port number
            service_name (string ): The service name to establish connection
            log (logging ): The logging intance to log the outputs
            oracle_tab_index_loc (String): The index location tablespace name
            oracle_tab_table_loc (String): The table location tablespace name
            oracle_tab_lob_loc (String): The lob location tablespace name
        Returns:
            none
        Raises:
            Exception
    """

    #connect to the ssh client to login to oracle server
    process = connect_to_ssh(ssh_host, host_password, log)
    log.logger.info(f'Dropping usernames: {user_names}')
    print(f'Dropping databases: {user_names}')
    process.sendline('cd /home')
    process.expect('#', timeout=10)

    #log into the oracle to execute sql queries
    login_to_oracle(process, ssh_host, login_user, login_password, port, service_name, log)

    try:
        #Loop to get all the user names to drop the user and tablespaces
        for user_name in user_names:
            #Set the tablespace names accordingly
            if user_name.startswith('ICN'):
                tablespace_name = f'{user_name}TS'
                temp_tablespace_name = f'{user_name}TSTEMP'
            else:
                tablespace_name = f'{user_name}DATATS'
                temp_tablespace_name = f'{user_name}DATATSTEMP'

            
            log.logger.info(f'Deleting tablespace_name {tablespace_name}')
            log.logger.info(f'Deleting temp_tablespace_name : {temp_tablespace_name}')
            #Dropping temp tablespace if present
            drop_tablespace(process, temp_tablespace_name, log)

            #Dropping tablespace if present
            drop_tablespace(process, tablespace_name, log)

            #Dropping the user if present
            drop_user(process, user_name, log)

        log.logger.info(f'tablespace_dict =  {tablespace_dict}')
        for tbl_key, tbl_val in tablespace_dict.items():
            try:
                #Dropping tablespace index,loc if present
                log.logger.info(f'Iterating throguh the table space to delete the items...')
                if tbl_key == 'tablespace_option':
                    continue
                log.logger.info(f'Dropping the tablespace with name {tbl_val}')
                drop_tablespace(process, tbl_val, log)

            except Exception as e:
                log.logger.info(f'Dropping the tablespace with name {tbl_val} failed')

    except pexpect.exceptions.TIMEOUT as e: 
        drop_db_output = process.before.decode('utf-8')
        log.logger.debug(f'DB drop output: {drop_db_output}'+ str(e))
        print(f'DB drop output: {drop_db_output}')     
        raise Exception('Error occured while dropping the database: '+ user_name + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))   
    finally:
        #Close the process to exist from the ssh
        process.close()      
        log.logger.info('SSH session closed.')


def login_to_oracle(process, ssh_host, login_user, login_password, port, service_name, log):
    """
        Name: login_to_oracle
        Author: Dhanesh
        Desc: To log into the orcale server
        Parameters:
            process (pexpect ): The instance of the pexpect process
            login_user (string ): The login user name
            login_password (string ): The login password
            port (string ): The connection port number
            service_name (string ): The service name to establish connection
            log (logging ): The logging intance to log the outputs
        Returns:
            none
        Raises:
            Exception
    """
     
    try:
        log = logger if hasattr(logger, "logger") else type("Wrapper", (), {"logger": logger})()
        #construct the command and execute it to login to the oracle
        login = f'sqlplus \'{login_user}/{login_password}@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCPS)(HOST={ssh_host}) (PORT={port}))(CONNECT_DATA=(SERVICE_NAME={service_name})))\' as sysdba'
        process.sendline(login)
        pattern = re.compile(r'.*' + re.escape('Connected to') + r'.*')
        index = process.expect([pattern, pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        process.expect('SQL>', timeout=10)
        output = process.before.decode('utf-8')
        if index == 0:
            log.logger.info(f'successfully logged in as oracle user: {login}')
            log.logger.debug(output)
            print(f'successfully logged in as oracle user: {output}')
        else:
            log.logger.info(f'Login as oracle user was unsuccessful: {output}')
            raise ValueError(f'Login as oracle user was unsuccessful: {output}')

    except pexpect.exceptions.TIMEOUT as e: 
        output = process.before.decode('utf-8')
        log.logger.debug(f'Login to oracle: {output}'+ str(e))
        print(f'Login to oracle: {output}') 
        raise Exception('Error occured while login to oracle: ' + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))   
    

def drop_user(process, user_name, log):
    """
        Name: drop_user
        Author: Dhanesh
        Desc: To drop the user present in the server if present else skip
        Parameters:
            process (pexpect ): The instance of the pexpect process
            user_name (string ): The username name to delete
            log (logging ): The logging intance to log the outputs
        Returns:
            none
        Raises:
            Exception, ValueError
    """
        
    try:
        drop_user_pattern = re.compile(r'.*' + re.escape('User dropped') + r'.*')

        #Check if the user is present in the directory
        is_present = is_user_present(process, user_name, log)

        #Deleting user if present
        if is_present:
            log.logger.info(f'Dropping user {user_name}')
            print(f'Dropping user {user_name}')
            drop_user_query = f'DROP USER {user_name} CASCADE;'
            process.sendline(drop_user_query)
            index = process.expect([drop_user_pattern, pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            if index != 0:

                process.expect('SQL>', timeout=10)
                output = process.before.decode('utf-8')
                log.logger.info(f'Error dropping user {user_name} : {output}')
                raise ValueError(f'Error dropping user {user_name} : {output}')
            else:

                #Verifying user deleted successfully
                is_present = is_user_present(process, user_name, log)
                if not is_present:
                    log.logger.info(f'The user {user_name} dropped successfully')
                    print(f'The user {user_name} dropped successfully')
                else:
                    log.logger.info(f'Error dropping user {user_name} : {output}')
                    raise ValueError(f'Error dropping user {user_name} : {output}')

        else:
            log.logger.info(f'The user {user_name} is not present.')
            log.logger.info(f'Skipped dropping user {user_name}')
            print(f'The user {user_name} is not present.')
            print(f'Skipped dropping user {user_name}')

    except pexpect.exceptions.TIMEOUT as e: 
        drop_user_output = process.before.decode('utf-8')
        log.logger.debug(f'Drop user output: {drop_user_output}'+ str(e))
        print(f'Drop user output: {drop_user_output}')     
        raise Exception('Error occured while dropping the user: '+ user_name + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))  


def is_tablespace_present(process, tablespace_name, log):
    """
        Name: is_tablespace_present
        Author: Dhanesh
        Desc: To drop the tablespace present in the server if present else skip
        Parameters:
            process (pexpect ): The instance of the pexpect process
            tablespace_name (string ): The tablespace name to find
            log (logging ): The logging intance to log the outputs
        Returns:
            True or False
        Raises:
            TIMEOUT, EOF
    """
    try:
        user_present = False
        list_tablespace_query = 'SELECT TABLESPACE_NAME FROM USER_TABLESPACES;'

        #Check if the tablespace is present in the directory
        pattern = re.compile(r'.*' + re.escape(tablespace_name) + r'.*')
        process.sendline(list_tablespace_query)
        index = process.expect([pattern, pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        process.expect('SQL>', timeout=10)
        if index == 0:
            log.logger.info(f'The tablespace {tablespace_name} is present.')
            print(f'The tablespace {tablespace_name} is present.')
            user_present = True
        else:
            log.logger.info(f'The tablespace {tablespace_name} is not present.')
            print(f'The tablespace {tablespace_name} is not present.')
        
        #Listing all the users
        process.sendline(list_tablespace_query)
        process.expect('SQL>', timeout=10)
        output = process.before.decode('utf-8')
        log.logger.info('All users present:')
        log.logger.info(output)
        print('All tablepaces present:')
        print(output)

        return user_present

    except pexpect.exceptions.TIMEOUT as e: 
        output = process.before.decode('utf-8')
        log.logger.debug(f'List tablespace output: {output}'+ str(e))
        print(f'List tablespace output: {output}'+ str(e))  
        raise Exception('Error occured while listing the tablespace: '+ tablespace_name + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))  


def is_user_present(process, user_name, log):
    """
        Name: drop_user
        Author: Dhanesh
        Desc: To drop the user present in the server if present else skip
        Parameters:
            process (pexpect ): The instance of the pexpect process
            user_name (string ): The user name to find
            log (logging ): The logging intance to log the outputs
        Returns:
            True or False
        Raises:
            TIMEOUT, EOF
    """
    try:
        user_present = False
        list_users_query = 'SELECT USERNAME FROM DBA_USERS;'

        #Check if the user is present in the directory
        pattern = re.compile(r'.*' + re.escape(user_name) + r'.*')
        process.sendline(list_users_query)
        index = process.expect([pattern, pexpect.EOF, pexpect.TIMEOUT], timeout=10)
        process.expect('SQL>', timeout=10)
        if index == 0:
            log.logger.info(f'The user {user_name} is present.')
            print(f'The user {user_name} is present.')
            user_present = True
        else:
            log.logger.info(f'The user {user_name} is not present.')
            print(f'The user {user_name} is not present.')
        
        #Listing all the users
        process.sendline(list_users_query)
        process.expect('SQL>', timeout=10)
        output = process.before.decode('utf-8')
        log.logger.info('All users present:')
        log.logger.info(output)
        print('All users present:')
        print(output)

        return user_present
        
    except pexpect.exceptions.TIMEOUT as e: 
        output = process.before.decode('utf-8')
        log.logger.debug(f'List users output: {output}'+ str(e))
        print(f'List users output: {output}'+ str(e))  
        raise Exception('Error occured while listing the users: '+ user_name + str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))  

