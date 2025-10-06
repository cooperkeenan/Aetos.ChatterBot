# src/services/captcha_service.py
"""
Captcha service with 2Captcha API integration
"""

import time
import requests
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from ..core.config_service import ConfigService
from .browser_service import BrowserService


class SimpleCaptchaService:
    """Handles reCAPTCHA using 2Captcha service"""
    
    def __init__(self, config: ConfigService, browser: BrowserService):
        self.config = config
        self.browser = browser
        self.enabled = config.captcha.enabled
        self.api_key = config.captcha.api_key
        self.base_url = "http://2captcha.com"
    
    def check_and_solve(self) -> bool:
        """Check for captcha and solve using 2Captcha API"""
        if not self.enabled or not self.api_key:
            return True
        
        driver = self.browser.get_driver()
        
        if not self._is_captcha_present(driver):
            return True
        
        print("[Captcha] Detected reCAPTCHA, sending to 2Captcha...")
        self.browser.take_screenshot("captcha_detected")
        
        # Get site key
        site_key = self._get_site_key(driver)
        if not site_key:
            print("[Captcha] Could not find site key")
            return False
        
        # Get page URL
        page_url = driver.current_url
        
        # Solve with 2Captcha
        token = self._solve_with_2captcha(page_url, site_key)
        if not token:
            return False
        
        # Inject token
        if self._inject_token(driver, token):
            print("[Captcha] Successfully solved")
            return True
        
        return False
    
    def _is_captcha_present(self, driver) -> bool:
        """Check if reCAPTCHA is present"""
        try:
            page_source = driver.page_source.lower()
            return "recaptcha" in page_source or "g-recaptcha" in page_source
        except:
            return False
    
    def _get_site_key(self, driver) -> Optional[str]:
        """Extract reCAPTCHA site key from page"""
        try:
            # Try different methods to find site key
            
            # Method 1: data-sitekey attribute
            elements = driver.find_elements(By.CSS_SELECTOR, "[data-sitekey]")
            for elem in elements:
                key = elem.get_attribute("data-sitekey")
                if key:
                    return key
            
            # Method 2: iframe src
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if "k=" in src:
                    key = src.split("k=")[1].split("&")[0]
                    if key:
                        return key
            
            # Method 3: Page source search
            import re
            page_source = driver.page_source
            match = re.search(r'data-sitekey="([^"]+)"', page_source)
            if match:
                return match.group(1)
            
        except Exception as e:
            print(f"[Captcha] Error getting site key: {e}")
        
        return None
    
    def _solve_with_2captcha(self, page_url: str, site_key: str) -> Optional[str]:
        """Send captcha to 2Captcha and get solution"""
        try:
            # Submit captcha
            submit_url = f"{self.base_url}/in.php"
            params = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1
            }
            
            print(f"[Captcha] Submitting to 2Captcha...")
            response = requests.get(submit_url, params=params, timeout=30)
            result = response.json()
            
            if result.get("status") != 1:
                print(f"[Captcha] 2Captcha error: {result.get('request')}")
                return None
            
            captcha_id = result.get("request")
            print(f"[Captcha] Captcha ID: {captcha_id}, waiting for solution...")
            
            # Poll for result
            result_url = f"{self.base_url}/res.php"
            max_attempts = self.config.captcha.solve_timeout // 5
            
            for attempt in range(max_attempts):
                time.sleep(5)
                
                params = {
                    "key": self.api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
                
                response = requests.get(result_url, params=params, timeout=30)
                result = response.json()
                
                if result.get("status") == 1:
                    token = result.get("request")
                    print(f"[Captcha] Solved in {(attempt + 1) * 5} seconds")
                    return token
                
                if result.get("request") != "CAPCHA_NOT_READY":
                    print(f"[Captcha] Error: {result.get('request')}")
                    return None
            
            print("[Captcha] Timeout waiting for solution")
            return None
            
        except Exception as e:
            print(f"[Captcha] 2Captcha API error: {e}")
            return None
    
    def _inject_token(self, driver, token: str) -> bool:
        """Inject solved captcha token into page"""
        try:
            # Find textarea and inject token
            script = f"""
                var textarea = document.querySelector('[name="g-recaptcha-response"]');
                if (textarea) {{
                    textarea.innerHTML = '{token}';
                    textarea.value = '{token}';
                }}
            """
            driver.execute_script(script)
            
            # Trigger callback if exists
            callback_script = """
                var callback = ___grecaptcha_cfg.clients[0].callback;
                if (callback) callback();
            """
            try:
                driver.execute_script(callback_script)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"[Captcha] Error injecting token: {e}")
            return False