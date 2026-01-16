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
class RouteRule:
    """Custom routing rule for specific domains/destinations.

    Allows routing specific traffic differently - e.g., different gateway
    or bypassing proxy for certain domains.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""  # User-friendly name
    pattern: str = ""  # Domain pattern (e.g., "api.anthropic.com", "*.google.com")
    match_type: str = "exact"  # "exact", "suffix", "contains", "regex"
    enabled: bool = True

    # Gateway override
    use_custom_gateway: bool = False
    custom_gateway: str = ""  # Gateway IP for this route

    # Proxy override
    bypass_proxy: bool = False  # If True, don't use proxy for this domain
    use_custom_proxy: bool = False  # If True, use a different proxy
    custom_proxy_server: str = ""
    custom_proxy_port: int = 8080

    # DNS override (optional)
    use_custom_dns: bool = False
    custom_dns: str = ""

    def clone(self) -> "RouteRule":
        """Create a copy of this rule with new ID."""
        return RouteRule(
            id=str(uuid.uuid4()),
            name=f"{self.name} (Copy)" if self.name else "",
            pattern=self.pattern,
            match_type=self.match_type,
            enabled=self.enabled,
            use_custom_gateway=self.use_custom_gateway,
            custom_gateway=self.custom_gateway,
            bypass_proxy=self.bypass_proxy,
            use_custom_proxy=self.use_custom_proxy,
            custom_proxy_server=self.custom_proxy_server,
            custom_proxy_port=self.custom_proxy_port,
            use_custom_dns=self.use_custom_dns,
            custom_dns=self.custom_dns
        )

    def matches(self, domain: str) -> bool:
        """Check if this rule matches the given domain."""
        import re

        if not self.pattern or not domain:
            return False

        pattern = self.pattern.lower()
        domain = domain.lower()

        if self.match_type == "exact":
            return domain == pattern
        elif self.match_type == "suffix":
            # Matches domain and all subdomains
            return domain == pattern or domain.endswith(f".{pattern}")
        elif self.match_type == "contains":
            return pattern in domain
        elif self.match_type == "regex":
            try:
                return bool(re.match(pattern, domain))
            except re.error:
                return False
        return False

    @property
    def description(self) -> str:
        """Get a human-readable description of the rule."""
        parts = []
        if self.bypass_proxy:
            parts.append("No Proxy")
        if self.use_custom_gateway and self.custom_gateway:
            parts.append(f"GW: {self.custom_gateway}")
        if self.use_custom_proxy and self.custom_proxy_server:
            parts.append(f"Proxy: {self.custom_proxy_server}:{self.custom_proxy_port}")
        if self.use_custom_dns and self.custom_dns:
            parts.append(f"DNS: {self.custom_dns}")
        return " | ".join(parts) if parts else "No overrides"


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
    route_rules: list[RouteRule] = field(default_factory=list)

    def clone(self) -> "NetworkProfile":
        """Create a copy of this profile with new ID."""
        return NetworkProfile(
            id=str(uuid.uuid4()),
            name=f"{self.name} (Copy)",
            is_default=False,
            created_at=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            network_settings=self.network_settings.clone(),
            proxy_settings=self.proxy_settings.clone(),
            route_rules=[r.clone() for r in self.route_rules]
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
            },
            "route_rules": [asdict(r) for r in self.route_rules]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NetworkProfile":
        """Create profile from dictionary."""
        network_settings = NetworkSettings(**data.get("network_settings", {}))
        proxy_settings = ProxySettings(**data.get("proxy_settings", {}))
        route_rules = [RouteRule(**r) for r in data.get("route_rules", [])]

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "New Profile"),
            is_default=data.get("is_default", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_modified=data.get("last_modified", datetime.now().isoformat()),
            network_settings=network_settings,
            proxy_settings=proxy_settings,
            route_rules=route_rules
        )

    def get_matching_rule(self, domain: str) -> Optional[RouteRule]:
        """Find the first matching enabled route rule for a domain."""
        for rule in self.route_rules:
            if rule.enabled and rule.matches(domain):
                return rule
        return None


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
