# src/core/config_service.py
"""
Configuration service - Central configuration management
Follows Single Responsibility Principle
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BrowserConfig:
    """Browser-specific configuration"""
    headless: bool = True
    window_size: str = "1920,1080"
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    page_load_timeout: int = 30
    implicit_wait: int = 10
    enable_stealth: bool = True


@dataclass
class ProxyConfig:
    """Proxy-specific configuration"""
    enabled: bool = False
    provider: str = "iproyal"
    sticky_sessions: bool = True
    connection_timeout: int = 15
    # Credentials from environment
    username: Optional[str] = None
    password: Optional[str] = None
    country: str = "gb"
    city: str = "edinburgh"


@dataclass
class FacebookConfig:
    """Facebook-specific configuration"""
    login_url: str = "https://www.facebook.com/login"
    max_login_attempts: int = 3
    session_refresh_hours: int = 12
    # Credentials from environment
    username: Optional[str] = None
    password: Optional[str] = None

##
@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    enabled: bool = True
    max_requests_per_day: int = 50


@dataclass
class CaptchaConfig:
    """Captcha solving configuration"""
    enabled: bool = True
    provider: str = "2captcha"
    solve_timeout: int = 300
    # API key from environment
    api_key: Optional[str] = None


@dataclass
class PathConfig:
    """Path configuration"""
    cookies_dir: str = "/app/cookies"
    logs_dir: str = "/app/logs"
    screenshots_dir: str = "/app/logs/screenshots"


class ConfigService:
    """
    Central configuration service
    Loads configuration from YAML and environment variables
    """
    
    def __init__(self, config_path: str = "/app/config.yaml"):
        self.config_path = config_path
        self._raw_config: Dict[str, Any] = {}
        
        # Configuration objects
        self.browser = BrowserConfig()
        self.proxy = ProxyConfig()
        self.facebook = FacebookConfig()
        self.rate_limit = RateLimitConfig()
        self.captcha = CaptchaConfig()
        self.paths = PathConfig()
        
        # Load configuration
        self._load_config()
        self._load_env_vars()
        self._ensure_directories()
        
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self._raw_config = yaml.safe_load(f) or {}
                self._apply_config()
            else:
                print(f"[Config] No config file found at {self.config_path}, using defaults")
        except Exception as e:
            print(f"[Config] Error loading config: {e}, using defaults")
    
    def _apply_config(self) -> None:
        """Apply loaded configuration to dataclasses"""
        # Browser config
        if 'browser' in self._raw_config:
            for key, value in self._raw_config['browser'].items():
                if hasattr(self.browser, key):
                    setattr(self.browser, key, value)
        
        # Proxy config
        if 'proxy' in self._raw_config:
            for key, value in self._raw_config['proxy'].items():
                if hasattr(self.proxy, key):
                    setattr(self.proxy, key, value)
        
        # Facebook config
        if 'facebook' in self._raw_config:
            for key, value in self._raw_config['facebook'].items():
                if hasattr(self.facebook, key):
                    setattr(self.facebook, key, value)
        
        # Rate limit config
        if 'rate_limiting' in self._raw_config:
            for key, value in self._raw_config['rate_limiting'].items():
                if hasattr(self.rate_limit, key):
                    setattr(self.rate_limit, key, value)
        
        # Captcha config
        if 'captcha' in self._raw_config:
            for key, value in self._raw_config['captcha'].items():
                if hasattr(self.captcha, key):
                    setattr(self.captcha, key, value)
        
        # Paths config
        if 'paths' in self._raw_config:
            for key, value in self._raw_config['paths'].items():
                if hasattr(self.paths, key):
                    setattr(self.paths, key, value)
    
    def _load_env_vars(self) -> None:
        """Load sensitive data from environment variables"""
        # Proxy credentials
        self.proxy.username = os.getenv("IPROYAL_USER")
        self.proxy.password = os.getenv("IPROYAL_PASS")
        self.proxy.country = os.getenv("PROXY_COUNTRY", self.proxy.country)
        self.proxy.city = os.getenv("PROXY_CITIES", self.proxy.city).split(',')[0]
        
        # Facebook credentials
        self.facebook.username = os.getenv("FACEBOOK_USER") or os.getenv("GOOGLE_USER")
        self.facebook.password = os.getenv("FACEBOOK_PASS") or os.getenv("GOOGLE_PASS")
        
        # Captcha API key
        self.captcha.api_key = os.getenv("TWOCAPTCHA_API_KEY")
        
        # Override proxy enabled from env if set
        if os.getenv("USE_PROXY"):
            self.proxy.enabled = os.getenv("USE_PROXY", "false").lower() == "true"
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist"""
        for path_attr in ['cookies_dir', 'logs_dir', 'screenshots_dir']:
            path = getattr(self.paths, path_attr)
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def get_browser_options(self) -> Dict[str, Any]:
        """Get browser configuration as dict"""
        return {
            'headless': self.browser.headless,
            'window_size': self.browser.window_size,
            'user_agent': self.browser.user_agent,
            'page_load_timeout': self.browser.page_load_timeout,
            'implicit_wait': self.browser.implicit_wait,
            'enable_stealth': self.browser.enable_stealth
        }
    
    def get_proxy_url(self) -> Optional[str]:
        """Build and return proxy URL if enabled"""
        if not self.proxy.enabled:
            return None
            
        if not self.proxy.username or not self.proxy.password:
            print("[Config] Proxy enabled but credentials not found")
            return None
        
        # Build proxy URL based on provider
        if self.proxy.provider == "iproyal":
            parts = [f"country-{self.proxy.country}"]
            if self.proxy.city:
                parts.append(f"city-{self.proxy.city}")
            
            if self.proxy.sticky_sessions:
                import hashlib
                import datetime
                session_id = hashlib.md5(
                    f"fb-scraper-{datetime.date.today()}".encode()
                ).hexdigest()[:8]
                parts.append(f"session-{session_id}")
            
            password = f"{self.proxy.password}_{'_'.join(parts)}"
            return f"http://{self.proxy.username}:{password}@geo.iproyal.com:12321"
        
        return None
    
    def is_valid(self) -> bool:
        """Check if configuration has required values"""
        if not self.facebook.username or not self.facebook.password:
            print("[Config] Missing Facebook credentials")
            return False
        
        if self.proxy.enabled and not self.get_proxy_url():
            print("[Config] Proxy enabled but invalid configuration")
            return False
        
        if self.captcha.enabled and not self.captcha.api_key:
            print("[Config] Captcha enabled but no API key")
            # Don't fail, just warn
        
        return True
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"""
Configuration:
  Browser: headless={self.browser.headless}, stealth={self.browser.enable_stealth}
  Proxy: enabled={self.proxy.enabled}, provider={self.proxy.provider}
  Facebook: user={self.facebook.username[:20]}... if self.facebook.username else 'None'
  Rate Limit: enabled={self.rate_limit.enabled}, max={self.rate_limit.max_requests_per_day}/day
  Captcha: enabled={self.captcha.enabled}, provider={self.captcha.provider}
"""


# Singleton instance
_config_instance: Optional[ConfigService] = None


def get_config() -> ConfigService:
    """Get singleton configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigService()
    return _config_instance