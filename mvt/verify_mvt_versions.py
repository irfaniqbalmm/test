import os
import sys
import re
import csv
from pathlib import Path
from typing import Any, Literal

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from utils.bvt_status import update_status
from utils.check_cr_content import get_optional_components
from utils.logger import logger

class VerifyMvtVersion() :
    def __init__(self, product):
        """
        Method name: __init__
        Author: Anisha Suresh
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        self.product = product
        if self.product.upper() in ["CP4BA", "ADP"]:
            CONTENT = True
            config_file = "./inputs/config.toml"
        elif self.product.upper() in ["BAIS"]:
            CONTENT = False
            config_file = "./BAI_BVT/resources/config.toml"

        with open(config_file, "r") as file :
            input_data = parse(file.read())
            
        self.build = input_data['configurations']['build']
        self.ifix_version = input_data['configurations']['ifix_version']
        self.project_name = input_data['configurations']['project_name']
        self.git_user = input_data['git']['git_user']
        self.git_pwd = input_data['git']['git_pwd']
        self.generated_reports_path = input_data['paths']['generated_reports_path']
        self.download_directory = input_data['paths']['download_path']
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": f'{self.download_directory}',
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs",prefs)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        
    def file_exists_in_directory(self):
        """
        Method name : file_exists_in_directory
        Description : Checks if the IER file exists in the specified download directory.
        Parameters  :    None
        Returns     :
            True if file present else False.
        """
        files = [f for f in os.listdir(self.download_directory) if f == "FNCM, BAN, and ADP IFix Releases.xlsx"]
        return len(files) > 0

    def download_excel(self) :
        """
        Method name: download_excel
        Author: Anisha Suresh
        Description: Goes to the public box note url and downloads the excel file locally
        Parameters:
            None
        Returns:
            None
        """
        try : 
            file_url = 'https://ibm.box.com/shared/static/25j8j5ptvenktqndq26fqqwv77fg0hsr.xlsx'
            # Fetch the file content from the URL
            self.driver.get(file_url)
            WebDriverWait(self.driver, 60).until(lambda driver : self.file_exists_in_directory())
            self.driver.quit()
        except Exception as e :
            logger.error(f"An exception occured during download of excel file : {e}")
            logger.error("Couldn't complete download of excel file.")

    def normalize_version(self,version):
        # Replace underscores with dots and split the version string into components
        components = version.replace('_', '.').split('.')
        # Convert components to integers
        return [int(part) for part in components]

    def get_version_from_xl(self, component_name, filtered_df) :
        """
        Method name : get_version_from_xl
        Author      : Anisha Suresh
        Description : Fetch the version of compoenntss from the data frame
        Parameters  :
            filtered_df     : data frame
            component_name  : component for which version has to be fetched from the data frame
        Returns     :
            build_version   : build version of component from df
            liberty_version : liberty version of component from df
            java_version    : java version of component from df
            ubi_version     : ubi version of component from df
        """
        component = filtered_df[filtered_df.iloc[:, 1].str.lower() == component_name.lower()]
        build_version = 0
        liberty_version = 0
        java_version = 0
        ubi_version = 0
        if component.empty:
            logger.warning(f"NOT FOUND : {component_name} not verified")
        else :
            if '21.0.3' in self.build:
                build_version = component.iloc[0][5]
                liberty_version = component.iloc[0][6]
                java_version = component.iloc[0][7]
                ubi_version = component.iloc[0][8]
            elif self.build in ['22.0.2', '23.0.1', '23.0.2']:
                build_version = component.iloc[0][6]
                liberty_version = component.iloc[0][7]
                java_version = component.iloc[0][8]
                ubi_version = component.iloc[0][9]
            else: #24.0.0, 24.0.1, 25.0.0
                build_version = component.iloc[0][6]
                liberty_version = component.iloc[0][7]
                java_version = component.iloc[0][8]
                ubi_version = component.iloc[0][10]
            if component_name.lower() == "viewone":
                build_version = component.iloc[0][3]
        logger.info(f"Excel values for {component_name}: {build_version}, {liberty_version}, {java_version}, {ubi_version}")
        return build_version, liberty_version, java_version, ubi_version
    
    def get_mvt_csv(self, component_name):
        """
        Method name : get_mvt_csv
        Author      : Anisha Suresh
        Description : Fetch the version of compoenntss from the csv file
        Parameters  :
            component_name :  component for which version has to be fetched
        Returns     :    
            build_version, liberty_version, java_version and ubi_version from csv file
        """
        logger.info(f"Getting csv values for: {component_name}")
        mvt_csv = Path(self.generated_reports_path) / f"{self.project_name}_MVT.csv"
        if os.path.exists(mvt_csv):
            with open(mvt_csv, 'r') as csvfile :
                csv_reader = csv.reader(csvfile)
                found_component = False
                for row in csv_reader :
                    if row[0].lower() == component_name.lower() :
                        logger.info(f"CSV values for {component_name} are : {row[1]}, {row[2]}, {row[3]}, {row[4]}\n")
                        found_component = True
                        return row[1], row[2], row[3], row[4]
            if not found_component:
                return (None,) * 4
        else :
            logger.error("MVT CSV doesn't exits.")

    def extract_ifix_number(self) -> int:
        """
        Method name : extract_ifix_number
        Author      : Anisha Suresh
        Description : Extracts the numeric part of an IFIX version string.
        Parameters  : None
        Returns     :    
            int: The numeric part of the IFIX version, or -1 if no number is found.
        """
        match = re.search(r'\d+', self.ifix_version)
        return int(match.group()) if match else -1

    def is_ga_build(self) -> bool:
        """
        Method name : is_ga_build
        Author      : Anisha Suresh
        Description : Determine if a given ifix_version string represents a Generally Available (GA) build.
        Parameters  : None
        Returns     :    
            bool: If the ifix_version matches any of the strings in the tuple, the function returns True, else returns False
        """
        return self.ifix_version in ["IFix 0", "GA", "GM"]

    def format_ifix_tag(self, base_tag: str, ifix_number: int) -> str:
        """
        Method name : format_ifix_tag
        Author      : Anisha Suresh
        Description : Formats the tag name by appending the IFIX number with 3 digit padding to to the base tag.
        Parameters  :
            base_tag (str): The base tag string.
            ifix_number (int): The IFIX number to append to the base tag.
        Returns     :    
            str: The formatted tag string.
        """
        return f"{base_tag}-IF{ifix_number:03d}"
                    
    def _get_non_master_branch(self, base_tag: str, threshold: int, ifix_offset: int = 0) -> str:
        """
        Helper method to handle non-master branch logic.
        
        Parameters:
            base_tag (str): The base tag to use for formatting.
            threshold (int): The threshold value for ifix number comparison.
            ifix_offset (int, optional): Offset to add to the ifix number. Defaults to 0.
            
        Returns:
            str: The branch name based on the provided parameters.
        """
        if self.is_ga_build():
            return base_tag
        
        ifix_number = self.extract_ifix_number() + ifix_offset
        
        # For 21.0.3, we need to check if ifix_number is less than threshold
        if "21.0.3" in base_tag and ifix_number >= threshold:
            logger.error(f"Invalid IFix : {ifix_number}")
            return None
        elif "21.0.3" in base_tag:
            return self.format_ifix_tag(base_tag, ifix_number)
        
        # For other versions, return build if ifix_number >= threshold
        return self.build if ifix_number >= threshold else self.format_ifix_tag(base_tag, ifix_number)

    def get_branch_name(self) -> str:
        """
        Method name : get_branch_name
        Author      : Anisha Suresh
        Description : Determines the branch name based on the build version and ifix number.
        Parameters  : None
        Returns     :
            str: The branch name corresponding to the build version and ifix number.
        """
        tag_name = "CP4BA"
        
        # Define version configuration mapping
        version_config: dict[str, Any] = {
            "25.0.1": {"is_master": True},
            "25.0.0": {"base_tag": f"{tag_name}-25.0.0", "threshold": 1},
            "24.0.1": {"base_tag": f"{tag_name}-24.0.1", "threshold": 5},
            "24.0.0": {"base_tag": f"{tag_name}-24.0.0", "threshold": 6, "bais_offset": 2},
            "21.0.3": {"base_tag": f"{tag_name}-21.0.3", "threshold": 40}
        }
        
        # Check each version in the configuration
        for version, config in version_config.items():
            if version in self.build:
                # Special case for master branch
                if config.get("is_master", False):
                    return "master"
                
                # Apply BAIS offset if applicable
                ifix_offset: Any | Literal[0] = config.get("bais_offset", 0) if self.product.upper() == "BAIS" else 0
                
                # Use helper method for non-master branch logic
                return self._get_non_master_branch(
                    config["base_tag"],
                    config["threshold"],
                    ifix_offset
                )
        
        # No matching version found
        return None

    def clone_catalog(self):
        """
        Method name : clone_catalog
        Author      : Anisha Suresh
        Description : Clone the cert-kubernetes repo to get the catalog source file
        Parameters  : None
        Returns     : None
        """
        branch = self.get_branch_name()
        logger.info(f"Branch used to download catalog source file from : {branch}")
        url = f"https://raw.github.ibm.com/dba/cert-kubernetes/{branch}/descriptors/op-olm/catalog_source.yaml"
        logger.info(f"URL used to download catalog source file : {url}")
        response = requests.get(url, auth=HTTPBasicAuth(self.git_user, self.git_pwd))
        catalog_source_file = Path(self.download_directory) / 'catalog_source.yaml'
        logger.info(f"Setted catalog source path as : {catalog_source_file}")
        if response.status_code == 200:
            with open(catalog_source_file, "wb") as file :
                file.write(response.content)
            logger.info("Catalog source file downloaded.")
        else :
            logger.error("Couldn't download catalog source file.")

    def get_comments_from_catalog(self):
        """
        Method name : get_comments_from_catalog
        Author      : Anisha Suresh
        Description : Retrive the commented lines from catalog source file
        Parameters  : None
        Returns     :
            comments: comments retrived
        """
        comments = []
        catalog_file = Path(self.download_directory) / 'catalog_source.yaml'
        if os.path.exists(catalog_file) :
            with open(catalog_file,'r') as file :
                for line in file :
                    stripped_line =  line.strip()
                    if stripped_line.startswith('#') :
                        if self.build == "21.0.3":
                            if "IBM Cloud Foundational Services" in stripped_line :
                                version_pattern = r"#\s*(.*?)\s*(\d+(\.\d+)*$)"
                                match = re.search(version_pattern, stripped_line)
                                if match:
                                    comment_text = match.group(1)
                                    version = match.group(2)
                                    comments.append((comment_text, version))
                                logger.info(f"Comments retrived : {comments}")
                                return comments
                        else:
                            # version_pattern = r"^(.*?)\s+(\d+\.\d+\.\d+)(?:[^\d]*\((\d+\.\d+\.\d+)\))?.*?$"
                            # version_pattern = r"^(.*?)\s+(\d+\.\d+\.\d+(?:-IF\d+)?)(?:[^\d]*\((\d+\.\d+\.\d+)\))?.*?$"
                            version_pattern = r"^(.*?)\s+(\d+\.\d+\.\d+(?:-IF\d+)?)(?:[^\d]*\((\d+\.\d+\.\d+(?:\+[0-9.]+)?)\))?.*?$"

                            match = re.search(version_pattern, stripped_line)
                            if match:
                                comment_text = match.group(1).strip()
                                if "CP4BA" in comment_text :
                                    comment_text = " # Operator" #Changing comment text to Operator
                                version1 = match.group(3) if match.group(3) else match.group(2)
                                comments.append((comment_text, version1))
        else : 
            logger.error(f"{catalog_file} doesn't exists.")
        logger.info(f"Comments retrived : {comments}")
        return comments
    
    def _parse_version(self,version):
        """
        Method name : _parse_version
        Author      : Anisha Suresh
        Description : Extracts base version and converts IFxxx notation to numeric format.
        Parameters  : 
            version : version to be parsed
        Returns     :
            Tuple containing base version and IFxxx notation converted to numeric format.
        """
        try:
            match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:\s+IF(\d+))?", version)
            if not match:
                return None  
            major, minor, patch = map(int, match.groups()[:3])  # Extract main version
            fix_pack = match.group(4)  # Extract IFxxx number (if any)
            if fix_pack:
                patch += int(fix_pack)  # Convert IFxxx into patch level
            return (major, minor, patch)
        except Exception as e:
            logger.error(f"An exception occured during parsing of version : {e}")

    def _are_versions_equivalent(self,v1, v2):
        """
        Method name : _parse_version
        Author      : Anisha Suresh
        Description : Checks if version a is equivalent to or newer than version b.
        Parameters  : 
            v1 : version from csv file
            v2 : version from excel file
        Returns :
            True/False (boolean) : value indicating whether the versions are equivalent or not
        """
        version_a = self._parse_version(v1)
        version_b = self._parse_version(v2)
        return version_a >= version_b  # Compare tuple (major, minor, patch)

    def compare_operator_versions(self):
        """
        Method name : compare_operator_versions
        Author      : Anisha Suresh
        Description : Compare the operator versions from the downloaded the catalog source file
        Parameters  : None
        Returns     :
            result  : comparison result
        """
        result = ""
        comments = self.get_comments_from_catalog()
        logger.info("Comparing operator versions.")
        if self.build == "21.0.3" :
            csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version = self.get_mvt_csv("CPFS")
            if all(v is None for v in (csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version)):
                result = "Couldn't verify CPFS version. Please Verify Manually.<br>"
            elif csv_build_version == comments[0][1] :
                pass
            else : 
                cpfs_version = f"Mismatch in CPFS build version:<br> Actual version : {csv_build_version}<br>Expected value : {comments[0][1]}<br>"
                result += cpfs_version
        else :
            if self.product == "BAIS":
                components = {
                    "CPFS": False, 
                    "Zen": False, 
                    "Flink": False, 
                    "OS": False, 
                    "BAI": False,
                }
            elif self.product in ["CP4BA"]:
                components = {
                    "Operator": False,
                    "CPFS": False, 
                    "Zen": False, 
                    "Flink": False, 
                    "OS": False, 
                    "BAI": False,
                }
            elif self.product in ["ADP"]:
                components = {
                    "Operator": False,
                    "CPFS": False, 
                    "Zen": False, 
                }
            for operator,version in comments : 
                for component in components :
                    csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version = self.get_mvt_csv(component)
                    if all(v is None for v in (csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version)):
                        result = f"Couldn't verify {component} version. Please Verify Manually.<br>"
                    elif component == 'BAI' and components[component] != True:
                        components[component] = True
                        if self.build in csv_build_version :
                            pass
                        else : 
                            component_version = f"Mismatch in {component} build version:<br> Actual version : {csv_build_version}<br>Expected value : {self.build}<br>"
                            result += component_version
                        
                    elif component == "Operator" and components[component] != True:
                        components[component] = True
                        version_match =  re.search(r"(?<=Version :\s)\d+\.\d+\.\d+", csv_build_version)
                        if version_match:
                            operator_version = version_match.group()
                            if (self._are_versions_equivalent(operator_version,version)):
                                pass
                            else:
                                component_version = f"Mismatch in {component} build version:<br> Actual version : {csv_build_version}<br>Expected value : {version}<br>"
                                result += component_version
                        else :
                            result += f"Couldn't verify {component} version. Please verify manually."
                    elif ((component in operator) or (component == 'CPFS' and 'Foundational Services' in operator) or (component == 'OS' and 'Opensearch' in operator)) and components[component] != True:
                        components[component] = True
                        if csv_build_version == version :
                            pass
                        elif str(csv_build_version) in str(version):
                            pass
                        else : 
                            component_version = f"Mismatch in {component} build version:<br> Actual version : {csv_build_version}<br>Expected value : {version}<br>"
                            result += component_version
        if result :
            logger.error(f"Operators comparing result : {result}")
        return result
    
    def _strip_trailing_zeros(self, version):
        """
        Method name : _strip_trailing_zeros
        Author      : Anisha Suresh
        Description : Strip the trailing zereos from a version string
        Parameters  :
            version (str)    : version string to be stripped off trailing zeroes
        Returns :
            stripped_version : version that is stripped off trailing zeroes
        """
        try:
            logger.info(f"Stripping the zeroes out of {version}")
            stripped_version = re.sub(r'(\.0)+$', '', version)
            logger.info(f"Stripped version : {stripped_version}")
            return stripped_version
        except Exception as e:
            logger.error(F"An exception occured while  stripping the version of zeroes : {e}")

    def clean_version(self, version):
        """
        Method name : clean_version
        Author      : Anisha Suresh
        Description : Remove any -0- sequences from versions
        Parameters  :
            version (str): The version string to clean.
        Returns:
            str: The cleaned version string.
        """
        return re.sub(r'(-0)+-', '-', version)

    def comparison(self, filtered_df, component_name):
        """
        Method name : comparison
        Author      : Anisha Suresh
        Description : Compare the build versions from the downloaded the excel file
        Parameters  :
            filtered_df     : df containing the deatils of particulr ifix version
            component_name  : component for which version has to be fetched
        Returns     :
            result  : comparison result
        """
        result = ""
        try :
            xl_build_version, xl_liberty_version, xl_java_version, xl_ubi_version = self.get_version_from_xl(component_name.replace(" ", ""), filtered_df)

            csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version = self.get_mvt_csv(component_name)
            if all(v is None for v in (csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version)):
                result = f"Couldn't verify {component_name} version. Please Verify Manually.<br>"
                return result
            try :
                if str(xl_build_version) in str(csv_build_version):
                    build_version = ""
                elif self.clean_version(xl_build_version) in str(csv_build_version):
                    build_version = ""
                elif str(csv_build_version) in str(xl_build_version):
                    build_version = ""
                else : 
                    build_version = f"Mismatch in {component_name} build version:<br> Actual version : {csv_build_version}<br>  Expected value : {xl_build_version}<br>"
                result += build_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} build version : {e}")
                result += f"Couldn't verify {component_name} build version. Please verify manually<br>"
            # Liberty version check
            try :
                # These components does not have liberty
                if component_name in ["CSS", "CDS", "Mongo", "Git Gateway"] :
                    liberty_version = ""   
                elif str(xl_liberty_version) == str(csv_liberty_version):
                    liberty_version = ""
                elif "_" in str(xl_liberty_version) : 
                    xl_liberty_version_list = self.normalize_version(xl_liberty_version)
                    csv_liberty_version_list = self.normalize_version(csv_liberty_version)
                    if xl_liberty_version_list == csv_liberty_version_list :
                        liberty_version = ""
                    else :
                        liberty_version = f"Mismatch in {component_name} liberty version:<br> Actual version : {csv_liberty_version}<br>Expected value : {xl_liberty_version}<br>"
                else : 
                    liberty_version = f"Mismatch in {component_name} liberty version:<br> Actual version : {csv_liberty_version}<br>Expected value : {xl_liberty_version}<br>"
                result += liberty_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} liberty version : {e}")
                result += f"Couldn't verify {component_name} liberty version. Please verify manually<br>"
            # Java version check
            try :
                logger.info(f"Checking {component_name} java version")
                # These components does not have java
                if component_name in ["CDS", "Mongo"] :
                    java_version = ""
                elif str(csv_java_version) in str(xl_java_version):
                    java_version = ""
                elif str(self._strip_trailing_zeros(csv_java_version)) in str(xl_java_version) :
                    java_version = ""
                else :
                    java_version = f"Mismatch in {component_name} java version:<br>Actual version : {csv_java_version}<br>Expected value : {xl_java_version}<br>"
                result += java_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} java version : {e}")
                result += f"Couldn't verify {component_name} java version. Please verify manually<br>"
            # UBI version check
            try :
                logger.info(f"Checking {component_name} UBI version")
                # These components does not have ubi version check
                if component_name in ["Mongo"] :
                    ubi_version = ""
                elif str(csv_ubi_version) in str(xl_ubi_version):
                    ubi_version = ""
                else :
                    ubi_version = f"Mismatch in {component_name} ubi version:<br>Actual version : {csv_ubi_version}<br>Expected value : {xl_ubi_version}<br>"
                result += ubi_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} ubi version : {e}")
                result += f"Couldn't verify {component_name} ubi version. Please verify manually<br>"
            if component_name == "CPE" :
                return xl_liberty_version,xl_java_version,xl_ubi_version,result
        except Exception as e:
            logger.error(f"Couldn't verify {component_name} build version : {e}")
            result += f"Couldn't verify {component_name} versions. Please verify manually<br>"
        if result:
            logger.error(f"Comparison result : {result}")
        return result
    
    def compare_major_builds(self, df, xl_liberty_version, xl_java_version, xl_ubi_version, component_name) :
        """
        Method name : compare_major_builds
        Author      : Anisha Suresh
        Description : Compare the build versions of major builds from the downloaded the excel file
        Parameters  :
            df                  : data frame from downloaded excel
            xl_liberty_version  : expected liberty version from excel
            xl_java_version     : expected java version from excel
            xl_ubi_version      : expected ubi version from excel
            component_name      : component for which version has to be fetched
        Returns     :
            result  : comparison result
        """
        result = ""
        try :
            logger.info("Comparing major build versions.")
            csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version = self.get_mvt_csv(component_name)
            if all(v is None for v in (csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version)):
                result = f"Couldn't verify {component_name} version. Please Verify Manually.<br>"
                return result
            if str(component_name).lower() == "css" and "24.0.1" in self.build:
                xl_build_version = df['Final build version']
            else:
                xl_build_version = df['Final build version'].iloc[0]
            pos = xl_build_version.find(':')
            if pos != -1:
                # Return the substring after the colon, stripping any leading/trailing whitespace
                xl_build_version = xl_build_version[pos+1:].strip()
            try:
                if str(xl_build_version) in str(csv_build_version) :
                    build_version = ""
                elif str(csv_build_version) in str(xl_build_version):
                    build_version = ""
                elif self.clean_version(xl_build_version) in str(csv_build_version):
                    build_version = ""
                else :
                    build_version = f"Mismatch in {component_name} build version:<br> Actual version : {csv_build_version}<br>  Expected value : {xl_build_version}<br>"
                result += build_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} build version : {e}")
                result += f"Couldn't verify {component_name} build version. Please verify manually<br>"
            try :
                if component_name == "CSS" :
                    liberty_version = ""   
                elif str(xl_liberty_version) == str(csv_liberty_version):
                    liberty_version = ""
                elif "_" in str(xl_liberty_version) : 
                    xl_liberty_version_list = self.normalize_version(xl_liberty_version)
                    csv_liberty_version_list = self.normalize_version(csv_liberty_version)
                    if xl_liberty_version_list == csv_liberty_version_list :
                        liberty_version = ""
                    else :
                        liberty_version = f"Mismatch in {component_name} liberty version:<br> Actual version : {csv_liberty_version}<br>Expected value : {xl_liberty_version}<br>"
                else : 
                    liberty_version = f"Mismatch in {component_name} liberty version: <br>  Actual version : {csv_liberty_version}<br>   Expected value : {xl_liberty_version}<br>"
                result += liberty_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} liberty version : {e}")
                result += f"Couldn't verify {component_name} liberty version. Please verify manually<br>"
            try:
                if csv_java_version in xl_java_version:
                    java_version = ""
                elif str(self._strip_trailing_zeros(csv_java_version)) in str(xl_java_version) :
                    java_version = ""
                else :
                    java_version = f"Mismatch in {component_name} java version:<br>  Actual version : {csv_java_version}<br>  Expected value : {xl_java_version}<br>"
                result += java_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} java version : {e}")
                result += f"Couldn't verify {component_name} java version. Please verify manually<br>"
            # UBI version
            try:
                if csv_ubi_version in str(xl_ubi_version):
                    ubi_version = ""
                else :
                    ubi_version = f"Mismatch in {component_name} UBI version:<br>  Actual version : {csv_ubi_version}<br>  Expected value : {xl_ubi_version}<br>"
                result += ubi_version
            except Exception as e:
                logger.error(f"Couldn't verify {component_name} UBI version : {e}")
                result += f"Couldn't verify {component_name} UBI version. Please verify manually<br>"
        except Exception as e: 
            logger.error(f"Couldn't verify {component_name} build version : {e}")
            result += f"Couldn't verify {component_name} versions. Please verify manually<br>"
        if result :
            logger.error(f"Major builds comparison result : {result}")
        return result
        
    def comparison_liberty(self, component_name, xl_liberty_version) :
        """
        Method name : comparison_liberty
        Author      : Anisha Suresh
        Description : Compare the liberty version of a component
        Parameters  :
            xl_liberty_version  : expected liberty version from excel
            component_name      : component for which version has to be fetched
        Returns     :
            result  : comparison result
        """
        result = ""
        try:
            csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version = self.get_mvt_csv(component_name)
            if all(v is None for v in (csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version)):
                result = f"Couldn't verify {component_name} liberty version. Please Verify Manually.<br>"
                return result
            if str(xl_liberty_version) == str(csv_liberty_version):
                liberty_version = ""
            elif "_" in xl_liberty_version : 
                    xl_liberty_version_list = self.normalize_version(xl_liberty_version)
                    csv_liberty_version_list = self.normalize_version(csv_liberty_version)
                    if xl_liberty_version_list == csv_liberty_version_list :
                        liberty_version = ""
                    else :
                        liberty_version = f"Mismatch in {component_name} liberty version:<br> Actual version : {csv_liberty_version}<br>Expected value : {xl_liberty_version}<br>"
            else : 
                liberty_version = f"Mismatch in {component_name} liberty version:<br> Actual version : {csv_liberty_version}<br>Expected value : {xl_liberty_version}<br>"
            result += liberty_version
        except Exception as e:
            logger.error(f"Couldn't verify {component_name} liberty version : {e}")
            result += f"Couldn't verify {component_name} liberty version. Please verify manually<br>"
        return result
    
    def comparison_java_ubi(self, component_name, xl_java_version, xl_ubi_version) :
        """
        Method name : comparison_java_ubi
        Author      : Anisha Suresh
        Description : Compare the java and ubi versions of a component
        Parameters  :
            xl_java_version : expected java version from excel
            xl_ubi_version  : expected ubi version from excel
            component_name  : component for which version has to be fetched
        Returns     :
            result  : comparison result
        """
        result = ""
        csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version = self.get_mvt_csv(component_name)
        if all(v is None for v in (csv_build_version, csv_liberty_version, csv_java_version, csv_ubi_version)):
            result = f"Couldn't verify {component_name} Java and UBI versions. Please Verify Manually.<br>"
            return result
        try:
            if str(csv_java_version) in str(xl_java_version):
                java_version = ""
            elif str(self._strip_trailing_zeros(csv_java_version)) in str(xl_java_version) :
                java_version = ""
            else : 
                java_version = f"Mismatch in {component_name} java version:<br> Actual version : {csv_java_version}<br>Expected value : {xl_java_version}<br>"
            result += java_version
        except Exception as e:
            logger.error(f"Couldn't verify {component_name} java version : {e}")
            result += f"Couldn't verify {component_name} java version. Please verify manually<br>"
        try :
            if str(csv_ubi_version) in str(xl_ubi_version):
                ubi_version = ""
            else : 
                ubi_version = f"Mismatch in {component_name} UBI version:<br> Actual version : {csv_ubi_version}<br>Expected value : {xl_ubi_version}<br>"
            result += ubi_version
        except Exception as e:
            logger.error(f"Couldn't verify {component_name} UBI version : {e}")
            result += f"Couldn't verify {component_name} UBI version. Please verify manually<br>"
        return result
    
    def compare_css_liberty(self, filtered_df, csv_liberty_version):
        """
        Method name : compare_css_liberty
        Author      : Anisha Suresh
        Description : Compare the liberty version of a CSS
        Parameters  :
            xl_liberty_version  : expected liberty version from excel
            filtered_df         : df containing the filetered ifixes
        Returns     :
            result  : comparison result
        """
        result = ""
        try :
            xl_build_version, xl_liberty_version, xl_java_version, xl_ubi_version = self.get_version_from_xl("CSS",filtered_df)
            if csv_liberty_version == xl_liberty_version : 
                liberty_version = ""
            else : 
                liberty_version = f"Mismatch in CSS liberty version:<br> Actual version : {csv_liberty_version}<br>Expected value : {xl_liberty_version}<br>"
            result += liberty_version
        except Exception as e:
            logger.error(f"Couldn't verify CSS liberty version : {e}")
            result += "Couldn't verify CSS liberty version. Please verify manually<br>"
        return result
    
    def verification(self) :
        """
        Method name: verification
        Author: Anisha Suresh
        Description: Performs MVT verification
        Parameters:
            None
        Returns:
            summary : Summary of BVT verification in html format
        """
        logger.info("MVT Verfication begins ...")
        comparison_result = ""
        try :
            version = self.build
            build = re.match(r'^(\d+\.\d+\.\d+)', version).group(1)
            ifix_version = self.ifix_version
            self.download_excel()
            file_content = f'{self.download_directory}/FNCM, BAN, and ADP IFix Releases.xlsx'
            xls = pd.ExcelFile(file_content)
            sheets = xls.sheet_names
            for sheet in sheets :
                if build in sheet:
                    df = pd.read_excel(file_content,sheet_name=sheet,engine='openpyxl')
            
            if self.product.upper() == "BAIS":
                # For BAIS only BAI versions has to be compared.
                optional_components = ["BAI"]
            else:
                # Getting optional components
                optional_components = get_optional_components()

            if self.is_ga_build():
                logger.info(f"Executing {ifix_version} build verification")
                xl_liberty_version = df.iloc[2,5]
                xl_java_version = df.iloc[2,6]
                xl_ubi_version = df.iloc[2,7]

                if self.product.upper() in ['CONTENT', 'CP4BA', 'ADP']:
                    components = {
                        "cpe": "CPE",
                        "graphql": "GraphQL",
                        "nav": "Navigator",
                        "cds": "CDS",
                        "cpds": "CPDS",
                        "cdra": "CDRA",
                        "viewone": "ViewOne",
                        "mongo": "Mongo",
                        "gitgateway": "Git Gateway"}
                    
                    for component, tag in components.items():
                        component_df = df[df.iloc[:, 0] == f"{component}:{build}"]
                        comparison_result += self.compare_major_builds(component_df, xl_liberty_version, xl_java_version, xl_ubi_version, tag)

                    # Content/CP4BA operator java and UBI versions can be comapared here using a common value(Because we don't have operator reference versions in excel)
                    operator_java_comparison_result = self.comparison_java_ubi("Operator", xl_java_version, xl_ubi_version)
                    comparison_result += operator_java_comparison_result

                #cmis
                if 'CMIS' in optional_components : 
                    cmis_df = df[df.iloc[:, 0] == f"cmis:{build}"]
                    comparison_result += self.compare_major_builds(cmis_df, xl_liberty_version, xl_java_version, xl_ubi_version, "CMIS")
                #css
                if 'CSS' in optional_components : 
                    # In 24.0.1 GA build, the CSS build version is separated into the second line of the actual expected index
                    if "24.0.1" in self.build :
                        real_css_df = df[df.iloc[:, 0] == f"css:{build}"]
                        css_index = real_css_df.index
                        if not css_index.empty :
                            css_df = df.iloc[css_index[0]+ 1]
                    else :
                        css_df = df[df.iloc[:, 0] == f"css:{build}"]
                    comparison_result += self.compare_major_builds(css_df, xl_liberty_version, xl_java_version, xl_ubi_version, "CSS")
                #TM
                if 'TM' in optional_components:
                    tm_df = df[df.iloc[:, 0] == f"taskmgr:{build}"]
                    comparison_result += self.compare_major_builds(tm_df, xl_liberty_version, xl_java_version, xl_ubi_version, "TM")
                #IER
                if 'IER' in optional_components:
                    ier_liberty_comparison_result = self.comparison_liberty("IER", xl_liberty_version)
                    comparison_result += ier_liberty_comparison_result
                    ier_java_comparison_result = self.comparison_java_ubi("IER", xl_java_version, xl_ubi_version)
                    comparison_result += ier_java_comparison_result
                #ICCSAP
                if 'ICCSAP' in optional_components:
                    iccsap_java_comparison_result = self.comparison_java_ubi("ICCSAP", xl_java_version, xl_ubi_version)
                    comparison_result += iccsap_java_comparison_result
                # BAI
                # For BAI build version check is similar to Operator, but we can check the liberty, java and UBI versions from the excel sheet
                if 'BAI' in optional_components:
                    bai_java_comparison_result = self.comparison_java_ubi("BAI", xl_java_version, xl_ubi_version)
                    comparison_result += bai_java_comparison_result

            else :
                
                if self.build == "24.0.0" and self.product.upper() == "BAIS":
                    ifix_number =  self.extract_ifix_number() + 2
                    ifix_version = f"IFix {ifix_number}"
                logger.info(f"Executing {self.build} {ifix_version} build verification.")
                filtered_df = df[df.iloc[:, 0] == ifix_version]
                logger.info(f"Filtered data frame for ifix : {filtered_df}")
                # These are CONTENT only mandatory components
                if self.product.upper() in ['CP4BA', 'CONTENT', 'ADP']:
                    #CPE
                    liberty_version, java_version, ubi_version, cpe_comparison_result = self.comparison(filtered_df, "CPE")
                    comparison_result += cpe_comparison_result
                    if "document_processing_designer" in optional_components:
                        components = ["GraphQL", "Navigator", "CPDS", "CDS", "CDRA", "ViewOne", "Mongo", "Git Gateway"]
                    else:
                        components = ["GraphQL", "Navigator"]
                    for component in components:
                        component_comparison_result = self.comparison(filtered_df, component)
                        comparison_result += component_comparison_result
                    operator_java_comparison_result = self.comparison_java_ubi("Operator", java_version, ubi_version)
                    comparison_result += operator_java_comparison_result
                elif self.product.upper() == "BAIS":
                    build_version, liberty_version, java_version, ubi_version = self.get_version_from_xl("BAI", filtered_df)
                    logger.info(f"Expected versions of BAI are: build_version: {build_version}, liberty_version: {liberty_version}, java_version: {java_version}, ubi_version: {ubi_version}")
                #CMIS
                if 'CMIS' in optional_components : 
                    cmis_comparison_result = self.comparison(filtered_df, "CMIS")
                    comparison_result += cmis_comparison_result
                #CSS
                if 'CSS' in optional_components : 
                    css_comparison_result = self.comparison(filtered_df, "CSS")
                    css_liberty_comparison_result = self.compare_css_liberty(filtered_df, liberty_version)
                    comparison_result += css_liberty_comparison_result
                    comparison_result += css_comparison_result
                #TM
                if 'TM' in optional_components :
                    tm_comparison_result = self.comparison(filtered_df, "TM")
                    comparison_result += tm_comparison_result
                #IER
                if 'IER' in optional_components :
                    ier_liberty_comparison_result = self.comparison_liberty("IER", liberty_version)
                    comparison_result += ier_liberty_comparison_result
                    ier_java_comparison_result = self.comparison_java_ubi("IER", java_version, ubi_version)
                    comparison_result += ier_java_comparison_result
                #ICCSAP
                if 'ICCSAP' in optional_components :
                    iccsap_java_comparison_result = self.comparison_java_ubi("ICCSAP", java_version, ubi_version)
                    comparison_result += iccsap_java_comparison_result
                # BAI
                # For BAI build version check is similar to Operator, but we can check the java and UBI versions from the excel sheet
                if 'BAI' in optional_components:
                    # BAI doesn't have liberty
                    bai_java_comparison_result = self.comparison_java_ubi("BAI", java_version, ubi_version)
                    comparison_result += bai_java_comparison_result
                
            logger.info("Cloning cert-kubernetes...")
            self.clone_catalog()
            comparison_result += self.compare_operator_versions()

            #Return summary
            if comparison_result == "" :
                logger.info("MVT is successful")
                mvt_status = "PASSED"
                if self.product in  ['CP4BA', 'CONTENT']:
                    update_status("MVT", mvt_status)
                summary = (
                    '<div style="margin-bottom :10px;">'
                    f'<span style="color: black;font-size: 16px;margin-bottom: 6px;"><b>SUMMARY : </b></span><br>'
                    '<span>Results : </span>'
                    f'<span style="color: green;"><b>{mvt_status}</b></span><br>'
                    '</div>'
                )
            else :
                mvt_status = "FAILED"
                logger.error(comparison_result)
                summary = (
                    '<div style="margin-bottom :10px;">'
                    f'<span style="color: black;font-size: 16px;margin-bottom: 6px;"><b>SUMMARY : </b></span><br>'
                    '<span>Results : </span>'
                    f'<span style="color: red;"><b>{mvt_status}</b></span><br>'
                    f'<span style="color: red;">{comparison_result}</span>'
                    '</div>'
                )
        except Exception as e:
            logger.error(f"An exception occured during comparison of MVT results : {e}")
            logger.warning("Could not verify MVT. Please verify manually.")
            summary = (
                       '<div style="margin-bottom :10px;">'
                       '<span style="color: black;font-size: 16px;margin-bottom: 6px;"><b>SUMMARY : </b></span><br>'
                       '<span style="color: red;">Could not verify MVT. Please verify manually.</span><br>'
                       '</div>'
                    )
        return summary

if __name__ =="__main__" :
    verify_mvt_version = VerifyMvtVersion("ADP")
    verify_mvt_version.verification()

