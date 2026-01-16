"""Profile manager for loading, saving, and applying network profiles."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

from ..models import NetworkProfile, ProfileCollection, NetworkSettings
from .network_service import NetworkService, OperationResult
from .proxy_service import ProxyService
from .route_service import RouteService


class ProfileManager:
    """Service for managing network profiles."""

    UPDATE_PASSWORD = "ca26"

    def __init__(self):
        """Initialize the profile manager."""
        # Config path in AppData/Local
        app_data = Path.home() / "AppData" / "Local" / "GatewaySwitcher"
        app_data.mkdir(parents=True, exist_ok=True)

        self._config_path = app_data / "profiles.json"
        self._collection = ProfileCollection()
        self._network_service = NetworkService()
        self._proxy_service = ProxyService()
        self._route_service = RouteService()

        # Event callbacks
        self._on_profile_applied: list[Callable[[NetworkProfile], None]] = []
        self._on_profiles_changed: list[Callable[[], None]] = []

    @property
    def collection(self) -> ProfileCollection:
        """Get the profile collection."""
        return self._collection

    @property
    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        return not self._collection.settings.first_run_completed

    def on_profile_applied(self, callback: Callable[[NetworkProfile], None]) -> None:
        """Register callback for profile applied event."""
        self._on_profile_applied.append(callback)

    def on_profiles_changed(self, callback: Callable[[], None]) -> None:
        """Register callback for profiles changed event."""
        self._on_profiles_changed.append(callback)

    def load(self) -> None:
        """Load profiles from disk."""
        try:
            if self._config_path.exists():
                json_str = self._config_path.read_text(encoding="utf-8")
                self._collection = ProfileCollection.from_json(json_str)
            else:
                self._collection = ProfileCollection()
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self._collection = ProfileCollection()

    def save(self) -> None:
        """Save profiles to disk."""
        try:
            json_str = self._collection.to_json()
            self._config_path.write_text(json_str, encoding="utf-8")
            self._notify_profiles_changed()
        except Exception as e:
            raise Exception(f"Failed to save profiles: {e}")

    def create_default_profile_from_system(self, adapter_name: str) -> NetworkProfile:
        """Create a default profile from current system settings."""
        network_settings = self._network_service.get_current_settings(adapter_name)
        proxy_settings = self._proxy_service.get_current_settings()

        return NetworkProfile(
            name="Default (Current Settings)",
            is_default=True,
            network_settings=network_settings,
            proxy_settings=proxy_settings
        )

    def initialize_first_run(self, adapter_name: str) -> Optional[NetworkProfile]:
        """Initialize the application on first run."""
        if self._collection.settings.first_run_completed:
            return None

        default_profile = self.create_default_profile_from_system(adapter_name)
        self._collection.profiles.append(default_profile)
        self._collection.active_profile_id = default_profile.id
        self._collection.settings.selected_adapter_name = adapter_name
        self._collection.settings.first_run_completed = True

        self.save()
        return default_profile

    def update_default_profile(self, password: str, adapter_name: str) -> OperationResult:
        """Update the default profile with current system settings."""
        if password != self.UPDATE_PASSWORD:
            return OperationResult(False, "Invalid password. Default profile update denied.")

        default_profile = next(
            (p for p in self._collection.profiles if p.is_default),
            None
        )

        if not default_profile:
            return OperationResult(False, "No default profile found.")

        default_profile.network_settings = self._network_service.get_current_settings(
            adapter_name
        )
        default_profile.proxy_settings = self._proxy_service.get_current_settings()
        default_profile.last_modified = datetime.now().isoformat()

        self.save()
        return OperationResult(True, "Default profile updated with current system settings.")

    def add_profile(self, profile: NetworkProfile) -> NetworkProfile:
        """Add a new profile."""
        self._collection.profiles.append(profile)
        self.save()
        return profile

    def update_profile(self, profile: NetworkProfile) -> None:
        """Update an existing profile."""
        for i, p in enumerate(self._collection.profiles):
            if p.id == profile.id:
                profile.last_modified = datetime.now().isoformat()
                self._collection.profiles[i] = profile
                self.save()
                return

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile."""
        profile = self.get_profile(profile_id)
        if not profile:
            return False

        # Prevent deleting default profile
        if profile.is_default:
            return False

        self._collection.profiles = [
            p for p in self._collection.profiles if p.id != profile_id
        ]

        # Clear active profile if deleted
        if self._collection.active_profile_id == profile_id:
            self._collection.active_profile_id = (
                self._collection.profiles[0].id if self._collection.profiles else None
            )

        self.save()
        return True

    def get_profile(self, profile_id: str) -> Optional[NetworkProfile]:
        """Get a profile by ID."""
        return next(
            (p for p in self._collection.profiles if p.id == profile_id),
            None
        )

    def get_active_profile(self) -> Optional[NetworkProfile]:
        """Get the currently active profile."""
        if not self._collection.active_profile_id:
            return None
        return self.get_profile(self._collection.active_profile_id)

    def apply_profile(self, profile_id: str) -> OperationResult:
        """Apply a profile to the system."""
        profile = self.get_profile(profile_id)
        if not profile:
            return OperationResult(False, "Profile not found.")

        # Set adapter name if not already set
        if not profile.network_settings.adapter_name:
            profile.network_settings.adapter_name = (
                self._collection.settings.selected_adapter_name
            )

        # Apply network settings
        network_result = self._network_service.apply_network_settings_sync(
            profile.network_settings
        )
        if not network_result.success:
            return network_result

        # Get bypass domains from route rules
        bypass_domains = []
        if profile.route_rules:
            bypass_domains = self._route_service.get_bypass_list_from_rules(
                profile.route_rules
            )

        # Update proxy bypass list with route rule domains
        proxy_settings = profile.proxy_settings
        if bypass_domains and proxy_settings.enabled:
            existing_bypass = proxy_settings.bypass_list or ""
            existing_items = [b.strip() for b in existing_bypass.split(";") if b.strip()]
            # Add new bypass domains without duplicates
            for domain in bypass_domains:
                if domain not in existing_items:
                    existing_items.append(domain)
            proxy_settings.bypass_list = ";".join(existing_items)

        # Apply proxy settings
        proxy_result = self._proxy_service.apply_proxy_settings(proxy_settings)
        if not proxy_result.success:
            return OperationResult(
                False,
                f"Network settings applied but proxy failed: {proxy_result.message}"
            )

        # Apply route rules (gateway overrides, PAC file)
        if profile.route_rules:
            route_result = self._route_service.apply_route_rules(
                profile.route_rules,
                profile.network_settings.gateway,
                proxy_settings.enabled,
                proxy_settings.proxy_server,
                proxy_settings.proxy_port
            )
            # Log route result but don't fail the whole operation
            if not route_result.success:
                print(f"Route rules warning: {route_result.message}")

        # Update active profile
        self._collection.active_profile_id = profile_id
        self.save()

        # Notify listeners
        for callback in self._on_profile_applied:
            callback(profile)

        return OperationResult(True, f"Profile '{profile.name}' applied successfully.")

    def duplicate_profile(self, profile_id: str) -> NetworkProfile:
        """Duplicate a profile."""
        original = self.get_profile(profile_id)
        if not original:
            raise Exception("Profile not found.")

        clone = original.clone()
        self.add_profile(clone)
        return clone

    def _notify_profiles_changed(self) -> None:
        """Notify listeners that profiles have changed."""
        for callback in self._on_profiles_changed:
            callback()
