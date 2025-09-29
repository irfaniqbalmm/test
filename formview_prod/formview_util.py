import subprocess
import os
import time
from cp4ba_proddeploy_automation.utils.logs import *
from formview_prod.formview_locators import *
from ruamel.yaml import YAML

log = DeploymentLogs(logname="formview_prod")
logger = log.logger

def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        log.logger.info(f"Command: {' '.join(command)}\nOutput:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        log.logger.error(f"Error running command: {' '.join(command)}\nError: {e.stderr}")
        raise SystemExit(f"Stopping script due to failed command: {' '.join(command)}")

def wait_for_seconds(wait_seconds=20):
    """Waits for a given time."""
    try:
        log.logger.info(f"Waiting for {wait_seconds} seconds...")
        time.sleep(wait_seconds)
        log.logger.info(f"Waited for {wait_seconds} seconds.")
    except Exception as e:
        log.logger.error(f"Failed to wait: {e}")
        raise SystemExit("Stopping script due to failure in wait_for_seconds()")

def wait_for_locator_visible(page, locator, timeout=30000):
    """Waits for a specific locator to be visible on the page."""
    try:
        log.logger.info(f"Waiting for the locator {locator} to be visible...")
        page.wait_for_selector(locator, state="visible", timeout=timeout)
        log.logger.info(f"Locator {locator} is now visible.")
    except Exception as e:
        log.logger.error(f"Failed to find the locator {locator} visible: {e}")
        raise SystemExit(f"Stopping script due to missing element: {locator}")
        
def wait_and_reload(page, wait_seconds=20):
    """Waits for a given time, reloads the page, and waits for network to be idle."""
    try:
        log.logger.info(f"Waiting for {wait_seconds} seconds before reload...")
        time.sleep(wait_seconds)
        page.reload()
        page.wait_for_load_state("networkidle")
        time.sleep(10)
        log.logger.info("Page reloaded and network is idle.")
    except Exception as e:
        log.logger.error(f"Failed to reload the page: {e}")
        raise SystemExit("Stopping script due to page reload failure.")

def update_operator_group_yaml(file_path, project_name):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    try:
        with open(file_path, "r") as file:
            data = yaml.load(file)
        log.logger.info("Opened the operator_group YAML")

        # Modify values
        data["metadata"]["namespace"] = project_name
        data["spec"]["targetNamespaces"] = [project_name]

        with open(file_path, "w") as file:
            yaml.dump(data, file)

        log.logger.info(f"operator_group YAML file updated successfully with project name: {project_name}")

    except Exception as e:
        log.logger.error(f"Failed to update operator_group YAML file: {e}")
        raise SystemExit("Stopping script due to operator_group YAML update failure.")
        

def create_configmap_yaml(file_path, project_name):
    yaml = YAML()
    yaml.default_flow_style = False  # Make YAML readable

    configmap_content = {
        "kind": "ConfigMap",
        "apiVersion": "v1",
        "metadata": {
            "name": "ibm-cp4ba-common-config",
            "namespace": project_name
        },
        "data": {
            "operators_namespace": project_name,
            "services_namespace": project_name
        }
    }

    try:
        with open(file_path, "w") as file:
            yaml.dump(configmap_content, file)
        log.logger.info(f"ConfigMap YAML file created successfully with project name: {project_name}")
    except Exception as e:
        log.logger.error(f"Failed to create ConfigMap YAML file: {e}")
        raise SystemExit("Stopping script due to ConfigMap YAML creation failure.")
    

def safe_click(page, selector, timeout=5000):
    """Waits for an element and clicks it if found, otherwise skips."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.locator(selector).click()
        log.logger.info(f"Clicked element: {selector}")
    except Exception as e:
        log.logger.warning(f"Element not found or not clickable: {selector}, skipping... Error: {e}")
        raise SystemExit(f"Stopping script due to missing element: {selector}")

def click_if_found(page, selector, timeout=5000):
    """
    Attempts to click an element if it exists.
    Logs a warning if the element is missing but continues execution.
    """
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.locator(selector).click()
        log.logger.info(f"Clicked element: {selector}")
    except Exception as e:
        log.logger.warning(f"Element not found or not clickable: {selector}. Continuing... Error: {e}")
    
def safe_fill(page, selector, text, timeout=5000):
    """Waits for an input element and fills it if found, otherwise skips."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.locator(selector).fill(text)
        log.logger.info(f"Filled '{text}' in element: {selector}")
    except Exception as e:
        log.logger.warning(f"Element not found or not fillable: {selector}, skipping fill... Error: {e}")
        raise SystemExit(f"Stopping script due to missing element: {selector}")

def safe_fill_with_clear(page, selector, value, timeout=5000):
    """Waits for an input element, clears it, and fills it if found, otherwise skips."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.locator(selector).fill("")  # Clear existing value
        page.locator(selector).fill(value)
        log.logger.info(f"Filled '{value}' in element: {selector}")
    except Exception as e:
        log.logger.warning(f"Element not found or not fillable: {selector}, skipping fill... Error: {e}")
        raise SystemExit(f"Stopping script due to missing element: {selector}")

def click_and_fill(page, selector, text, timeout=5000):
    """Clicks an input element and fills it with text if found, otherwise skips."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.locator(selector).click()
        page.locator(selector).fill(text)
        log.logger.info(f"Clicked and filled '{text}' in element: {selector}")
    except Exception as e:
        log.logger.warning(f"Element not found or not clickable/fillable: {selector}, skipping... Error: {e}")
        raise SystemExit(f"Stopping script due to missing element: {selector}")
    
def radio_button_click(page, selector, timeout=5000):
    """Checks and clicks a radio button if it's not already selected."""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        radio_button = page.locator(selector)
        if not radio_button.is_checked():
            radio_button.click()
            log.logger.info(f"Selected radio button: {selector}")
        else:
            log.logger.info(f"Radio button already selected: {selector}")
    except Exception as e:
        log.logger.warning(f"Radio button not found or not clickable: {selector}, skipping... Error: {e}")
        raise SystemExit(f"Stopping script due to missing element: {selector}")
    
def safe_scroll(page, selector, timeout=0):
    """
    Scrolls until the element is visible.
    If timeout=0, it waits indefinitely (relies on Playwright's auto-wait).
    """
    try:
        element = page.locator(selector)
        element.scroll_into_view_if_needed()
        element.wait_for(state="visible", timeout=timeout)
        log.logger.info(f"Scrolled into view: {selector}")
        return True
    except Exception as e:
        log.logger.warning(f"Element not found or not scrollable: {selector}, skipping scroll... Error: {e}")
        raise SystemExit(f"Stopping script due to missing element: {selector}")

def set_checkbox_state(page, input_selector: str, toggle_selector: str = None, should_be_checked: bool = True):
    """
    Ensures any checkbox/switch is in the desired state.

    :param page: Playwright Page object
    :param input_selector: CSS selector for the underlying <input type="checkbox">
    :param toggle_selector: (Optional) CSS selector for the visible toggle (if input is hidden/styled, e.g. PatternFly switch)
    :param should_be_checked: True to turn ON, False to turn OFF
    """
    checkbox = page.locator(input_selector)

    # Get current state
    is_checked = checkbox.is_checked()

    if should_be_checked and not is_checked:
        if toggle_selector:
            page.locator(toggle_selector).click()
        else:
            checkbox.check()
        checkbox.wait_for(state="attached")  # ensure DOM is stable
        page.wait_for_function(
            f'document.querySelector("{input_selector}").checked === true'
        )
    elif not should_be_checked and is_checked:
        if toggle_selector:
            page.locator(toggle_selector).click()
        else:
            checkbox.uncheck()
        checkbox.wait_for(state="attached")
        page.wait_for_function(
            f'document.querySelector("{input_selector}").checked === false'
        )
    # else already in desired state → no action


def force_element_visibility(page, locator, max_attempts=5):
    """
    Force page conditions to make element appear using different strategies
    
    Args:
        page: Playwright page object
        locator: Element locator to find
        max_attempts: Maximum number of attempts (default: 5)
    
    Returns:
        bool: True if element found, False otherwise
    """
    attempts = 0
    
    while attempts < max_attempts:
        try:
            log.logger.info(f"Attempting to find element, attempt {attempts + 1}")
            
            # Apply different strategies based on attempt number
            if attempts == 0:
                # Wait for network to be idle
                page.wait_for_load_state("networkidle", timeout=10000)
                
            elif attempts == 1:
                # Scroll to top then down
                page.evaluate("window.scrollTo(0, 0)")
                wait_for_seconds(2)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                
            elif attempts == 2:
                # Try focusing on form elements
                page.evaluate("document.querySelector('form')?.focus()")
                
            elif attempts == 3:
                # Try clicking somewhere to trigger UI updates
                try:
                    page.click("body")
                    wait_for_seconds(1)
                except:
                    pass
                    
            elif attempts == 4:
                # Last resort - wait longer
                wait_for_seconds(10)
            
            # Check if element is now available
            if page.locator(locator).count() > 0:
                log.logger.info(f"Element found on attempt {attempts + 1}")
                return True
            else:
                log.logger.warning(f"Element not found on attempt {attempts + 1}")
                
        except Exception as attempt_error:
            log.logger.warning(f"Attempt {attempts + 1} failed: {attempt_error}")
            
        attempts += 1
        wait_for_seconds(3)
    
    # All attempts failed
    log.logger.error(f"Element not found after {max_attempts} attempts")
    return False
