#!/bin/bash

SCHEMA="ICCSAPOS_SCHEMA"
DBNAME="OS1_QUR"

echo "Connecting to database $DBNAME..."
db2 connect to $DBNAME

# Drop Views
echo "Dropping views..."
db2 -x "SELECT 'DROP VIEW ' || VIEWSCHEMA || '.' || VIEWNAME || ';' FROM SYSCAT.VIEWS WHERE VIEWSCHEMA = '${SCHEMA}'" > drop_views.sql
db2 -tvf drop_views.sql

# Drop Triggers
echo "Dropping triggers..."
db2 -x "SELECT 'DROP TRIGGER ' || TRIGSCHEMA || '.' || TRIGNAME || ';' FROM SYSCAT.TRIGGERS WHERE TRIGSCHEMA = '${SCHEMA}'" > drop_triggers.sql
db2 -tvf drop_triggers.sql

# Drop Functions
echo "Dropping functions..."
db2 -x "SELECT 'DROP FUNCTION ' || FUNCSCHEMA || '.' || FUNCNAME || ';' FROM SYSCAT.FUNCTIONS WHERE FUNCSCHEMA = '${SCHEMA}'" > drop_functions.sql
db2 -tvf drop_functions.sql

# Drop Sequences
echo "Dropping sequences..."
db2 -x "SELECT 'DROP SEQUENCE ' || SEQSCHEMA || '.' || SEQNAME || ';' FROM SYSCAT.SEQUENCES WHERE SEQSCHEMA = '${SCHEMA}'" > drop_sequences.sql
db2 -tvf drop_sequences.sql

# Drop Tables
echo "Dropping tables..."
db2 -x "SELECT 'DROP TABLE ' || TABSCHEMA || '.' || TABNAME || ';' FROM SYSCAT.TABLES WHERE TABSCHEMA = '${SCHEMA}'" > drop_tables.sql
db2 -tvf drop_tables.sql

# Drop Schema
echo "Dropping schema..."
db2 "DROP SCHEMA ${SCHEMA} RESTRICT"

echo "Cleanup complete."
