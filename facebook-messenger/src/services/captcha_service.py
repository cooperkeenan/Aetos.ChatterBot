# src/services/captcha_service.py
"""
Simplified captcha service - Handles basic reCAPTCHA checkboxes
Follows Single Responsibility Principle
"""

import time
import random
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from core.config_service import ConfigService
from services.browser_service import BrowserService


class SimpleCaptchaService:
    """
    Handles simple reCAPTCHA checkbox interactions
    Single Responsibility: Basic captcha detection and clicking
    """
    
    def __init__(self, config: ConfigService, browser: BrowserService):
        self.config = config
        self.browser = browser
        self.enabled = config.captcha.enabled
    
    def check_and_solve(self) -> bool:
        """
        Check for captcha and attempt to solve
        Returns True if solved or no captcha found
        """
        if not self.enabled:
            return True
        
        driver = self.browser.get_driver()
        
        # Check if captcha present
        if not self._is_captcha_present(driver):
            return True
        
        print("[Captcha] Detected reCAPTCHA")
        self.browser.take_screenshot("captcha_detected")
        
        # Try to click checkbox
        if self._click_checkbox(driver):
            time.sleep(3)  # Wait for verification
            
            # Check if solved
            if self._is_solved(driver):
                print("[Captcha] ✅ Successfully solved")
                return True
            else:
                print("[Captcha] ⚠️ May require manual intervention")
                return False
        else:
            print("[Captcha] ❌ Could not find checkbox")
            return False
    
    def _is_captcha_present(self, driver) -> bool:
        """Check if reCAPTCHA is present on page"""
        try:
            # Check page source
            page_source = driver.page_source.lower()
            indicators = ["recaptcha", "i'm not a robot", "g-recaptcha"]
            
            if any(indicator in page_source for indicator in indicators):
                return True
            
            # Check for reCAPTCHA iframes
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            if iframes:
                return True
                
        except Exception:
            pass
        
        return False
    
    def _click_checkbox(self, driver) -> bool:
        """Find and click the reCAPTCHA checkbox"""
        # Try main page first
        if self._try_click_main_page(driver):
            return True
        
        # Try iframes
        if self._try_click_in_iframe(driver):
            return True
        
        return False
    
    def _try_click_main_page(self, driver) -> bool:
        """Try to click checkbox in main page"""
        selectors = [
            ".recaptcha-checkbox-border",
            ".recaptcha-checkbox",
            "#recaptcha-anchor",
            "div[role='checkbox']",
            "span[role='checkbox']"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        self._human_click(driver, element)
                        return True
            except Exception:
                continue
        
        return False
    
    def _try_click_in_iframe(self, driver) -> bool:
        """Try to click checkbox inside iframe"""
        original_frame = None
        
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "recaptcha" in src.lower():
                    try:
                        driver.switch_to.frame(iframe)
                        
                        if self._try_click_main_page(driver):
                            return True
                        
                    finally:
                        driver.switch_to.default_content()
                        
        except Exception as e:
            print(f"[Captcha] Error checking iframes: {e}")
            
        finally:
            # Ensure we're back in default content
            try:
                driver.switch_to.default_content()
            except:
                pass
        
        return False
    
    def _human_click(self, driver, element):
        """Click element with human-like behavior"""
        try:
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Use ActionChains for realistic movement
            actions = ActionChains(driver)
            
            # Add small random offset
            x_offset = random.randint(-2, 2)
            y_offset = random.randint(-2, 2)
            
            actions.move_to_element_with_offset(element, x_offset, y_offset)
            time.sleep(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            
            print("[Captcha] Clicked checkbox")
            
        except Exception as e:
            # Fallback to simple click
            try:
                element.click()
                print("[Captcha] Clicked checkbox (simple)")
            except:
                raise
    
    def _is_solved(self, driver) -> bool:
        """Check if captcha was solved"""
        # Check if we got redirected
        current_url = driver.current_url.lower()
        if "facebook.com/home" in current_url or "facebook.com/?" in current_url:
            return True
        
        # Check if captcha indicators are gone
        try:
            page_source = driver.page_source.lower()
            if "i'm not a robot" not in page_source:
                return True
        except:
            pass
        
        # Check for image challenges (means simple click wasn't enough)
        challenge_indicators = [
            ".rc-imageselect",
            "select all images",
            "click verify"
        ]
        
        page_source = driver.page_source.lower()
        if any(indicator in page_source for indicator in challenge_indicators):
            print("[Captcha] Complex challenge detected - manual intervention needed")
            return False
        
        return False