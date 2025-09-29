from utils.logger import logger

from selenium.common.exceptions import WebDriverException

class DriverNotInitializedException(Exception):
    """Raised when trying to use driver before initialization."""
    pass

class BrowserManager:
    def __init__(self, driver):
        """
        Method name: __init__
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Method Description: Initialises the BrowserManager class.
        Parameters: 
            driver: The driver instance
        """ 
        self.driver = driver

    def open_url(self, url):
        """
        Method name: open_url
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Method Description: Loads the given url in the browser.
        Parameters: 
            url: URL to be loaded.
        Returns: None
        Raises:
            DriverNotInitializedException: If driver is closed before intialising.
        """ 
        if not self.driver:
            raise DriverNotInitializedException("Cannot open URL: driver is not initialized.")
        self.driver.get(url)

    def close_browser(self):
        """
        Method name: close_browser
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Method Description: Closes the current browser window. The WebDriver session will remain active if other windows are open.
        Parameters: None
        Returns: None
        Raises:
            DriverNotInitializedException: If driver is closed before intialising.
            WebDriverException: If there is an error while closing the browser.
        """ 
        if not self.driver:
            raise DriverNotInitializedException("Cannot close browser: driver is not initialized.")
        try:
            self.driver.close()
            logger.info("Closed current browser window.")
        except WebDriverException as e:
            raise RuntimeError(f"Error while closing browser window: {str(e)}")


    def quit_browser(self):
        """
        Method name: quit_browser
        Author: Anisha Suresh (anisha-suresh@ibm.com)
        Method Description:  Closes all browser windows and quits the WebDriver session.
        Parameters: None
        Returns: None
        Raises:
            DriverNotInitializedException: If driver is closed before intialising.
            WebDriverException: If there is an error while closing the browser.
        """ 
        if not self.driver:
            raise DriverNotInitializedException("Cannot quit browser: driver is not initialized.")
        try:
            self.driver.quit()
            logger.info("Quit the browser and ended session.")
        except WebDriverException as e:
            raise RuntimeError(f"Error while quitting browser: {str(e)}")
