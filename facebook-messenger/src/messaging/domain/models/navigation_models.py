# src/messaging/domain/models/navigation_models.py
"""
Navigation domain models
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class NavigationResult:
    """Result of navigating to a listing"""
    success: bool
    url: str
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()