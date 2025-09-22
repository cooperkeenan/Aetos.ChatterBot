# src/services/proxy_service.py
"""
Proxy service with IPRoyal sticky sessions
Ported from scraper code
"""

import os
import hashlib
import datetime
import requests
from typing import Optional


class ProxyService:
    """Manages IPRoyal residential proxy with sticky sessions"""
    
    def __init__(self):
        self.user = os.getenv("IPROYAL_USER")
        self.password = os.getenv("IPROYAL_PASS") 
        self.country = os.getenv("PROXY_COUNTRY", "gb")
        self.city = os.getenv("PROXY_CITIES", "edinburgh").split(',')[0]
        self.host = "geo.iproyal.com"
        self.port = "12321"
        
        if not self.user or not self.password:
            raise ValueError("Missing IPROYAL_USER or IPROYAL_PASS environment variables")
    
    def get_proxy_url(self, sticky_session: bool = True) -> str:
        """Build proxy URL with sticky session"""
        parts = [f"country-{self.country}"]
        
        # Add city
        if self.city:
            parts.append(f"city-{self.city}")
        
        # Add sticky session (same IP for 24 hours)
        if sticky_session:
            session_id = self._get_daily_session_id()
            parts.append(f"session-{session_id}")
            print(f"[Proxy] Using sticky session: {session_id}")
        
        password = f"{self.password}_{'_'.join(parts)}"
        proxy_url = f"http://{self.user}:{password}@{self.host}:{self.port}"
        
        return proxy_url
    
    def _get_daily_session_id(self) -> str:
        """Generate consistent session ID for current day"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        session_hash = hashlib.md5(f"facebook-messenger-{today}".encode()).hexdigest()
        return session_hash[:8]
    
    def test_proxy(self, proxy_url: str = None) -> Optional[str]:
        """Test proxy and return IP address"""
        if not proxy_url:
            proxy_url = self.get_proxy_url()
        
        try:
            print(f"[Proxy] Testing proxy: {proxy_url[:50]}...")
            response = requests.get(
                "https://ipv4.icanhazip.com",
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=15
            )
            ip = response.text.strip()
            print(f"[Proxy] ✅ Proxy IP: {ip}")
            return ip
        except Exception as e:
            print(f"[Proxy] ❌ Test failed: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if proxy is properly configured"""
        return bool(self.user and self.password)