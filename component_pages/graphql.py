import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import urllib.parse
from termcolor import colored
from tomlkit import parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import inputs.locators as locators
from utils.bvt_status import update_status
from utils.logger import logger

class GraphQLTester:
    graphql_status = "FAILED"

    def __init__(self):
        """
        Method name: __init__
        Description: Initializes the WebDriver with specified options and settings.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting execution of GraphQL BVT==========================================")
        logger.info("Initialising chrome driver for graphql execution ...")
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--incognito")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        logger.info("Chromedriver initialised.")
        logger.info("Setting initial URL to 'None' value.")
        self.initial_url = None

        with open("./inputs/config.toml","r") as file :
            self.config = parse(file.read())
        
        self.username = self.config['credentials']['app_login_username']
        self.password = self.config['credentials']['app_login_password']
        self.screenshot_path = self.config['paths']['screenshot_path']
        self.deployment_type = self.config['configurations']['deployment_type']
        self.graphql_folder_name = self.config['graphql']['graphql_folder_name']
        self.s_graphqlcmd1 = self.config['graphql']['s_graphqlcmd1']
        self.s_graphqlcmd2 = self.config['graphql']['s_graphqlcmd2']
        self.s_graphqlcmd3 = self.config['graphql']['s_graphqlcmd3']
        self.graphqlcmd1 = self.config['graphql']['graphqlcmd1']
        self.graphqlcmd2 = self.config['graphql']['graphqlcmd2']
        self.graphqlcmd3 = self.config['graphql']['graphqlcmd3']

    def login(self):
        """
        Method name: login
        Description: Login to graphql page
        Parameters:
            None
        Returns:
            None
        """
        logger.info("Logging in to GraphQL API page ...")
        with open('./inputs/endpoints.json', 'r') as json_file:
            endpoints = json.load(json_file)
        graphql_route = endpoints.get("graphql_route")
        logger.info(f"Loading GraphQL API page : {graphql_route}")
        self.driver.get(graphql_route)
        try : 
            self.driver.find_element(By.CLASS_NAME, locators.LocatorElements.enterpriseLDAP).click()
            logger.info("Clicked on enterprise LDAP option for login!")
        except Exception as e:
            logger.debug(f"An exception occured during clicking enterprise LDAP option : {e}")
            logger.warning("Retrying using dropdown option ...")
            dropdown_element = self.driver.find_element(By.ID,"login_options")
            select = Select(dropdown_element)
            select.select_by_visible_text("Enterprise LDAP")
            logger.info("Clicked on enterprise LDAP option for login!")
        self.driver.find_element(By.ID, locators.LocatorElements.acceUsername).send_keys(self.username)
        logger.info(f"Username send: {self.username}")
        self.driver.find_element(By.ID, locators.LocatorElements.accePassword).send_keys(self.password)
        logger.info(f"Password send : {self.password}")
        self.driver.find_element(By.NAME, locators.LocatorElements.loginbtn).click()
        logger.info("Login button clicked!")
        time.sleep(5)
        for i in (0,3) :
            logger.info(f"Attempt {i+1}: Trying to navigate to  graphql endpoint...")
            try :
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'graphiql')))
                logger.info("GraphQL API page is loaded!")
                break
            except Exception as e: 
                logger.error(f"An exception occured during loading Graphql API : {e}")
                logger.info("Retrying to see if the page is loaded ...")
                self.driver.execute_script("window.open('', '_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(graphql_route) 
                i = i+1
                continue
        logger.info("Setting initial url as the current url.")
        self.initial_url = self.driver.current_url

    def execute_query(self, new_data, screenshot_name,n):
        """
        Method name: execute_query
        Description: Execute grapql query
        Parameters:
            query : graphql query that needs to be executed
            screenshot_name : name of screenshot to be saved
        Returns:
            None
        """
        self.driver.execute_script(f'dfltQryTxt = `{new_data}`;')
        self.driver.refresh()
        encoded_query = urllib.parse.quote(new_data)
        new_url = f'{self.driver.current_url}?query={encoded_query}'
        logger.info("Loading new query ...")
        self.driver.get(new_url)
        time.sleep(2)
        logger.info("Query loaded.")
        execute_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, locators.LocatorElements.graphql_run)))
        execute_button.click()
        logger.info("Clicked execute button.")
        time.sleep(5)
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        required_height = total_height*n
        self.driver.set_window_size(1920, int(required_height))
        self.driver.save_screenshot(screenshot_name)
        logger.info("Query execution completed!")
        logger.info(f"Saving screenshot : {screenshot_name}.")
        self.driver.maximize_window()

    def run_test(self):
        """
        Method name: run_test
        Description: Run graphql testes
        Parameters:
            None
        Returns:
            graphql_status : Status of graphql testes
        """
        try:
            self.login()
            if self.deployment_type == 'starter' :
                query_1 = self.s_graphqlcmd1
            else : 
                query_1 = self.graphqlcmd1
            logger.info(f"Starting to execute qraphql query1 ...")
            self.execute_query(query_1, f'{self.screenshot_path}/graphql1.png',3/4)
            try :
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.graphql_check)))
                logger.error("Graphql Query1: FAILED. GraphQL Execution FAILED! Errors present in GraphQL page.")
            except : 
                logger.info("Graphql Query1: PASSED")
            logger.info("Loading intial url ...")
            self.driver.get(self.initial_url)
            time.sleep(2)

            if self.deployment_type == 'starter' :
                query_2 = self.s_graphqlcmd2
            else : 
                query_2 =self.graphqlcmd2
            logger.info(f"Starting to execute qraphql query2 ...")
            logger.info("This query creates the folder in the ACCE.")
            self.execute_query(query_2, f'{self.screenshot_path}/graphql2.png',0.95)
            try :
                logger.info("Executing check for succesfull query execution ...")
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.graphql_check)))
                logger.warning("Graphql Query2: FAILED!! Errors present in GraphQL page. This error will be ignored, assuming the intended folder is already created once.")
            except : 
                logger.info("Graphql Query2: PASSED. Folder created sucessfully.")
                logger.info(f"Folder created using graphql API is : {self.graphql_folder_name}")
            logger.info("Loading intial url ...")
            self.driver.get(self.initial_url)
            time.sleep(2)
            if self.deployment_type == 'starter' :
                query_3 = self.s_graphqlcmd3
            else : 
                query_3 = self.graphqlcmd3
            logger.info(f"Starting to execute qraphql query3 ...")
            self.execute_query(query_3, f'{self.screenshot_path}/graphql3.png',1)
            try :
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, locators.LocatorElements.graphql_check)))
                logger.critical("Graphql Query3: FAILED. GraphQL Execution FAILED! Errors present in GraphQL page.")
                graphql_status = "FAILED"
            except : 
                logger.info("Graphql Query3: PASSED")
                graphql_status = "PASSED"

            logger.info("Capturing GraphQL ping page for MVT ...")
            ping_url = urllib.parse.urljoin(self.initial_url, "ping")
            logger.info(f"Setting ping url to : {ping_url}")
            self.driver.get(ping_url)
            logger.info("Loading ping page ...")
            time.sleep(10)
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            total_hidth = self.driver.execute_script("return document.body.scrollWidth")
            required_height = total_height*0.5
            required_width = total_hidth*0.5
            self.driver.set_window_size(int(required_width), int(required_height))
            self.driver.save_screenshot(f'{self.screenshot_path}/mvt_graphql_ping_page.png')
            logger.info(f"Saved screenshot of graphql ping page : {f'{self.screenshot_path}/mvt_graphql_ping_page.png'}")
        except Exception as e:
            logger.error("An exception occured during GraphQL execution : {e}")
        finally:
            logger.info("Closing the webdriver.")
            self.driver.quit()
        update_status("Graphql",graphql_status)
        return graphql_status
    
    def close_graphql(self):
        """
        Method name: close_graphql
        Description: Closes the browser after execution
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Completed execution of GraphQL BVT==========================================\n\n")
        self.driver.quit()

if __name__ == "__main__":
    graphql = GraphQLTester()
    graphql.run_test()
    graphql.close_graphql()
