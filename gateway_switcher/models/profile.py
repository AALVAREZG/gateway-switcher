"""Network profile data models using dataclasses."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid
import json


@dataclass
class NetworkSettings:
    """Network adapter configuration settings."""

    use_dhcp: bool = True
    ip_address: str = ""
    subnet_mask: str = "255.255.255.0"
    gateway: str = ""
    use_dhcp_dns: bool = True
    primary_dns: str = ""
    secondary_dns: str = ""
    adapter_name: str = ""

    def clone(self) -> "NetworkSettings":
        """Create a copy of this settings object."""
        return NetworkSettings(
            use_dhcp=self.use_dhcp,
            ip_address=self.ip_address,
            subnet_mask=self.subnet_mask,
            gateway=self.gateway,
            use_dhcp_dns=self.use_dhcp_dns,
            primary_dns=self.primary_dns,
            secondary_dns=self.secondary_dns,
            adapter_name=self.adapter_name
        )


@dataclass
class ProxySettings:
    """Proxy configuration settings."""

    enabled: bool = False
    proxy_server: str = ""
    proxy_port: int = 8080
    use_authentication: bool = False
    username: str = ""
    password: str = ""
    bypass_list: str = "localhost;127.0.0.1"
    bypass_local: bool = True

    @property
    def full_proxy_address(self) -> str:
        """Get full proxy address as server:port."""
        if not self.proxy_server:
            return ""
        return f"{self.proxy_server}:{self.proxy_port}"

    def clone(self) -> "ProxySettings":
        """Create a copy of this settings object."""
        return ProxySettings(
            enabled=self.enabled,
            proxy_server=self.proxy_server,
            proxy_port=self.proxy_port,
            use_authentication=self.use_authentication,
            username=self.username,
            password=self.password,
            bypass_list=self.bypass_list,
            bypass_local=self.bypass_local
        )


@dataclass
class NetworkProfile:
    """Complete network configuration profile."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Profile"
    is_default: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    network_settings: NetworkSettings = field(default_factory=NetworkSettings)
    proxy_settings: ProxySettings = field(default_factory=ProxySettings)

    def clone(self) -> "NetworkProfile":
        """Create a copy of this profile with new ID."""
        return NetworkProfile(
            id=str(uuid.uuid4()),
            name=f"{self.name} (Copy)",
            is_default=False,
            created_at=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            network_settings=self.network_settings.clone(),
            proxy_settings=self.proxy_settings.clone()
        )

    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "network_settings": asdict(self.network_settings),
            "proxy_settings": {
                k: v for k, v in asdict(self.proxy_settings).items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NetworkProfile":
        """Create profile from dictionary."""
        network_settings = NetworkSettings(**data.get("network_settings", {}))
        proxy_settings = ProxySettings(**data.get("proxy_settings", {}))

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "New Profile"),
            is_default=data.get("is_default", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_modified=data.get("last_modified", datetime.now().isoformat()),
            network_settings=network_settings,
            proxy_settings=proxy_settings
        )


@dataclass
class AppSettings:
    """Application-wide settings."""

    start_with_windows: bool = False
    start_minimized: bool = True
    show_notifications: bool = True
    selected_adapter_name: str = ""
    first_run_completed: bool = False


@dataclass
class ProfileCollection:
    """Container for all network profiles and app settings."""

    version: str = "1.0"
    active_profile_id: Optional[str] = None
    profiles: list[NetworkProfile] = field(default_factory=list)
    settings: AppSettings = field(default_factory=AppSettings)

    def to_dict(self) -> dict:
        """Convert collection to dictionary."""
        return {
            "version": self.version,
            "active_profile_id": self.active_profile_id,
            "profiles": [p.to_dict() for p in self.profiles],
            "settings": asdict(self.settings)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProfileCollection":
        """Create collection from dictionary."""
        profiles = [NetworkProfile.from_dict(p) for p in data.get("profiles", [])]
        settings = AppSettings(**data.get("settings", {}))

        return cls(
            version=data.get("version", "1.0"),
            active_profile_id=data.get("active_profile_id"),
            profiles=profiles,
            settings=settings
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ProfileCollection":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
