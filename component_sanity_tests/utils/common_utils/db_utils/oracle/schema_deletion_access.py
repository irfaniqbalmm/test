import os
import sys

import oracledb

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))

from utils.logger import logger

def drop_schema(cursor, schema):
    # Check if user exists
    cursor.execute("""
        SELECT COUNT(*) FROM dba_users WHERE username = :username
    """, {"username": schema.upper()})

    count, = cursor.fetchone()
    
    if count > 0:
        logger.info(f"User {schema} exists. Dropping...")
        try:
            cursor.execute(f'DROP USER {schema} CASCADE')
            logger.info(f"User {schema} dropped successfully.")
        except oracledb.DatabaseError as e:
            logger.error(f"Failed to drop user {schema}: {e}")
            raise
    else:
        logger.info(f"User {schema} does not exist. Skipping drop.")

def run_grant_script(db_user, db_password, db_host, db_service, target_schema, db_name=None, sql_file_path=None):
    dsn = oracledb.makedsn(db_host, 1521, service_name=db_service)
    connection = oracledb.connect(user=db_user, password=db_password, dsn=dsn, mode=oracledb.AUTH_MODE_DEFAULT)
    
    cursor = connection.cursor()

    # Drop schema if it exists
    drop_schema(cursor, target_schema)

    # # Read and process SQL
    with open(sql_file_path, 'r') as f:
        sql_script = f.read()

    sql_script = sql_script.replace("{DB_NAME}", db_name)

    for statement in sql_script.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            logger.info(f"Executing: {stmt}")
            cursor.execute(stmt)

    connection.commit()
    cursor.close()
    connection.close()
    logger.info("Schema setup and grants completed.")

# Example usage
run_grant_script(
    db_user="oracle",
    db_password="<password>",
    db_host="<host>",
    db_service="orclpdb1",
    target_schema="ICCSAPOS_Schema",
    sql_file_path="grant_access.sql"
)