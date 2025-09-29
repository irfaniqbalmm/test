import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from tomlkit import parse
from utils.logger import logger

class PrepareProfile():
    def __init__(self, config_file):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Initializes the PrepareProfile class by reading the configuration from a TOML file.
        Parameters: 
            config_file: Path to the configuration file
        Returns: None
        """
        with open(config_file, "r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.namespace = self.config['configurations']['project_name']

        self.resources_path =  self.config['iccsap']['resources']

    def replace_word_in_file(self, file_path, target_word, new_word):
        """
        Method name: replace_word_in_file
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Replaces all occurrences of a target word with a new word in a given file.
        Parameters:
            file_path (str): The path to the file to be modified.
            target_word (str): The word to be replaced.
            new_word (str): The word to replace the target_word.
        Returns: None
        """

        logger.info(f"Opening file: {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()

        logger.info(f"Updating {target_word} to {new_word}")
        updated_content = content.replace(target_word, new_word)

        logger.info(f"Writing updates to profile file: {file_path}")
        with open(file_path, 'w') as f:
            f.write(updated_content)

    def prepare_profile(self):
        """
        Method name: prepare_profile
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Prepares the profile by replacing placeholders in the archint.ini file with actual username and namespace.
        Parameters: None
        Returns: None
        """
        profile_file_path = os.path.join(self.resources_path, 'archint.ini')
        logger.info(f"Profile file path: {profile_file_path}")

        logger.info(f"Replacing namespace as: {self.namespace}")
        self.replace_word_in_file(profile_file_path, '<namespace>', self.namespace)
        
        logger.info(f"Replacing username as: {self.username}")
        self.replace_word_in_file(profile_file_path, '<username>', self.username)

        return profile_file_path
    
    def restore_profile(self):
        """
        Method name: prepare_profile
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Description: Restores the profile file by replacing actual values in the archint.ini file with placeholders.
        Parameters: None
        Returns: None
        """
        profile_file_path = os.path.join(self.resources_path, 'archint.ini')
        logger.info(f"Profile file path: {profile_file_path}")

        logger.info(f"Replacing namespace placeholder")
        self.replace_word_in_file(profile_file_path, self.namespace, '<namespace>')
        
        logger.info(f"Replacing username placeholder")
        self.replace_word_in_file(profile_file_path, self.username, '<username>')

        return profile_file_path

if __name__ == "__main__":
    # TESTER CODE
    prepare_profile = PrepareProfile("./component_sanity_tests/config/config.toml")
    prepare_profile.prepare_profile()
    prepare_profile.restore_profile()

