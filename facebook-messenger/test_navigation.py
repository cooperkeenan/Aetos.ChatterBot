# test_navigation.py
"""
Test script for navigation service with proxy and stealth
"""

from dotenv import load_dotenv
from core.config_service import get_config
from services.browser_service import BrowserService
from services.proxy_service import ProxyService
from services.facebook_service import FacebookService
from services.session_service import SessionService
from messaging.services.navigation_service import NavigationService

# Load environment variables
load_dotenv()


def test_navigation():
    """Test navigation with proxy and stealth"""
    
    # Hardcoded test link - replace with actual listing
    TEST_LINK = "https://www.facebook.com/marketplace/item/1234150477463732470856789"
    
    print("🧪 Testing Facebook Messenger Navigation (Stealth + Proxy)")
    print("="*60)
    
    try:
        # Initialize services
        config = get_config()
        proxy_service = ProxyService()
        
        # Test proxy first
        if proxy_service.is_configured():
            proxy_url = proxy_service.get_proxy_url()
            ip = proxy_service.test_proxy(proxy_url)
            if not ip:
                print("❌ Proxy test failed - check credentials")
                return
        else:
            print("⚠️ No proxy configured - continuing without proxy")
            proxy_service = None
        
        browser = BrowserService(config, proxy_service)
        session = SessionService(config)
        facebook = FacebookService(config, browser, session)
        navigation = NavigationService(browser, facebook)
        
        with browser:
            # Try to restore session first
            if facebook.restore_session():
                print("✅ Session restored")
            else:
                print("🔑 Logging in...")
                if not facebook.login():
                    print("❌ Login failed")
                    return
            
            # Test navigation
            print(f"🎯 Testing navigation to: {TEST_LINK}")
            result = navigation.navigate_to_listing(TEST_LINK)
            
            if result.success:
                print("✅ Navigation successful")
                
                # Test finding message button
                if navigation.find_message_button():
                    print("✅ Message button found and clicked")
                else:
                    print("❌ Message button not found")
            else:
                print(f"❌ Navigation failed: {result.error}")
    
    except Exception as e:
        print(f"💥 Test failed: {e}")
        if 'browser' in locals():
            browser.take_screenshot("test_error")


if __name__ == "__main__":
    test_navigation()