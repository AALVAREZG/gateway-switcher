"""Data models for Gateway Switcher."""

from .profile import (
    NetworkProfile, NetworkSettings, ProxySettings, ProfileCollection,
    AppSettings, RouteRule
)

__all__ = [
    "NetworkProfile", "NetworkSettings", "ProxySettings", "ProfileCollection",
    "AppSettings", "RouteRule"
]
