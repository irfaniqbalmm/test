import sys
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import logger
from inputs.locators import LocatorElements

class LdapLogin:
    def login(self, driver, route, username, password):
        """
        Method name: login
        Description: Login to the route loaded using the credentials passed and retries for maximum 3 times if fails
        Parameters:
            driver : (selenium.webdriver) An active Selenium WebDriver instance controlling the browser.
        route : (str) The URL route to login.
        username : (str) The username used for login.
        password : (str) The password used for login.

        Returns:
            login_succeeded : (bool) True if login is successful within 3 attempts, False otherwise.

        Raises :
            NoSuchElementException : if Enterprise LDAP option is not found.

        Notes:
        -----
        - It tries clicking a "Enterprise LDAP" button by class name first.
        - If that fails, it attempts to select "Enterprise LDAP" from a dropdown.
        """
        login_succeeded = False
        logger.info(f"Setted username/password to : {username}/{password}")
        n = 0
        while n < 3 :
            logger.info(f"Attempt : #{n+1}")
            try :
                try : 
                    logger.info("Trying to click on Enterprise LDAP option for login...")
                    driver.find_element(By.CLASS_NAME, LocatorElements.enterpriseLDAP).click()
                    logger.info("Successfully clicked on Enterprise LDAP option for login!")
                except NoSuchElementException:
                    logger.warning("NoSuchElementException is thrown.")
                    logger.info("Trying to select Enterprise LDAP option from dropdown for login...")
                    dropdown_element = driver.find_element(By.ID,"login_options")
                    select = Select(dropdown_element)
                    select.select_by_visible_text("Enterprise LDAP")
                    logger.info("Successfully selected Enterprise LDAP option from dropdown for login!")
                driver.find_element(By.ID, LocatorElements.acceUsername).send_keys(username)
                logger.info(f"Entered username : {username}")
                driver.find_element(By.ID, LocatorElements.accePassword).send_keys(password)
                logger.info(f"Entered password.")
                driver.find_element(By.NAME, LocatorElements.loginbtn).click()
                logger.info("Clicked on Login button !")
                WebDriverWait(driver,60).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                time.sleep(2)
                login_succeeded = True
                break
            except Exception as e:
                logger.error(f"An exception occured during logging in : {e}")
                n += 1
                logger.info("Loading a new blank window")
                driver.execute_script("window.open('','_blank');")
                logger.info("Switching to the new window")
                driver.switch_to.window(driver.window_handles[-1])
                logger.info(f"Getting the page : {route}")
                driver.get(route)
                continue
        return login_succeeded
