"""
Login flow handler with captcha and security code support
"""
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginHandler:
    """Handles Facebook login with multiple fallback strategies"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, 10)
    
    def handle_login_page(self):
        """
        Smart login handler that detects page state and acts accordingly
        Returns: ('login_fields', 'captcha', 'security_code', or 'unknown')
        """
        time.sleep(2)  # Let page stabilize
        
        # Check what's on the page
        if self._has_login_fields():
            return 'login_fields'
        elif self._has_captcha():
            return 'captcha'
        elif self._has_security_code():
            return 'security_code'
        else:
            return 'unknown'
    
    def _has_login_fields(self):
        """Check if login fields are present"""
        try:
            self.driver.find_element(By.CSS_SELECTOR, "#email")
            self.driver.find_element(By.CSS_SELECTOR, "#pass")
            return True
        except NoSuchElementException:
            return False
    
    def _has_captcha(self):
        """Check if captcha is present"""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "iframe[title*='reCAPTCHA']",
            ".g-recaptcha",
            "#captcha"
        ]
        for selector in captcha_selectors:
            try:
                self.driver.find_element(By.CSS_SELECTOR, selector)
                return True
            except NoSuchElementException:
                continue
        return False
    
    def _has_security_code(self):
        """Check if security code input is present"""
        code_selectors = [
            "input[name='approvals_code']",
            "input[id='approvals_code']",
            "input[placeholder*='code' i]"
        ]
        for selector in code_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        return False
    
    def wait_for_security_code(self, timeout=300):
        """
        Wait for user to manually enter security code
        Returns True if code was entered, False if timeout
        """
        print("\n" + "="*50)
        print("SECURITY CODE REQUIRED")
        print("Please enter the code sent to your device")
        print(f"Waiting up to {timeout} seconds...")
        print("="*50 + "\n")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if we've moved past the code page
            current_url = self.driver.current_url.lower()
            if 'checkpoint' not in current_url and 'login' not in current_url:
                print("Security code accepted!")
                return True
            
            time.sleep(2)
        
        print("Timeout waiting for security code")
        return False