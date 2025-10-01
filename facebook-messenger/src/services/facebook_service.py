# src/services/facebook_service.py
"""
Facebook service - Handles Facebook-specific operations
Follows Single Responsibility and Open/Closed principles
"""

import time
import random
import re
from typing import Optional, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from core.config_service import ConfigService
from services.browser_service import BrowserService
from services.session_service import SessionService
from services.captcha_service import SimpleCaptchaService


class FacebookService:
    """
    Handles Facebook-specific operations
    Single Responsibility: Facebook interaction logic
    """
    
    def __init__(self, config: ConfigService, browser: BrowserService, 
                 session: SessionService, captcha: Optional[SimpleCaptchaService] = None):
        self.config = config
        self.browser = browser
        self.session = session
        self.captcha = captcha
        self.driver = None
    
    def login(self) -> bool:
        """
        Perform Facebook login and set location
        Returns True if successful
        """
        if not self.config.facebook.username or not self.config.facebook.password:
            print("[Facebook] Missing credentials")
            return False
        
        print(f"[Facebook] Logging in as {self.config.facebook.username}")
        
        # Get driver
        self.driver = self.browser.get_driver()
        wait = self.browser.wait()
        
        try:
            # Navigate to login page
            print("[Facebook] Navigating to login page...")
            self.driver.get(self.config.facebook.login_url)
            self._human_delay(2, 4)
            
            # Check for captcha before login
            if self.captcha:
                self.captcha.check_and_solve()
            
            # Find and fill email field
            email_input = self._find_email_input(wait)
            if not email_input:
                print("[Facebook] Could not find email input")
                self.browser.take_screenshot("login_no_email_field")
                return False
            
            self._type_slowly(email_input, self.config.facebook.username)
            self._human_delay()
            
            # Find and fill password field
            password_input = self._find_password_input()
            if not password_input:
                print("[Facebook] Could not find password input")
                return False
                
            self._type_slowly(password_input, self.config.facebook.password)
            self._human_delay()
            
            # Check for captcha before submitting
            if self.captcha:
                self.captcha.check_and_solve()
            
            # Submit login
            if not self._submit_login():
                print("[Facebook] Failed to submit login")
                return False
            
            self._human_delay(3, 5)
            
            # Check for captcha after login
            if self.captcha:
                self.captcha.check_and_solve()
            
            # Handle 2FA if needed
            self._handle_2fa(wait)
            
            # Check if login successful
            if self._is_logged_in(wait):
                print("[Facebook] ✅ Login successful!")
                
                # Check and fix location
                print("[Facebook] 🌍 Checking location settings...")
                location_fixed = self.check_and_fix_location()
                
                if location_fixed:
                    print("[Facebook] ✅ Location set to UK")
                else:
                    print("[Facebook] ⚠️ Could not verify UK location - marketplace may show US results")
                
                # Save cookies
                cookies = self.driver.get_cookies()
                self.session.save_cookies(cookies)
                
                self.browser.take_screenshot("login_success")
                return True
            else:
                print("[Facebook] ❌ Login failed")
                self.browser.take_screenshot("login_failed")
                return False
                
        except Exception as e:
            print(f"[Facebook] Login error: {e}")
            self.browser.take_screenshot("login_error")
            return False
    
    def check_and_fix_location(self) -> bool:
        """Check if Facebook location is set to UK and fix if needed"""
        try:
            print("[Facebook] Checking location settings...")
            
            # First, check marketplace to see current location
            self.driver.get("https://www.facebook.com/marketplace")
            self._human_delay(3, 5)
            
            page_source = self.driver.page_source.lower()
            
            # Check for currency and location indicators
            has_usd = '$' in page_source and page_source.count('$') > page_source.count('£')
            has_gbp = '£' in page_source
            has_rebel = 'rebel' in page_source
            has_uk_locations = any(loc in page_source for loc in ['london', 'manchester', 'birmingham', 'edinburgh', 'united kingdom'])
            has_us_locations = any(loc in page_source for loc in ['new york', 'california', 'texas', 'florida', 'united states'])
            
            print(f"[Facebook] Location indicators:")
            print(f"   💰 USD ($): {has_usd}")
            print(f"   💰 GBP (£): {has_gbp}")
            print(f"   📷 Rebel models: {has_rebel}")
            print(f"   🇬🇧 UK locations: {has_uk_locations}")
            print(f"   🇺🇸 US locations: {has_us_locations}")
            
            # If clearly in US, try to change
            if (has_usd or has_us_locations) and not (has_gbp and has_uk_locations):
                print("[Facebook] ⚠️ Detected US location, attempting to change to UK...")
                return self._change_location_to_uk()
            elif has_gbp or has_uk_locations:
                print("[Facebook] ✅ UK location detected")
                return True
            else:
                print("[Facebook] ⚠️ Location unclear, attempting to set UK...")
                return self._change_location_to_uk()
                
        except Exception as e:
            print(f"[Facebook] Error checking location: {e}")
            return False
    
    def _change_location_to_uk(self) -> bool:
        """Attempt to change Facebook location to UK"""
        try:
            print("[Facebook] Trying to change location via Marketplace...")
            self.driver.get("https://www.facebook.com/marketplace")
            self._human_delay(3, 5)
            
            # Look for location selector/filter
            location_selectors = [
                "[aria-label*='location' i]",
                "[data-testid*='location']",
                "input[placeholder*='location' i]",
                "button[aria-label*='Change location' i]",
                "[aria-label*='filters' i]",
                "span:contains('Location')",
                "div:contains('Location')"
            ]
            
            for selector in location_selectors:
                try:
                    # Handle :contains selectors differently
                    if ':contains(' in selector:
                        text = selector.split(':contains(')[1].rstrip(')')
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), {text})]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                print(f"[Facebook] Found location element, clicking...")
                                element.click()
                                self._human_delay(2, 3)
                                
                                # Try to find location input field
                                location_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[placeholder*='location' i], input[aria-label*='location' i]")
                                
                                for location_input in location_inputs:
                                    if location_input.is_displayed():
                                        print("[Facebook] Found location input, setting to London...")
                                        location_input.clear()
                                        self._type_slowly(location_input, "London, United Kingdom")
                                        self._human_delay(2, 3)
                                        
                                        # Press Enter or look for suggestions
                                        location_input.send_keys(Keys.RETURN)
                                        self._human_delay(3, 5)
                                        
                                        # Check if location changed
                                        if self._verify_uk_location():
                                            print("[Facebook] ✅ Successfully changed to UK location")
                                            return True
                                        
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
            
            # Try alternative method - look for any text input and see if we can set location
            print("[Facebook] Trying alternative location setting...")
            return self._try_search_location_method()
            
        except Exception as e:
            print(f"[Facebook] Error changing location: {e}")
            return False
    
    def _try_search_location_method(self) -> bool:
        """Try setting location through search or URL parameters"""
        try:
            # Method 1: Try URL with location parameter
            uk_urls = [
                "https://www.facebook.com/marketplace/london",
                "https://www.facebook.com/marketplace/category/cameras-camcorders?lat=51.5074&lon=0.1278",  # London coordinates
                "https://www.facebook.com/marketplace/search/?query=camera&exact=false&lat=51.5074&lon=0.1278"
            ]
            
            for url in uk_urls:
                try:
                    print(f"[Facebook] Trying UK URL: {url}")
                    self.driver.get(url)
                    self._human_delay(3, 5)
                    
                    if self._verify_uk_location():
                        print("[Facebook] ✅ URL method worked!")
                        return True
                        
                except Exception as e:
                    continue
            
            # Method 2: Try setting location through profile settings
            return self._change_location_via_settings()
            
        except Exception as e:
            print(f"[Facebook] Alternative location method failed: {e}")
            return False
    
    def _change_location_via_settings(self) -> bool:
        """Try to change location via account settings"""
        try:
            print("[Facebook] Trying location change via settings...")
            
            # Go to location settings
            settings_urls = [
                "https://www.facebook.com/settings/?tab=location",
                "https://www.facebook.com/settings/?tab=account",
                "https://www.facebook.com/settings"
            ]
            
            for url in settings_urls:
                try:
                    self.driver.get(url)
                    self._human_delay(3, 5)
                    
                    # Look for location/region related settings
                    location_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'location') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'region') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'country')]")
                    
                    for element in location_elements:
                        try:
                            if element.is_displayed():
                                print("[Facebook] Found location setting, clicking...")
                                element.click()
                                self._human_delay(2, 3)
                                
                                # Look for UK options
                                uk_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'United Kingdom') or contains(text(), 'UK') or contains(text(), 'England') or contains(text(), 'London')]")
                                
                                for uk_element in uk_elements:
                                    if uk_element.is_displayed():
                                        print("[Facebook] Found UK option, selecting...")
                                        uk_element.click()
                                        self._human_delay(2, 3)
                                        
                                        # Save if possible
                                        save_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Save') or contains(text(), 'Update') or contains(text(), 'Apply')]")
                                        for save_element in save_elements:
                                            if save_element.is_displayed():
                                                save_element.click()
                                                self._human_delay(3, 5)
                                                return True
                                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            print(f"[Facebook] Settings location change failed: {e}")
            return False
    
    def _verify_uk_location(self) -> bool:
        """Verify that we're now in UK location"""
        try:
            # Refresh marketplace and check indicators
            self.driver.get("https://www.facebook.com/marketplace")
            self._human_delay(3, 5)
            
            page_source = self.driver.page_source.lower()
            
            # Check for UK indicators
            has_gbp = '£' in page_source
            has_uk_locations = any(loc in page_source for loc in ['london', 'manchester', 'birmingham', 'edinburgh', 'united kingdom'])
            has_fewer_rebels = page_source.count('rebel') < 5  # Should see fewer US-style model names
            
            # Check URL for UK indicators
            current_url = self.driver.current_url.lower()
            has_uk_in_url = any(indicator in current_url for indicator in ['london', 'uk', 'gb'])
            
            uk_score = sum([has_gbp, has_uk_locations, has_fewer_rebels, has_uk_in_url])
            
            print(f"[Facebook] UK verification score: {uk_score}/4")
            print(f"   💰 GBP currency: {has_gbp}")
            print(f"   🇬🇧 UK locations: {has_uk_locations}")
            print(f"   📷 Fewer rebels: {has_fewer_rebels}")
            print(f"   🔗 UK in URL: {has_uk_in_url}")
            
            return uk_score >= 2  # Need at least 2 indicators
            
        except Exception as e:
            print(f"[Facebook] Error verifying UK location: {e}")
            return False
    
    def debug_current_location(self) -> None:
        """Debug what location Facebook thinks we're in"""
        try:
            print("\n🌍 LOCATION DEBUG")
            print("="*50)
            
            # Go to marketplace
            self.driver.get("https://www.facebook.com/marketplace")
            self._human_delay(3, 5)
            
            # Check page source for location indicators
            page_source = self.driver.page_source
            
            # Look for currency symbols
            dollar_count = page_source.count('$')
            pound_count = page_source.count('£')
            
            print(f"💰 Currency Analysis:")
            print(f"   $ symbols: {dollar_count}")
            print(f"   £ symbols: {pound_count}")
            
            if dollar_count > pound_count:
                print("   🇺🇸 Likely USD/American")
            elif pound_count > 0:
                print("   🇬🇧 Likely GBP/British")
            else:
                print("   ❓ Currency unclear")
            
            # Look for location text
            location_patterns = [
                (r'(United States|USA|America)', '🇺🇸'),
                (r'(United Kingdom|UK|Britain|England)', '🇬🇧'),
                (r'(London|Manchester|Birmingham|Edinburgh)', '🇬🇧'),
                (r'(New York|California|Texas|Florida)', '🇺🇸')
            ]
            
            print(f"\n📍 Location References:")
            for pattern, flag in location_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    print(f"   {flag} {pattern.split('|')[0]}: {len(matches)} references")
            
            # Check camera naming conventions
            rebel_count = page_source.lower().count('rebel')
            d_number_count = len(re.findall(r'\b\d+d\b', page_source.lower()))
            
            print(f"\n📷 Camera Naming Analysis:")
            print(f"   'Rebel' models: {rebel_count} (US naming)")
            print(f"   'XXXd' models: {d_number_count} (International naming)")
            
            if rebel_count > d_number_count:
                print("   🇺🇸 Likely US camera market")
            elif d_number_count > rebel_count:
                print("   🌍 Likely International camera market")
            
            # Check URL
            current_url = self.driver.current_url
            print(f"\n🔗 Current URL: {current_url}")
            
            print("="*50)
            
        except Exception as e:
            print(f"[Facebook] Debug error: {e}")
    
    def _find_email_input(self, wait):
        """Find email/username input field"""
        selectors = [
            "#email",
            "input[name='email']",
            "input[type='email']",
            "input[placeholder*='email' i]",
            "#m_login_email",
            "input[name='login']",
            "input[autocomplete='username']",
            "input[autocomplete='email']"
        ]
        
        for selector in selectors:
            try:
                element = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"[Facebook] Found email field: {selector}")
                return element
            except TimeoutException:
                continue
        
        return None
    
    def _find_password_input(self):
        """Find password input field"""
        selectors = [
            "#pass",
            "input[name='pass']",
            "input[type='password']",
            "input[placeholder*='password' i]",
            "#m_login_password",
            "input[autocomplete='current-password']"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    print(f"[Facebook] Found password field: {selector}")
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _submit_login(self):
        """Submit the login form"""
        submit_selectors = [
            "#loginbutton",
            "button[name='login']",
            "button[type='submit']",
            "input[type='submit']",
            "button[data-testid='royal_login_button']"
        ]
        
        for selector in submit_selectors:
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                if button.is_displayed():
                    print(f"[Facebook] Clicking login button: {selector}")
                    button.click()
                    return True
            except NoSuchElementException:
                continue
        
        # Try form submission as fallback
        try:
            self.driver.find_element(By.CSS_SELECTOR, "form").submit()
            print("[Facebook] Submitted form directly")
            return True
        except:
            return False
    
    def _handle_2fa(self, wait):
        """Handle 2FA if required"""
        try:
            # Check for 2FA input
            twofa_selectors = [
                "input[name='approvals_code']",
                "input[placeholder*='security code' i]",
                "input[placeholder*='code' i]"
            ]
            
            for selector in twofa_selectors:
                try:
                    short_wait = WebDriverWait(self.driver, 5)
                    twofa_input = short_wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    if twofa_input:
                        print("[Facebook] 2FA required - please enter code")
                        # In production, you'd integrate with your 2FA system
                        # For now, this is a placeholder
                        return
                        
                except TimeoutException:
                    continue
                    
        except Exception:
            pass  # No 2FA required

    def test_marketplace_access(self) -> bool:
        """Navigate to marketplace and take screenshot"""
        if not self.driver:
            self.driver = self.browser.get_driver()
        
        try:
            print("[Facebook] Navigating to marketplace...")
            self.driver.get("https://www.facebook.com/marketplace")
            
            # Wait a bit for page to load
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"[Facebook] Marketplace URL: {current_url}")
            
            # Take screenshot
            self.browser.take_screenshot("marketplace_test")
            
            # Debug location while we're here
            self.debug_current_location()
            
            # Check if we can access marketplace
            page_source = self.driver.page_source.lower()
            if "marketplace" in page_source or "buy" in page_source:
                print("[Facebook] ✅ Marketplace accessible")
                return True
            else:
                print("[Facebook] ❌ Marketplace not accessible")
                return False
                
        except Exception as e:
            print(f"[Facebook] Marketplace error: {e}")
            self.browser.take_screenshot("marketplace_error")
            return False
    
    def _is_logged_in(self, wait) -> bool:
        """Check if login was successful"""
        # Check URL
        current_url = self.driver.current_url.lower()
        if any(path in current_url for path in ['facebook.com/?', 'facebook.com/home']):
            return True
        
        # Check for logged-in elements
        logged_in_selectors = [
            "[aria-label='Home']",
            "[data-testid='blue_bar_profile']",
            "#userNavigationLabel",
            ".fb_logo",
            "[role='navigation']"
        ]
        
        for selector in logged_in_selectors:
            try:
                short_wait = WebDriverWait(self.driver, 5)
                short_wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return True
            except TimeoutException:
                continue
        
        return False
    
    def restore_session(self) -> bool:
        """
        Restore session from saved cookies
        Returns True if session is valid
        """
        cookies = self.session.load_cookies()
        if not cookies:
            return False
        
        if not self.session.validate_cookies(cookies):
            return False
        
        # Get driver and load cookies
        self.driver = self.browser.get_driver()
        
        # Navigate to Facebook first
        self.driver.get("https://www.facebook.com")
        
        # Clear existing cookies
        self.driver.delete_all_cookies()
        
        # Add saved cookies
        for cookie in cookies:
            try:
                # Remove expiry if it's causing issues
                if 'expiry' in cookie and cookie['expiry'] < time.time():
                    cookie.pop('expiry', None)
                
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"[Facebook] Failed to add cookie {cookie.get('name')}: {e}")
        
        # Refresh to apply cookies
        self.driver.refresh()
        self._human_delay(2, 3)
        
        # Check if logged in
        wait = self.browser.wait()
        if self._is_logged_in(wait):
            print("[Facebook] ✅ Session restored successfully")
            
            # Check location after restoring session
            self.check_and_fix_location()
            
            return True
        else:
            print("[Facebook] ❌ Session invalid")
            return False
    
    def _type_slowly(self, element, text: str):
        """Type text slowly to appear human"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _human_delay(self, min_seconds: float = None, max_seconds: float = None):
        """Add human-like delay"""
        if min_seconds is None:
            min_seconds = self.config._raw_config.get('scraping', {}).get('human_delays', {}).get('min', 1)
        if max_seconds is None:
            max_seconds = self.config._raw_config.get('scraping', {}).get('human_delays', {}).get('max', 3)
        
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)