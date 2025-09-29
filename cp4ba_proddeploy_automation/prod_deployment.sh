#!/bin/bash

#Checking the number of arguments are 18
if [ "$#" -ne 19 ]

then
  echo "Incorrect number of arguments"
  echo $# arguments
  exit 1
fi

# Set the path to your Python script
PYTHON_SCRIPT="prod_deployment.py"

# Check if the Python script exists
if [ -f "$PYTHON_SCRIPT" ]; then
    echo "Running $PYTHON_SCRIPT..."
    # Execute the Python script using the correct interpreter
    #you can run the command "which python3.9" to check the exact path of the interpreter
    #please replace the path if it is different.
    
    #python3 "$PYTHON_SCRIPT" db2 msad cp2400 master dev hulk pass spd fips meta extcrt

    python3 "$PYTHON_SCRIPT" $1 $2 $3 $4 $5 $6 $7 $8 $9 ${10} ${11} ${12} ${13} ${14} ${15} ${16} ${17} ${18} ${19}

    
    # Check the exit status of the Python script
 
    if [ $? -eq 0 ]; then
        echo "Script executed completed."
    else
        echo "Script execution failed."
        exit 1
    fi
else
    echo "Python script $PYTHON_SCRIPT not found."
    exit 1
fi

