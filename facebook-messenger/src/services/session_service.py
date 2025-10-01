# src/services/session_service.py
"""
Session service - Manages cookies and session persistence
Follows Single Responsibility Principle
"""

import os
import json
import pickle
import time
from typing import List, Dict, Optional, Any
from pathlib import Path

from ..core.config_service import ConfigService


class SessionService:
    """
    Manages browser sessions and cookies
    Single Responsibility: Session persistence and validation
    """
    
    def __init__(self, config: ConfigService):
        self.config = config
        self.cookie_file = os.path.join(config.paths.cookies_dir, "fb_cookies.pkl")
        self.json_cookie_file = os.path.join(config.paths.cookies_dir, "fb_cookies.json")
        self.laptop_cookie_file = "/app/laptop_cookies.json"
        self.session_info_file = os.path.join(config.paths.cookies_dir, "session_info.json")
    
    def load_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """
        Load cookies from available sources
        Priority: laptop cookies > saved cookies
        """
        # Try laptop cookies first
        laptop_cookies = self._load_laptop_cookies()
        if laptop_cookies:
            print(f"[Session] Using {len(laptop_cookies)} laptop cookies")
            return laptop_cookies
        
        # Try saved cookies
        saved_cookies = self._load_saved_cookies()
        if saved_cookies:
            print(f"[Session] Using {len(saved_cookies)} saved cookies")
            return saved_cookies
        
        print("[Session] No cookies available")
        return None
    
    def _load_laptop_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """Load cookies from laptop export"""
        try:
            if not os.path.exists(self.laptop_cookie_file):
                return None
                
            with open(self.laptop_cookie_file, 'r') as f:
                laptop_cookies = json.load(f)
            
            # Convert to Selenium format
            selenium_cookies = []
            for cookie in laptop_cookies:
                selenium_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                    "secure": cookie["secure"],
                    "httpOnly": cookie["httpOnly"]
                }
                
                # Add expiry if present
                if "expirationDate" in cookie:
                    selenium_cookie["expiry"] = int(cookie["expirationDate"])
                
                selenium_cookies.append(selenium_cookie)
            
            return selenium_cookies
            
        except Exception as e:
            print(f"[Session] Failed to load laptop cookies: {e}")
            return None
    
    def _load_saved_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """Load previously saved cookies"""
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                # Check expiration
                expired = self._check_expired_cookies(cookies)
                if expired:
                    print(f"[Session] Warning: {expired} cookies may be expired")
                
                return cookies
                
        except Exception as e:
            print(f"[Session] Failed to load saved cookies: {e}")
            return None
    
    def save_cookies(self, cookies: List[Dict[str, Any]]) -> bool:
        """Save cookies in multiple formats"""
        try:
            # Save as pickle
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            
            # Save as JSON
            with open(self.json_cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            # Save session info
            self._save_session_info()
            
            print(f"[Session] Saved {len(cookies)} cookies")
            return True
            
        except Exception as e:
            print(f"[Session] Failed to save cookies: {e}")
            return False
    
    def _check_expired_cookies(self, cookies: List[Dict[str, Any]]) -> int:
        """Count expired cookies"""
        current_time = time.time()
        expired = 0
        
        for cookie in cookies:
            if 'expiry' in cookie and cookie['expiry'] < current_time:
                expired += 1
        
        return expired
    
    def _save_session_info(self) -> None:
        """Save session metadata"""
        try:
            session_info = {
                "last_login": time.time(),
                "last_login_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                "session_age_hours": 0
            }
            
            with open(self.session_info_file, 'w') as f:
                json.dump(session_info, f, indent=2)
                
        except Exception as e:
            print(f"[Session] Failed to save session info: {e}")
    
    def get_session_age_hours(self) -> Optional[float]:
        """Get session age in hours"""
        try:
            if not os.path.exists(self.session_info_file):
                return None
                
            with open(self.session_info_file, 'r') as f:
                info = json.load(f)
            
            last_login = info.get('last_login', 0)
            age_hours = (time.time() - last_login) / 3600
            return age_hours
            
        except Exception:
            return None
    
    def should_refresh_session(self) -> bool:
        """Determine if session needs refresh"""
        age_hours = self.get_session_age_hours()
        
        if age_hours is None:
            print("[Session] No session history, refresh needed")
            return True
        
        refresh_threshold = self.config.facebook.session_refresh_hours
        if age_hours > refresh_threshold:
            print(f"[Session] Session is {age_hours:.1f} hours old, refresh needed")
            return True
        
        print(f"[Session] Session is {age_hours:.1f} hours old, still valid")
        return False
    
    def validate_cookies(self, cookies: List[Dict[str, Any]]) -> bool:
        """Validate if cookies have required fields"""
        if not cookies:
            return False
        
        # Check for essential Facebook cookies
        cookie_names = {cookie.get('name') for cookie in cookies}
        essential_cookies = {'c_user', 'xs'}
        
        missing = essential_cookies - cookie_names
        if missing:
            print(f"[Session] Missing essential cookies: {missing}")
            return False
        
        print("[Session] Cookies appear valid")
        return True
    
    def clear_session(self) -> None:
        """Clear all saved session data"""
        try:
            for file_path in [self.cookie_file, self.json_cookie_file, self.session_info_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"[Session] Removed {file_path}")
                    
        except Exception as e:
            print(f"[Session] Failed to clear session: {e}")