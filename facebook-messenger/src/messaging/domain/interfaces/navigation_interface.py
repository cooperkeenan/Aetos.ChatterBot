# src/messaging/domain/interfaces/navigation_interface.py
"""
Navigation service interface
"""

from abc import ABC, abstractmethod
from ..models.navigation_models import NavigationResult


class INavigationService(ABC):
    """Interface for navigating to listings"""
    
    @abstractmethod
    def navigate_to_listing(self, url: str) -> NavigationResult:
        """Navigate to a marketplace listing"""
        pass
    
    @abstractmethod
    def find_message_button(self) -> bool:
        """Find and click message button"""
        pass