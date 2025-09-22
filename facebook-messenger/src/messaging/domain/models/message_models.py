# src/messaging/domain/models/message_models.py
"""
Message domain models
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class MessageRequest:
    """Request to send a message"""
    listing_url: str
    camera_name: str
    price: Optional[float] = None
    template_type: str = "interest"


@dataclass
class MessageResult:
    """Result of sending a message"""
    success: bool
    listing_url: str
    message_sent: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()