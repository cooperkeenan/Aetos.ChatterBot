# src/messaging/domain/interfaces/message_interface.py
"""
Message service interface
"""

from abc import ABC, abstractmethod
from ..models.message_models import MessageRequest, MessageResult


class IMessageService(ABC):
    """Interface for sending messages"""
    
    @abstractmethod
    def send_message(self, request: MessageRequest) -> MessageResult:
        """Send message to seller"""
        pass