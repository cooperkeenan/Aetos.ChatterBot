# src/main.py
"""
Facebook Messenger - Main entry point
"""

import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main entry point"""
    print("🤖 Facebook Messenger Starting...")
    
    # TODO: Implement main messaging logic
    # For now, just run the navigation test
    try:
        from test_navigation import test_navigation
        test_navigation()
    except ImportError:
        print("❌ test_navigation not found")
        sys.exit(1)


if __name__ == "__main__":
    main()