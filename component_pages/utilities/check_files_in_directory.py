import os

def file_exists_in_directory(destination_path, file):
    """
    Method name: file_exists_in_directory
    Author: Anisha Suresh (anisha-suresh@ibm.com)
    Description: Check if the files exists in the directory
    Parameters:
        file : name of file to be checked
    Returns:
        True if exists else False
    """
    files = [f for f in os.listdir(destination_path) if f == file]
    return len(files) > 0