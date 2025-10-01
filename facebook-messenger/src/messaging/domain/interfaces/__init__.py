# src/messaging/domain/interfaces/__init__.py
"""
Domain interfaces
"""

from .navigation_interface import INavigationService
from .message_interface import IMessageService


__all__ = [
    'INavigationService',
    'IMessageService'
]