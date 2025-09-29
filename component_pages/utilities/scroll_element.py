import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from component_sanity_tests.exceptions.iccsap_exception import ICCSAPSanityTestException
from utils.logger import logger

def find_element_in_scroller(driver, scrollable_element, target_element, product=None):
    try:
        element = None
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")
        scroll_position = 0
        scroll_step = 300
        max_scroll_attempts = 10
        logger.info("Waiting for the presence of scrollable div.")
        scrollable_div = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, scrollable_element)))
        logger.info("Scrollable div is present.")
        for _ in range(max_scroll_attempts):
            try:
                # Try to locate the element after each scroll
                logger.info(f"Waiting for the presence of element: {target_element}.")
                element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, target_element)))
                logger.info(f"Found element: {target_element}.")
                break  
            except TimeoutException:
                logger.error("A TimeoutException has occured.")
                scroll_position += scroll_step
                driver.execute_script("arguments[0].scrollTop = arguments[1];", scrollable_div, scroll_position)
        else:
            logger.warning(f"Element {target_element} not found after scrolling.")
    except Exception as e:
        if product == "ICCSAP":
            raise ICCSAPSanityTestException(f"Failed while trying to locate element: {target_element} in the scroller.", cause=e) from e
    return element   
