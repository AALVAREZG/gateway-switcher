"""Network configuration service using netsh commands."""

import subprocess
import re
from dataclasses import dataclass
from typing import Optional

from ..models import NetworkSettings


@dataclass
class OperationResult:
    """Result of a network operation."""

    success: bool
    message: str


@dataclass
class NetworkAdapterInfo:
    """Information about a network adapter."""

    name: str
    description: str
    status: str
    ip_address: str
    subnet_mask: str
    gateway: str
    dns_servers: list[str]
    is_dhcp_enabled: bool

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected."""
        return self.status.lower() in ("connected", "conectado", "up")

    @property
    def status_text(self) -> str:
        """Get human-readable status."""
        return "Connected" if self.is_connected else "Disconnected"


class NetworkService:
    """Service for configuring network adapter settings."""

    def get_network_adapters(self) -> list[NetworkAdapterInfo]:
        """Get list of available network adapters."""
        adapters = []

        try:
            # Get adapter names and status
            result = subprocess.run(
                ["netsh", "interface", "show", "interface"],
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="replace"
            )

            lines = result.stdout.strip().split("\n")
            for line in lines[3:]:  # Skip header lines
                parts = line.split()
                if len(parts) >= 4:
                    status = parts[0]
                    adapter_type = parts[1]
                    name = " ".join(parts[3:])

                    if adapter_type.lower() in ("dedicated", "dedicado"):
                        adapter_info = self._get_adapter_details(name, status)
                        if adapter_info:
                            adapters.append(adapter_info)

        except Exception as e:
            print(f"Error getting adapters: {e}")

        return adapters

    def _get_adapter_details(self, name: str, status: str) -> Optional[NetworkAdapterInfo]:
        """Get detailed information for a specific adapter."""
        try:
            # Get IP configuration
            result = subprocess.run(
                ["netsh", "interface", "ip", "show", "config", f"name={name}"],
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="replace"
            )

            output = result.stdout
            ip_address = ""
            subnet_mask = ""
            gateway = ""
            dns_servers = []
            is_dhcp = False

            # Parse IP address
            ip_match = re.search(r"IP[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if ip_match:
                ip_address = ip_match.group(1)

            # Parse subnet mask
            mask_match = re.search(r"(?:Subnet|Máscara)[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if mask_match:
                subnet_mask = mask_match.group(1)

            # Parse gateway
            gw_match = re.search(r"(?:Gateway|Puerta de enlace)[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if gw_match:
                gateway = gw_match.group(1)

            # Parse DNS servers
            dns_matches = re.findall(r"DNS[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            dns_servers = dns_matches if dns_matches else []

            # Check if DHCP is enabled
            is_dhcp = "DHCP" in output and ("Yes" in output or "Sí" in output)

            return NetworkAdapterInfo(
                name=name,
                description=name,
                status=status,
                ip_address=ip_address,
                subnet_mask=subnet_mask,
                gateway=gateway,
                dns_servers=dns_servers,
                is_dhcp_enabled=is_dhcp
            )

        except Exception as e:
            print(f"Error getting adapter details for {name}: {e}")
            return None

    def get_current_settings(self, adapter_name: str) -> NetworkSettings:
        """Get current network configuration for an adapter."""
        adapters = self.get_network_adapters()
        adapter = next((a for a in adapters if a.name == adapter_name), None)

        if not adapter:
            return NetworkSettings()

        return NetworkSettings(
            adapter_name=adapter.name,
            use_dhcp=adapter.is_dhcp_enabled,
            ip_address=adapter.ip_address,
            subnet_mask=adapter.subnet_mask,
            gateway=adapter.gateway,
            use_dhcp_dns=adapter.is_dhcp_enabled,
            primary_dns=adapter.dns_servers[0] if adapter.dns_servers else "",
            secondary_dns=adapter.dns_servers[1] if len(adapter.dns_servers) > 1 else ""
        )

    async def apply_network_settings(self, settings: NetworkSettings) -> OperationResult:
        """Apply network settings to the specified adapter."""
        return self.apply_network_settings_sync(settings)

    def apply_network_settings_sync(self, settings: NetworkSettings) -> OperationResult:
        """Apply network settings synchronously."""
        try:
            adapter_name = settings.adapter_name
            if not adapter_name:
                return OperationResult(False, "No network adapter specified.")

            if settings.use_dhcp:
                # Enable DHCP for IP address
                result = self._run_netsh(
                    f'interface ip set address "{adapter_name}" dhcp'
                )
                if not result.success:
                    return OperationResult(False, f"Failed to enable DHCP: {result.message}")
            else:
                # Set static IP configuration
                if not settings.ip_address or not settings.subnet_mask:
                    return OperationResult(
                        False,
                        "IP address and subnet mask are required for static configuration."
                    )

                gateway = settings.gateway if settings.gateway else "none"
                result = self._run_netsh(
                    f'interface ip set address "{adapter_name}" static '
                    f'{settings.ip_address} {settings.subnet_mask} {gateway}'
                )
                if not result.success:
                    return OperationResult(False, f"Failed to set static IP: {result.message}")

            # Configure DNS
            if settings.use_dhcp_dns:
                result = self._run_netsh(f'interface ip set dns "{adapter_name}" dhcp')
                if not result.success:
                    return OperationResult(False, f"Failed to set DHCP DNS: {result.message}")
            else:
                # Set primary DNS
                if settings.primary_dns:
                    result = self._run_netsh(
                        f'interface ip set dns "{adapter_name}" static {settings.primary_dns} primary'
                    )
                    if not result.success:
                        return OperationResult(False, f"Failed to set primary DNS: {result.message}")

                    # Set secondary DNS
                    if settings.secondary_dns:
                        result = self._run_netsh(
                            f'interface ip add dns "{adapter_name}" {settings.secondary_dns} index=2'
                        )
                        if not result.success:
                            return OperationResult(
                                False,
                                f"Failed to set secondary DNS: {result.message}"
                            )

            return OperationResult(True, "Network settings applied successfully.")

        except Exception as e:
            return OperationResult(False, f"Error applying network settings: {e}")

    def _run_netsh(self, arguments: str) -> OperationResult:
        """Run a netsh command and return the result."""
        try:
            result = subprocess.run(
                f"netsh {arguments}",
                shell=True,
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="replace"
            )

            if result.returncode == 0:
                return OperationResult(True, result.stdout)
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return OperationResult(False, error_msg)

        except Exception as e:
            return OperationResult(False, str(e))
