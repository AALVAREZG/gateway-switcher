"""Network configuration service using netsh and PowerShell commands."""

import subprocess
import re
import json
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
        return self.status.lower() in ("connected", "conectado", "up", "arriba")

    @property
    def status_text(self) -> str:
        """Get human-readable status."""
        return "Connected" if self.is_connected else "Disconnected"


class NetworkService:
    """Service for configuring network adapter settings."""

    def get_network_adapters(self) -> list[NetworkAdapterInfo]:
        """Get list of available network adapters using PowerShell."""
        adapters = []

        try:
            # Use PowerShell to get adapter info in JSON format
            ps_command = '''
            Get-NetAdapter | Where-Object { $_.PhysicalMediaType -ne 'Unspecified' -and $_.InterfaceDescription -notlike '*Virtual*' -and $_.InterfaceDescription -notlike '*Loopback*' } | ForEach-Object {
                $adapter = $_
                $ipconfig = Get-NetIPConfiguration -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue
                $ipv4 = Get-NetIPAddress -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1
                $dns = Get-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue

                @{
                    Name = $adapter.Name
                    Description = $adapter.InterfaceDescription
                    Status = $adapter.Status
                    IPAddress = if ($ipv4) { $ipv4.IPAddress } else { "" }
                    SubnetMask = if ($ipv4) {
                        $prefix = $ipv4.PrefixLength
                        $mask = ([Math]::Pow(2, $prefix) - 1) * [Math]::Pow(2, (32 - $prefix))
                        $bytes = [BitConverter]::GetBytes([UInt32]$mask)
                        [Array]::Reverse($bytes)
                        ($bytes | ForEach-Object { $_ }) -join '.'
                    } else { "" }
                    Gateway = if ($ipconfig.IPv4DefaultGateway) { $ipconfig.IPv4DefaultGateway.NextHop } else { "" }
                    DNSServers = if ($dns) { $dns.ServerAddresses } else { @() }
                    DHCPEnabled = if ($ipv4) { $ipv4.PrefixOrigin -eq 'Dhcp' } else { $false }
                }
            } | ConvertTo-Json -Depth 3
            '''

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )

            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)

                # Handle single adapter (not returned as list)
                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    dns_servers = item.get("DNSServers", [])
                    if dns_servers is None:
                        dns_servers = []
                    elif isinstance(dns_servers, str):
                        dns_servers = [dns_servers] if dns_servers else []

                    adapters.append(NetworkAdapterInfo(
                        name=item.get("Name", ""),
                        description=item.get("Description", ""),
                        status=item.get("Status", "Disconnected"),
                        ip_address=item.get("IPAddress", "") or "",
                        subnet_mask=item.get("SubnetMask", "") or "",
                        gateway=item.get("Gateway", "") or "",
                        dns_servers=dns_servers,
                        is_dhcp_enabled=item.get("DHCPEnabled", False)
                    ))

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Fallback to netsh method
            adapters = self._get_adapters_netsh()
        except Exception as e:
            print(f"Error getting adapters: {e}")
            # Fallback to netsh method
            adapters = self._get_adapters_netsh()

        return adapters

    def _get_adapters_netsh(self) -> list[NetworkAdapterInfo]:
        """Fallback method using netsh."""
        adapters = []

        try:
            # Get adapter list
            result = subprocess.run(
                ["netsh", "interface", "ipv4", "show", "interfaces"],
                capture_output=True,
                text=True,
                encoding="cp850",
                errors="replace"
            )

            lines = result.stdout.strip().split("\n")

            for line in lines:
                # Skip header and empty lines
                if not line.strip() or "---" in line or "Idx" in line or "Métr" in line:
                    continue

                parts = line.split()
                if len(parts) >= 5:
                    try:
                        # Format: Idx  Met   MTU   State        Name
                        idx = parts[0]
                        state = parts[3]
                        name = " ".join(parts[4:])

                        # Skip loopback
                        if "loopback" in name.lower():
                            continue

                        # Get details for this adapter
                        adapter_info = self._get_adapter_details_netsh(name, state)
                        if adapter_info:
                            adapters.append(adapter_info)
                    except (ValueError, IndexError):
                        continue

        except Exception as e:
            print(f"Netsh fallback error: {e}")

        return adapters

    def _get_adapter_details_netsh(self, name: str, status: str) -> Optional[NetworkAdapterInfo]:
        """Get adapter details using netsh."""
        try:
            result = subprocess.run(
                ["netsh", "interface", "ipv4", "show", "config", f"name={name}"],
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

            # More flexible regex patterns
            ip_match = re.search(r"(?:IP|Dirección IP)[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if ip_match:
                ip_address = ip_match.group(1)

            mask_match = re.search(r"(?:Subnet|Máscara|mask)[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if mask_match:
                subnet_mask = mask_match.group(1)

            gw_match = re.search(r"(?:Gateway|Puerta)[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if gw_match:
                gateway = gw_match.group(1)

            dns_matches = re.findall(r"(?:DNS|Servidores DNS)[^:]*:\s*([\d.]+)", output, re.IGNORECASE)
            if dns_matches:
                dns_servers = dns_matches

            is_dhcp = bool(re.search(r"DHCP\s*(?:habilitado|enabled|Sí|Yes)", output, re.IGNORECASE))

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
                result = self._run_netsh(
                    f'interface ip set address "{adapter_name}" dhcp'
                )
                if not result.success:
                    return OperationResult(False, f"Failed to enable DHCP: {result.message}")
            else:
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
                if settings.primary_dns:
                    result = self._run_netsh(
                        f'interface ip set dns "{adapter_name}" static {settings.primary_dns} primary'
                    )
                    if not result.success:
                        return OperationResult(False, f"Failed to set primary DNS: {result.message}")

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
