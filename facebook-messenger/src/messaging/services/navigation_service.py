# src/messaging/services/navigation_service.py
"""
Navigation service for Facebook Marketplace messaging
Handles link navigation, login, and message flow
"""

import time
import random
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ...services.browser_service import BrowserService
from ...services.facebook_service import FacebookService
from ..domain.interfaces import INavigationService
from ..domain.models import NavigationResult


class NavigationService(INavigationService):
    """
    Handles Facebook marketplace navigation and messaging flow
    """
    
    def __init__(self, browser: BrowserService, facebook: FacebookService):
        self.browser = browser
        self.facebook = facebook
        self.driver = None
    
    def navigate_to_listing(self, url: str) -> NavigationResult:
        """Navigate to marketplace listing"""
        print(f"[Navigation] 🎯 Navigating to: {url}")
        
        self.driver = self.browser.get_driver()
        
        try:
            self.driver.get(url)
            self._human_delay(3, 5)
            
            if self._is_listing_page_loaded():
                print("[Navigation] ✅ Listing page loaded")
                return NavigationResult(success=True, url=url)
            else:
                print("[Navigation] ❌ Failed to load listing")
                return NavigationResult(success=False, url=url, error="Page load failed")
                
        except Exception as e:
            print(f"[Navigation] 💥 Navigation error: {e}")
            return NavigationResult(success=False, url=url, error=str(e))
    
    def find_message_button(self) -> bool:
        """Find and click the message seller button"""
        if not self.driver:
            return False
        
        print("[Navigation] 🔍 Looking for message button...")
        
        # Facebook uses various selectors for message buttons
        message_selectors = [
            "[aria-label*='Message' i]",
            "div[role='button']:contains('Message')",
            "button:contains('Message')",
            "[data-testid*='message']",
            "div:contains('Message seller')",
            "a[href*='/messages/']"
        ]
        
        for selector in message_selectors:
            if self._try_click_message_button(selector):
                return True
        
        print("[Navigation] ❌ No message button found")
        return False
    
    def _try_click_message_button(self, selector: str) -> bool:
        """Try to click message button with given selector"""
        try:
            # Handle :contains pseudo-selector
            if ':contains(' in selector:
                text = selector.split(':contains(')[1].rstrip(')')
                elements = self.driver.find_elements(
                    By.XPATH, f"//*[contains(translate(text(), 'MESSAGE', 'message'), {text.lower()})]"
                )
            else:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    print(f"[Navigation] 🖱️ Clicking message button: {selector}")
                    self._human_click(element)
                    self._human_delay(2, 4)
                    return True
                    
        except Exception as e:
            print(f"[Navigation] ⚠️ Selector failed {selector}: {e}")
        
        return False
    
    def _is_listing_page_loaded(self) -> bool:
        """Check if marketplace listing page loaded correctly"""
        try:
            current_url = self.driver.current_url.lower()
            
            # Check URL contains marketplace/item
            if '/marketplace/item/' not in current_url:
                return False
            
            # Check for listing indicators
            indicators = [
                "[data-testid*='marketplace']",
                ".marketplace-listing",
                "[role='main']"
            ]
            
            for indicator in indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def _human_click(self, element):
        """Click element with human-like behavior"""
        try:
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Add small random offset
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            x_offset = random.randint(-2, 2)
            y_offset = random.randint(-2, 2)
            
            actions.move_to_element_with_offset(element, x_offset, y_offset)
            time.sleep(random.uniform(0.1, 0.3))
            actions.click()
            actions.perform()
            
        except Exception:
            # Fallback to simple click
            element.click()
    
    def _human_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)