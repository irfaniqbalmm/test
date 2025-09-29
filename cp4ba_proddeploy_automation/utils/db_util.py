import pexpect
import shutil
import re
import os
import logging

logger = logging.getLogger(__name__)

def copy_files_to_ssh(ssh_host, src_path, dest_path, password, log):
        
    """
        Name: copy_files_to_ssh
        Author: Dhanesh
        Desc: copy the bashfiles to the db server to execute
        Parameters:
            ssh_host (string ): The ssh host name eg: db2bang1.fyre.ibm.com
            src_path (string ): The source path of the directory which has the bash files
            dest_path (string ): The destination path in the server
            password (string ): The ssh host password to make the ssh connection
        Returns:
            none
        Raises:
            Exception
    """

    try:
        log = logger if hasattr(logger, "logger") else type("Wrapper", (), {"logger": logger})()
        log.logger.info(f'Copying files to the server {ssh_host} ....')
        scp_command = 'scp -rp '+ src_path +' root@'+ssh_host+':'+dest_path
        print(scp_command)
        scp_process = pexpect.spawn(scp_command)
        try:
            pattern = re.compile(r'.*' + re.escape('Are you sure you want to continue connecting') + r'.*')
            scp_process.expect(pattern, timeout = 3)
            output = (scp_process.before + scp_process.after).decode('utf-8')
            log.logger.info('The authenticity of host cant be established: '+ output)
            scp_process.sendline('yes')
            scp_process.expect('#', timeout=10) 
            log.logger.info('The authenticity of host is now established')
        except pexpect.exceptions.TIMEOUT as e:
            log.logger.info('The authenticity of host already established')

        scp_process.expect('password:', timeout=120) 
        scp_process.sendline(password)
        scp_process.expect(pexpect.EOF)
        output = scp_process.before.decode('utf-8')
        log.logger.info(f'Files are copied to {dest_path}')
        log.logger.debug(output)
        print(output)

    except pexpect.exceptions.TIMEOUT as e:
        log.logger.info(f'Failed to copy the files to the server {ssh_host}')
        log.logger.debug('Operation timed out.'+ str(e))
        raise Exception('Operation timed out.'+ str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF. Check the SCP command and connection.'+ str(e))
        raise Exception('Unexpected EOF. Check the SCP command and connection.'+ str(e))
    finally:
        scp_process.close() 
        log.logger.info('SSH session closed.')   

def connect_to_ssh(ssh_host, password, log):

    """
        Name: connect_to_ssh
        Author: Dhanesh
        Desc: connect to the ssh server using pexpect
        Parameters:
            ssh_host (string ): The ssh host name eg: db2bang1.fyre.ibm.com
            password (string ): The ssh host password to make the ssh connection
        Returns:
            process
        Raises:
            Exception
    """

    try:
        log = logger if hasattr(logger, "logger") else type("Wrapper", (), {"logger": logger})()
        log.logger.info(f'Connecting to the ssh server {ssh_host} ....')
        process = pexpect.spawn('/usr/bin/ssh root@' + ssh_host)
        index = process.expect(['password:', pexpect.EOF, pexpect.TIMEOUT], timeout=120) 

        if index == 0:
            log.logger.info('Sending password...')
            print('Sending password...')
            process.sendline(password)
            process.expect('#', timeout=120) 
            log.logger.info('SSH connection successful.')
            print('SSH connection successful.')
            output = (process.before + process.after).decode('utf-8')
            log.logger.debug(f'SSH connection to the server: {output}')
            print(f'SSH connection to the server: {output}')
            return process
        
        elif index == 1:
            log.logger.debug('Connection to SSH closed unexpectedly.')
            raise Exception('Connection closed unexpectedly.')
        
        elif index == 2:
            log.logger.debug('Connection to SSH timed out.')
            raise Exception('Connection timed out.')

    except pexpect.exceptions.TIMEOUT as e:
        log.logger.debug(f'Operation timed out. Failed to connect to SSH server {ssh_host} '+ str(e))
        raise Exception('Operation timed out.'+ str(e))
    except pexpect.exceptions.EOF as e:
        raise Exception('Unexpected EOF.....'+ str(e))

def grant_file_permission(directory_path, ssh_host, password, log):

    """
        Name: grant_file_permission
        Author: Dhanesh
        Desc: To grant executable permissions to the files in the server
        Parameters:
            ssh_host (string ): The ssh host name eg: db2bang1.fyre.ibm.com
            password (string ): The ssh host password to make the ssh connection
            directory_path (string ): The path to the directory to which the files are copied.
        Returns:
            process
        Raises:
            Exception
    """

    command = 'chmod +x '+ directory_path
    print('chmod command to execute '+command)
    process = connect_to_ssh(ssh_host, password, log)

    try:
        log = logger if hasattr(logger, "logger") else type("Wrapper", (), {"logger": logger})()    
        log.logger.info(f'Making directory {directory_path} executable...')
        process.sendline(command)
        process.expect('#', timeout=30)
        output = (process.before + process.after).decode('utf-8')
        print('File permission: '+output)

        if 'chmod' in output:
            log.logger.info(f'Executable permission granted successfully. {output}')
            print('Executable permission granted successfully')
        else:
            log.logger.info('Error in granting permission: '+ output)
            raise Exception('Error in granting permission: '+ output)
        return process

    except pexpect.exceptions.TIMEOUT as e:
        log.logger.debug('Granting permission timed out.'+ str(e))
        raise Exception('Granting permission timed out.'+ str(e))
    except pexpect.exceptions.EOF as e:
        log.logger.error('Unexpected EOF.....'+ str(e))
        raise Exception('Unexpected EOF.....'+ str(e))


def get_db_script_file(src_files, dest_dir, log):
    
    for file in src_files:
        try:
            shutil.copy(file, dest_dir)
            log.logger.info(f"File '{file}' copied to '{dest_dir}'")
            print(f"File '{file}' copied to '{dest_dir}'")

        except FileNotFoundError as e:
            log.logger.debug(f"Error: Source file '{file}' not found ({e})")
            raise Exception(f"Error: Source file '{file}' not found ({e})")
        except NotADirectoryError as e:
            log.logger.debug(f"Error: Destination '{dest_dir}' is not a directory ({e})")
            raise Exception(f"Error: Destination '{dest_dir}' is not a directory ({e})")
        except IOError as e:
            log.logger.error(f"Error copying file: {e}")
            raise Exception(f"Error copying file: {e}")
        except Exception as e:
            log.logger.error(f"Unexpected error: {e}")
            raise Exception(f"Unexpected error: {e}")

def get_dbscripts(dbscript_dir_path, destination_dir_path, log):
    """
        Name: get_db_script_file
        Author: Dhanesh
        Desc: To get the database script files from the path provided
        Parameters:
            dbscript_dir_path (string ): The path to the dbscripts folder
        Returns:
            process
        Raises:
            Exception
    """
    # Check if the source directory exists
    if not os.path.exists(dbscript_dir_path):
        ValueError(f"Source directory {dbscript_dir_path} does not exist.")
    
    # Walk through the source directory
    for root, dir, files in os.walk(dbscript_dir_path):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(destination_dir_path, file)

            # Copy file to the destination directory
            shutil.copy2(src_file, dest_file)
            print(f"Copied {src_file} to {dest_file}")
            log.logger.debug(f"Copied {src_file} to {dest_file}")
