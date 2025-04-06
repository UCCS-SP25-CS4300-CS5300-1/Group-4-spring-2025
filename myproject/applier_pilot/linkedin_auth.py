from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logger = logging.getLogger(__name__)

def setup_browser():
    """Set up and return a configured Chrome browser instance."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return browser

def login_to_linkedin(username, password, browser=None):
    """
    Attempt to log in to LinkedIn with the given credentials.
    
    Args:
        username (str): LinkedIn username/email
        password (str): LinkedIn password
        browser (webdriver.Chrome, optional): Existing browser instance. If None, creates new one.
        
    Returns:
        tuple: (success: bool, message: str, browser: webdriver.Chrome)
        
    The browser is returned regardless of login success to allow for debugging/inspection.
    """
    try:
        if browser is None:
            browser = setup_browser()
        
        wait = WebDriverWait(browser, 30)
        
        browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        
        user_field = browser.find_element(By.ID, "username")
        user_field.send_keys(username)
        user_field.send_keys(Keys.TAB)
        time.sleep(1)
        
        pw_field = browser.find_element(By.ID, "password")
        pw_field.send_keys(password)
        time.sleep(1)
        
        login_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        time.sleep(5) 
        
        if "checkpoint" in browser.current_url or "two-step-verification" in browser.current_url:
            logger.info("Two-factor authentication detected. Waiting for manual input...")
            
            try:
                # Wait for either the feed-tab-icon (success) or error message
                wait_2fa = WebDriverWait(browser, 60)
                wait_2fa.until(lambda driver: 
                    driver.find_elements(By.ID, "feed-tab-icon") or
                    driver.find_elements(By.CLASS_NAME, "alert-error") or
                    "feed" in driver.current_url  # Additional check for successful login
                )
                
                if browser.find_elements(By.CLASS_NAME, "alert-error"):
                    return False, "Invalid credentials", browser
                elif browser.find_elements(By.ID, "feed-tab-icon") or "feed" in browser.current_url:
                    return True, "Successfully logged in", browser
                else:
                    return False, "Two-factor authentication failed", browser
                    
            except TimeoutException:
                return False, "Two-factor authentication timed out", browser
            
        try:
            wait.until(lambda driver: 
                driver.find_elements(By.ID, "feed-tab-icon") or  
                driver.find_elements(By.CLASS_NAME, "alert-error") or  
                "feed" in driver.current_url )
            
            if browser.find_elements(By.CLASS_NAME, "alert-error"):
                return False, "Invalid credentials", browser
            
            return True, "Successfully logged in", browser
            
        except TimeoutException:
            return False, "Could not verify login status", browser
            
    except Exception as e:
        return False, f"Login error: {str(e)}", browser 