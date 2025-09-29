from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from utils.logger import logger

class ClearChrome:
    def delete_data(self):
        """
        Method name: delete_data
        Description: Clears the cache and cookies from the chrome browser before a fresh run.
        Parameters:
            None
        Returns:
            None
        """
        logger.info("==========================================Starting clearing of Chrome cookies, cache and history==========================================")
        chrome_options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Loading chrome://settings/clearBrowserData...")
        self.driver.get('chrome://settings/clearBrowserData')
        self.driver.maximize_window()
        self.driver.implicitly_wait(2)
        root = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/settings-ui')))
        logger.info("Accessing shadow DOM elements step by step...")
        settings_main = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('#main')", root)
        logger.info("Accessed 'settings-main'.")
        settings_basic_page = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('settings-basic-page')", settings_main)
        logger.info("Accessed 'settings-basic-page'.")
        settings_privacy_page = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('settings-privacy-page')", settings_basic_page)
        logger.info("Accessed 'settings-privacy-page'.")
        settings_clear_browsing_data_dialog = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('settings-clear-browsing-data-dialog')", settings_privacy_page)
        logger.info("Accessed 'settings-clear-browsing-data-dialog'.")
        settings_dropdown_menu = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('settings-dropdown-menu')", settings_clear_browsing_data_dialog)
        logger.info("Accessed 'settings-dropdown-menu'.")
        logger.info("Selecting the desired time range for clearing data...")
        settings_time = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('#dropdownMenu option:nth-child(5)')", settings_dropdown_menu)
        if settings_time:
            logger.info("Time range dropdown option found. Clicking it...")
            settings_time.click()
        else:
            logger.info("Time range dropdown option not found!")
        time.sleep(2)
        logger.info("Locating the 'Clear data' button...")
        clear_data_button = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('#clearBrowsingDataConfirm')", settings_clear_browsing_data_dialog)
        logger.info(f"Clear data button: {clear_data_button}")
        if clear_data_button:
            logger.info("Clicking the 'Clear data' button...")
            clear_data_button.click()
        time.sleep(2)
        logger.info("Closing the Chrome driver...")
        self.driver.close()  
        logger.info("==========================================Completed clearing of Chrome cookies, cache and history==========================================\n\n")

if __name__ == "__main__":
    del_cache = ClearChrome()
    del_cache.delete_data()