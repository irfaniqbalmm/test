import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from utils.logger import logger

def check_logs(file_path, text_to_find):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if text_to_find in line:
                    return True
        return False
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
