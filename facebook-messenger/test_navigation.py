from dotenv import load_dotenv
from core.config_service import get_config
from services.browser_service import BrowserService
from services.proxy_service import ProxyService
from services.facebook_service import FacebookService
from services.session_service import SessionService
from messaging.services.navigation_service import NavigationService

load_dotenv()


def test_navigation():
    """Test navigation with saved cookies"""
    
    TEST_LINK = "https://www.facebook.com/marketplace/item/1234150477463732470856789"
    
    print("Testing Facebook Messenger Navigation")
    print("="*60)
    
    try:
        config = get_config()
        proxy_service = ProxyService() if config.proxy.enabled else None
        
        if proxy_service:
            ip = proxy_service.test_proxy(proxy_service.get_proxy_url())
            if not ip:
                print("Proxy test failed")
                return
        
        browser = BrowserService(config, proxy_service)
        session = SessionService(config)
        facebook = FacebookService(config, browser, session)
        navigation = NavigationService(browser, facebook)
        
        with browser:
            if not facebook.restore_session():
                print("No valid session - run scraper to generate cookies first")
                return
            
            print(f"Testing navigation to: {TEST_LINK}")
            result = navigation.navigate_to_listing(TEST_LINK)
            
            if result.success:
                print("Navigation successful")
                if navigation.find_message_button():
                    print("Message button found and clicked")
                else:
                    print("Message button not found")
            else:
                print(f"Navigation failed: {result.error}")
    
    except Exception as e:
        print(f"Test failed: {e}")
        if 'browser' in locals():
            browser.take_screenshot("test_error")


if __name__ == "__main__":
    test_navigation()