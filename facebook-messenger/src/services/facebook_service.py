"""Facebook service - Session management only"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from ..core.config_service import ConfigService
from .browser_service import BrowserService
from .session_service import SessionService


class FacebookService:
    """Handles Facebook session restoration"""
    
    def __init__(self, config: ConfigService, browser: BrowserService, session: SessionService):
        self.config = config
        self.browser = browser
        self.session = session
        self.driver = None
    
    def restore_session(self) -> bool:
        """Restore session from saved cookies"""
        cookies = self.session.load_cookies()
        if not cookies or not self.session.validate_cookies(cookies):
            return False
        
        self.driver = self.browser.get_driver()
        self.driver.get("https://www.facebook.com")
        self.driver.delete_all_cookies()
        
        for cookie in cookies:
            try:
                if 'expiry' in cookie and cookie['expiry'] < time.time():
                    cookie.pop('expiry', None)
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"[Facebook] Failed to add cookie {cookie.get('name')}: {e}")
        
        self.driver.refresh()
        self._human_delay(2, 3)
        
        if self._is_logged_in():
            print("[Facebook] Session restored successfully")
            return True
        
        print("[Facebook] Session invalid")
        return False
    
    def _is_logged_in(self) -> bool:
        """Check if logged in"""
        current_url = self.driver.current_url.lower()
        if any(path in current_url for path in ['facebook.com/?', 'facebook.com/home']):
            return True
        
        selectors = ["[aria-label='Home']", "[role='navigation']"]
        for selector in selectors:
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, selector)
                )
                return True
            except TimeoutException:
                continue
        
        return False
    
    def _human_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Add human-like delay"""
        time.sleep(random.uniform(min_seconds, max_seconds))