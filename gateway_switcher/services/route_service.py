"""Route rules service for applying domain-based routing."""

import os
import socket
import subprocess
from pathlib import Path
from typing import Optional

from ..models import RouteRule, NetworkProfile
from .network_service import OperationResult


class RouteService:
    """Service for applying custom route rules."""

    # PAC file location
    PAC_FILE_DIR = Path(os.environ.get("APPDATA", "")) / "GatewaySwitcher"
    PAC_FILE_PATH = PAC_FILE_DIR / "proxy.pac"

    def __init__(self):
        # Ensure PAC directory exists
        self.PAC_FILE_DIR.mkdir(parents=True, exist_ok=True)

    def apply_route_rules(
        self,
        rules: list[RouteRule],
        default_gateway: str,
        default_proxy_enabled: bool,
        default_proxy_server: str,
        default_proxy_port: int
    ) -> OperationResult:
        """Apply route rules.

        This method:
        1. Creates/updates a PAC file for proxy rules
        2. Adds static routes for gateway overrides

        Args:
            rules: List of route rules to apply
            default_gateway: The default gateway from network settings
            default_proxy_enabled: Whether proxy is enabled by default
            default_proxy_server: Default proxy server
            default_proxy_port: Default proxy port

        Returns:
            OperationResult with success status and message
        """
        if not rules:
            # Remove PAC file if no rules
            self._remove_pac_file()
            return OperationResult(True, "No route rules to apply.")

        enabled_rules = [r for r in rules if r.enabled]
        if not enabled_rules:
            self._remove_pac_file()
            return OperationResult(True, "No enabled route rules to apply.")

        messages = []

        # Apply gateway-based routes
        gateway_rules = [r for r in enabled_rules if r.use_custom_gateway and r.custom_gateway]
        if gateway_rules:
            result = self._apply_gateway_routes(gateway_rules)
            messages.append(result.message)

        # Generate PAC file for proxy rules
        proxy_rules = [r for r in enabled_rules if r.bypass_proxy or r.use_custom_proxy]
        if proxy_rules:
            result = self._generate_pac_file(
                proxy_rules,
                default_proxy_enabled,
                default_proxy_server,
                default_proxy_port
            )
            messages.append(result.message)
        else:
            self._remove_pac_file()

        return OperationResult(True, " | ".join(messages) if messages else "Route rules applied.")

    def get_bypass_list_from_rules(self, rules: list[RouteRule]) -> list[str]:
        """Get list of domains to bypass from route rules.

        Returns domains that should bypass the proxy, formatted for
        Windows proxy bypass list.
        """
        bypass_domains = []
        for rule in rules:
            if rule.enabled and rule.bypass_proxy:
                pattern = rule.pattern
                # Convert to Windows bypass format
                if rule.match_type == "suffix":
                    # "google.com" becomes "*.google.com;google.com"
                    bypass_domains.append(f"*.{pattern}")
                    bypass_domains.append(pattern)
                elif rule.match_type == "exact":
                    bypass_domains.append(pattern)
                elif rule.match_type == "contains":
                    bypass_domains.append(f"*{pattern}*")
                else:
                    bypass_domains.append(pattern)

        return bypass_domains

    def _apply_gateway_routes(self, rules: list[RouteRule]) -> OperationResult:
        """Apply static routes for gateway overrides.

        This resolves domain names to IPs and adds routes via the specified gateway.
        """
        routes_added = 0
        errors = []

        for rule in rules:
            try:
                # Resolve domain to IP addresses
                ips = self._resolve_domain(rule.pattern)
                if not ips:
                    errors.append(f"Could not resolve {rule.pattern}")
                    continue

                for ip in ips:
                    # Add route: route ADD destination MASK 255.255.255.255 gateway
                    result = subprocess.run(
                        ["route", "ADD", ip, "MASK", "255.255.255.255", rule.custom_gateway],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        routes_added += 1
                    else:
                        errors.append(f"Failed to add route for {ip}: {result.stderr}")

            except Exception as e:
                errors.append(f"Error processing {rule.pattern}: {e}")

        if routes_added > 0:
            msg = f"Added {routes_added} static route(s)."
            if errors:
                msg += f" Errors: {len(errors)}"
            return OperationResult(True, msg)
        elif errors:
            return OperationResult(False, f"Route errors: {'; '.join(errors[:3])}")
        else:
            return OperationResult(True, "No gateway routes to add.")

    def _resolve_domain(self, domain: str) -> list[str]:
        """Resolve a domain name to IP addresses."""
        # Remove wildcards for resolution
        clean_domain = domain.lstrip("*.")

        try:
            # Get all IPv4 addresses
            results = socket.getaddrinfo(clean_domain, None, socket.AF_INET)
            ips = list(set(r[4][0] for r in results))
            return ips
        except socket.gaierror:
            return []

    def _generate_pac_file(
        self,
        rules: list[RouteRule],
        default_proxy_enabled: bool,
        default_proxy_server: str,
        default_proxy_port: int
    ) -> OperationResult:
        """Generate a PAC (Proxy Auto-Config) file.

        PAC files allow fine-grained control over which proxy to use
        for different URLs/domains.
        """
        # Build the PAC file content
        default_return = "DIRECT"
        if default_proxy_enabled and default_proxy_server:
            default_return = f"PROXY {default_proxy_server}:{default_proxy_port}"

        conditions = []
        for rule in rules:
            if rule.bypass_proxy:
                # Direct connection (bypass proxy)
                proxy_return = "DIRECT"
            elif rule.use_custom_proxy and rule.custom_proxy_server:
                # Custom proxy
                proxy_return = f"PROXY {rule.custom_proxy_server}:{rule.custom_proxy_port}"
            else:
                continue

            # Generate condition based on match type
            if rule.match_type == "exact":
                condition = f'if (host == "{rule.pattern}") return "{proxy_return}";'
            elif rule.match_type == "suffix":
                # Match domain and all subdomains
                condition = (
                    f'if (dnsDomainIs(host, "{rule.pattern}") || '
                    f'dnsDomainIs(host, ".{rule.pattern}")) return "{proxy_return}";'
                )
            elif rule.match_type == "contains":
                condition = f'if (host.indexOf("{rule.pattern}") !== -1) return "{proxy_return}";'
            elif rule.match_type == "regex":
                # Use shExpMatch for simple wildcard patterns
                pattern = rule.pattern.replace(".", "\\.").replace("*", ".*")
                condition = f'if (shExpMatch(host, "{rule.pattern}")) return "{proxy_return}";'
            else:
                continue

            # Add comment with rule name if available
            if rule.name:
                conditions.append(f"    // {rule.name}")
            conditions.append(f"    {condition}")

        pac_content = f'''// Gateway Switcher Auto-Generated PAC File
// Do not edit manually - changes will be overwritten

function FindProxyForURL(url, host) {{
    // Normalize hostname
    host = host.toLowerCase();

    // Custom route rules
{chr(10).join(conditions)}

    // Default
    return "{default_return}";
}}
'''

        try:
            self.PAC_FILE_PATH.write_text(pac_content, encoding='utf-8')
            return OperationResult(
                True,
                f"PAC file created: {self.PAC_FILE_PATH}"
            )
        except Exception as e:
            return OperationResult(False, f"Failed to create PAC file: {e}")

    def _remove_pac_file(self) -> None:
        """Remove the PAC file if it exists."""
        try:
            if self.PAC_FILE_PATH.exists():
                self.PAC_FILE_PATH.unlink()
        except Exception:
            pass

    def get_pac_file_url(self) -> Optional[str]:
        """Get the file:// URL for the PAC file if it exists."""
        if self.PAC_FILE_PATH.exists():
            # Convert to file:// URL format
            path_str = str(self.PAC_FILE_PATH).replace("\\", "/")
            return f"file:///{path_str}"
        return None

    def clear_static_routes(self, rules: list[RouteRule]) -> OperationResult:
        """Remove static routes that were added for route rules."""
        routes_removed = 0
        errors = []

        gateway_rules = [r for r in rules if r.use_custom_gateway and r.custom_gateway]

        for rule in gateway_rules:
            try:
                ips = self._resolve_domain(rule.pattern)
                for ip in ips:
                    result = subprocess.run(
                        ["route", "DELETE", ip],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        routes_removed += 1
            except Exception as e:
                errors.append(str(e))

        if routes_removed > 0:
            return OperationResult(True, f"Removed {routes_removed} static route(s).")
        return OperationResult(True, "No routes to remove.")
