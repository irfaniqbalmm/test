import pyodbc
import pandas as pd
import textwrap
import subprocess

def create_mssql_db(db_file_names, server, port, uid, password, log):
    """
        Name: create_mssql_db
        Author: Dhanesh
        Desc: To create the dbs in the mssql server as per the db names provided
        Parameters:
            server (string ): The mssql server name
            uid (string ): The user name
            password (string ): The user password
            db_file_names (dictionary ): The sql file names to create the databases
            port (int ): The connection port number
            log (logging ): The logger object to log
        Returns:
            none
        Raises:
            ValueError
    """
        
    try:
        connection_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=" + server + ";PORT=" + port + ";UID=" + uid + ";PWD=" + password + ";TrustServerCertificate=yes"
        connection = pyodbc.connect(connection_str)
        connection.autocommit = True
        cursor = connection.cursor()

        #Loop to get all the database names and db script files to create the databases
        for db_name, file_name in db_file_names.items():

            #Check if the database already exists
            check_db_query = f"SELECT name FROM sys.databases WHERE name = '{db_name}'"
            cursor.execute(check_db_query)
            db_exists = cursor.fetchone()
            if db_exists:
                print(f"Database '{db_name}' already exists.")
                log.logger.info(f"Database '{db_name}' already exists.")
                log.logger.info('Skipping database creation')
            
            else:
            #Read the sql script file to execute
                try:
                    with open(file_name, 'r') as file:
                        query = file.read()
                except FileNotFoundError:
                    log.logger.info(f'Error: {file_name} file not found')
                    print(f'Error: {file_name} file not found')
                    raise ValueError(f'Error: {file_name} file not found')
                except Exception as e:
                    log.logger.error(f'Error reading file: {e}')
                    print(f'Error reading file: {e}')
                    raise RuntimeError(f'Error reading file: {e}')
            
            commands = query.split('GO')

            #executing the sql queries
            for command in commands:
                command = textwrap.dedent(command.strip())
                if command:
                    try:
                        print(command)
                        log.logger.info(command)
                        cursor.execute(command)
                        cursor.commit()
                        log.logger.info('command executed successfully')
                        print('command executed successfully')

                    except pyodbc.Error as e:
                        print(f"Error: {e}")
            
            #Verifying the database created
            cursor.execute(check_db_query)
            db_exists = cursor.fetchone()
            if db_exists:
                log.logger.info('Database created successfully')
                print(f'Database created successfully {db_exists}')
            else:
                log.logger.debug('Database creation failed: '+ db_exists)
                raise ValueError('Database creation failed.')

        #list all the databases
        fetch_db_query = "SELECT name FROM sys.databases"
        cursor.execute(fetch_db_query)
        databases = cursor.fetchall()
        df = pd.DataFrame(databases, columns=['Database Name'])
        print(f'list of databases: {df}')
        log.logger.info(f'list of databases: {df}')
    
    except pyodbc.Error as e:
        print(f"Error connecting to mssql server: {e}")
        raise RuntimeError(f"Error connecting to mssql server: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
    

def drop_mssql_db(db_names, server, port, uid, password, log):
    """
        Name: drop_mssql_db
        Author: Dhanesh
        Desc: To drop the dbs in the mssql server as per the db names provided
        Parameters:
            server (string ): The mssql server name
            uid (string ): The user name
            password (string ): The user password
            db_names (list ): The data bae names to delete the databases
            port (int ): The connection port number
            log (logging ): The logger object to log
        Returns:
            none
        Raises:
            ValueError
    """

    try:
        connection_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=" + server + ";PORT=" + port + ";UID=" + uid + ";PWD=" + password + ";TrustServerCertificate=yes"
        connection = pyodbc.connect(connection_str)
        connection.autocommit = True
        cursor = connection.cursor()
        
        #Loop to get all the database names to drop
        for db_name in db_names:

            #Check if the database exists
            check_db_query = f"SELECT name FROM sys.databases WHERE name = '{db_name}'"
            log.logger.info(f"Database query is {check_db_query}")
            cursor.execute(check_db_query)
            db_exists = cursor.fetchone()

            #Drop database if exists else skip
            if db_exists:
                print(f"Database '{db_name}' is present in the mssql server")
                log.logger.info(f"Database '{db_name}' is present in the mssql server")
                log.logger.info(f'Dropping database {db_name}')
                drop_db_query = f"DROP DATABASE {db_name}"
                cursor.execute(drop_db_query)

                #Verifying the database deleted
                cursor.execute(check_db_query)
                db_exists = cursor.fetchone()
                if db_exists:
                    log.logger.debug(f'Database creation failed: {db_exists}')
                    raise ValueError('Database drop failed.')     
                else:
                    print(f'Database dropped successfully')
                    log.logger.info(f'Database {db_name} dropped successfully')
            else:
                log.logger.info(f"Database '{db_name}' is not present in the mssql server")
                log.logger.info(f"Skipping '{db_name}' database drop")
                print(f"Database '{db_name}' is not present in the mssql server")
                print(f"Skipping '{db_name}' database drop")

        #list all the databases
        fetch_db_query = "SELECT name FROM sys.databases"
        cursor.execute(fetch_db_query)
        databases = cursor.fetchall()
        df = pd.DataFrame(databases, columns=['Database Name'])
        print(f'list of databases: {df}')
        log.logger.info(f'list of databases: {df}')

    except pyodbc.Error as e:
            print(f"Error dropping the database in mssql server: {e}")
            raise RuntimeError(f"Error dropping the database in mssql server: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

def install_odbc_drivers(install_drivers_script_file, log):
    """
        Name: install_odbc_drivers
        Author: Dhanesh
        Desc: To run bash and install the required odbc drivers as per the os version
        Parameters:
            log (logging ): The logger object to log
        Returns:
            none
        Raises:
            FileNotFoundError, CalledProcessError, Exception
    """

    try:
        subprocess.run(["chmod", "+x", install_drivers_script_file])
        process = subprocess.run(["bash", install_drivers_script_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log.logger.info(process.stdout)
        print(process.stdout)
        if process.returncode != 0:
            log.logger.info(f"Error: {process.stderr}")
            print(f"Error: {process.stderr}")
            raise subprocess.CalledProcessError(process.returncode, process.args)
    except FileNotFoundError:
        log.logger.info(f"Error: Script file not found: {install_drivers_script_file}")
        print(f"Error: Script file not found: {install_drivers_script_file}")
    except subprocess.CalledProcessError as e:
        log.logger.info(f"Error: Script returned an error: {e}")
        print(f"Error: Script returned an error: {e}")
    except Exception as e:
        log.logger.info(f"Error: An error occurred: {e}")
        print(f"Error: An error occurred: {e}")