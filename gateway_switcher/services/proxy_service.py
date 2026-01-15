"""Proxy configuration service using Windows Registry."""

import winreg
import ctypes
from ctypes import wintypes

from ..models import ProxySettings
from .network_service import OperationResult


# Windows API for refreshing proxy settings
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37

try:
    wininet = ctypes.windll.wininet
except AttributeError:
    wininet = None


class ProxyService:
    """Service for configuring Windows proxy settings."""

    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

    def get_current_settings(self) -> ProxySettings:
        """Get current proxy settings from Windows registry."""
        settings = ProxySettings()

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REGISTRY_PATH) as key:
                # Check if proxy is enabled
                try:
                    proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
                    settings.enabled = proxy_enable == 1
                except FileNotFoundError:
                    settings.enabled = False

                # Get proxy server address
                try:
                    proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    self._parse_proxy_server(proxy_server, settings)
                except FileNotFoundError:
                    pass

                # Get bypass list
                try:
                    proxy_override, _ = winreg.QueryValueEx(key, "ProxyOverride")
                    settings.bypass_list = proxy_override
                    settings.bypass_local = "<local>" in proxy_override
                except FileNotFoundError:
                    pass

        except Exception as e:
            print(f"Error reading proxy settings: {e}")

        return settings

    def apply_proxy_settings(self, settings: ProxySettings) -> OperationResult:
        """Apply proxy settings to Windows."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                # Set proxy enable/disable
                winreg.SetValueEx(
                    key,
                    "ProxyEnable",
                    0,
                    winreg.REG_DWORD,
                    1 if settings.enabled else 0
                )

                if settings.enabled:
                    # Set proxy server
                    proxy_address = settings.full_proxy_address
                    winreg.SetValueEx(
                        key,
                        "ProxyServer",
                        0,
                        winreg.REG_SZ,
                        proxy_address
                    )

                    # Set bypass list
                    bypass_list = settings.bypass_list
                    if settings.bypass_local and "<local>" not in bypass_list:
                        bypass_list = f"{bypass_list};<local>" if bypass_list else "<local>"

                    winreg.SetValueEx(
                        key,
                        "ProxyOverride",
                        0,
                        winreg.REG_SZ,
                        bypass_list
                    )
                else:
                    # Clear proxy settings when disabled
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")

            # Notify Windows of the changes
            self._refresh_proxy_settings()

            message = "Proxy settings applied successfully."
            if settings.enabled and settings.use_authentication:
                message += " Note: Some apps may prompt for credentials."

            return OperationResult(True, message)

        except PermissionError:
            return OperationResult(
                False,
                "Permission denied. Run as administrator to change proxy settings."
            )
        except Exception as e:
            return OperationResult(False, f"Failed to apply proxy settings: {e}")

    def disable_proxy(self) -> OperationResult:
        """Disable proxy settings."""
        return self.apply_proxy_settings(ProxySettings(enabled=False))

    def _refresh_proxy_settings(self) -> None:
        """Notify Windows that proxy settings have changed."""
        if wininet:
            try:
                wininet.InternetSetOptionW(
                    None,
                    INTERNET_OPTION_SETTINGS_CHANGED,
                    None,
                    0
                )
                wininet.InternetSetOptionW(
                    None,
                    INTERNET_OPTION_REFRESH,
                    None,
                    0
                )
            except Exception:
                pass

    def _parse_proxy_server(self, server_value: str, settings: ProxySettings) -> None:
        """Parse proxy server string."""
        if not server_value:
            return

        # Handle simple format: "server:port"
        if "=" not in server_value:
            parts = server_value.split(":")
            settings.proxy_server = parts[0]
            if len(parts) > 1:
                try:
                    settings.proxy_port = int(parts[1])
                except ValueError:
                    pass
        else:
            # Handle complex format: "http=server:port;https=server:port"
            for protocol in server_value.split(";"):
                if protocol.startswith("http="):
                    address = protocol[5:]
                    parts = address.split(":")
                    settings.proxy_server = parts[0]
                    if len(parts) > 1:
                        try:
                            settings.proxy_port = int(parts[1])
                        except ValueError:
                            pass
                    break
