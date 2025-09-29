import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from utils.logger import logger

class ChromeDriverSingleton:
    _instance = None

    def __new__(cls):
        """
        Name: __new__
        Author: Dhanesh
        Desc: Launch Chrome driver in incognito mode
        Parameters:
        Returns:
            driver instance
        Raises:
            WebDriverException: If there is an issue launching the Chrome browser.
            TimeoutException: If the browser takes too long to start.
            Exception: A generic exception to handle unforeseen issues.
        """
        if cls._instance is None:
            try:
                print('Launching chrome...')
                logger.info('Launching chrome...')
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--incognito")
                chrome_options.add_argument('--ignore-certificate-errors')
                
                # Initialize the ChromeDriver instance
                cls._instance = webdriver.Chrome(options=chrome_options)
                cls._instance.maximize_window()
                cls._instance.implicitly_wait(10)
                print('Chrome browser launched successfully')
                logger.info('Chrome browser launched successfully')

            except WebDriverException as e:
                print(f"Error launching Chrome WebDriver: {e}")
                logger.info(f"Error launching Chrome WebDriver: {e}")
                raise

            except TimeoutException as e:
                print(f"Chrome WebDriver timed out: {e}")
                logger.info(f"Chrome WebDriver timed out: {e}")
                raise

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                logger.info(f"An unexpected error occurred: {e}")
                raise

        return cls._instance
    
    @classmethod
    def closeBrowser(cls):
        """
        Name: close
        Author: Dhanesh
        Desc: Close the current driver window
        Parameters:
        Returns:
            None
        Raises:
            WebDriverException: If there's an error closing the WebDriver window.
            Exception: If there's an unexpected error while closing.
        """
        if cls._instance is not None:
            try:
                print('Closing the current browser window...')
                logger.info('Closing the current browser window...')
                cls._instance.close()
                cls._instance = None
                print('Browser window closed successfully.')
                logger.info('Browser window closed successfully.')
            except WebDriverException as e:
                print(f"Error closing the WebDriver window: {e}")
                logger.info(f"Error closing the WebDriver window: {e}")
                raise 
            except Exception as e:
                print(f"An unexpected error occurred while closing the browser: {e}")
                logger.info(f"An unexpected error occurred while closing the browser: {e}")
                raise

    @classmethod
    def quitBrowser(cls):
        """
        Name: quit
        Author: Dhanesh
        Desc: Close all window instances
        Parameters:
        Returns:
            None
        Raises:
            WebDriverException: If there's an error quitting the WebDriver session.
            Exception: If there's an unexpected error while quitting.
        """
        if cls._instance is not None:
            try:
                print('Quitting the browser and closing all windows...')
                logger.info('Quitting the browser and closing all windows...')
                cls._instance.quit()
                cls._instance = None
                print('All browser windows closed successfully.')
                logger.info('All browser windows closed successfully.')
            except WebDriverException as e:
                print(f"Error quitting the WebDriver session: {e}")
                logger.info(f"Error quitting the WebDriver session: {e}")
                raise 
            except Exception as e:
                print(f"An unexpected error occurred while quitting the browser: {e}")
                logger.info(f"An unexpected error occurred while quitting the browser: {e}")
                raise
