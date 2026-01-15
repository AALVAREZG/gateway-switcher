"""Services for Gateway Switcher."""

from .network_service import NetworkService, NetworkAdapterInfo, OperationResult
from .proxy_service import ProxyService
from .profile_manager import ProfileManager

__all__ = [
    "NetworkService",
    "NetworkAdapterInfo",
    "OperationResult",
    "ProxyService",
    "ProfileManager"
]
