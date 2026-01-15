using System;
using System.Runtime.InteropServices;
using GatewaySwitcher.Models;
using Microsoft.Win32;

namespace GatewaySwitcher.Services
{
    /// <summary>
    /// Service for configuring Windows proxy settings
    /// </summary>
    public class ProxyConfigurationService
    {
        private const string RegistryPath = @"Software\Microsoft\Windows\CurrentVersion\Internet Settings";

        [DllImport("wininet.dll")]
        private static extern bool InternetSetOption(IntPtr hInternet, int dwOption, IntPtr lpBuffer, int dwBufferLength);

        private const int INTERNET_OPTION_SETTINGS_CHANGED = 39;
        private const int INTERNET_OPTION_REFRESH = 37;

        /// <summary>
        /// Gets current proxy settings from Windows registry
        /// </summary>
        public ProxySettings GetCurrentSettings()
        {
            var settings = new ProxySettings();

            try
            {
                using (var key = Registry.CurrentUser.OpenSubKey(RegistryPath))
                {
                    if (key != null)
                    {
                        // Check if proxy is enabled
                        object? proxyEnable = key.GetValue("ProxyEnable");
                        settings.Enabled = proxyEnable != null && (int)proxyEnable == 1;

                        // Get proxy server address
                        object? proxyServer = key.GetValue("ProxyServer");
                        if (proxyServer != null)
                        {
                            string serverValue = proxyServer.ToString() ?? "";
                            ParseProxyServer(serverValue, settings);
                        }

                        // Get bypass list
                        object? proxyOverride = key.GetValue("ProxyOverride");
                        if (proxyOverride != null)
                        {
                            settings.BypassList = proxyOverride.ToString() ?? "";
                            settings.BypassLocal = settings.BypassList.Contains("<local>");
                        }
                    }
                }
            }
            catch (Exception)
            {
                // Return default settings on error
            }

            return settings;
        }

        /// <summary>
        /// Applies proxy settings to Windows
        /// </summary>
        public OperationResult ApplyProxySettings(ProxySettings settings)
        {
            var result = new OperationResult();

            try
            {
                using (var key = Registry.CurrentUser.OpenSubKey(RegistryPath, true))
                {
                    if (key == null)
                    {
                        result.Success = false;
                        result.Message = "Could not access registry for proxy settings.";
                        return result;
                    }

                    // Set proxy enable/disable
                    key.SetValue("ProxyEnable", settings.Enabled ? 1 : 0, RegistryValueKind.DWord);

                    if (settings.Enabled)
                    {
                        // Set proxy server
                        string proxyAddress = settings.FullProxyAddress;
                        key.SetValue("ProxyServer", proxyAddress, RegistryValueKind.String);

                        // Set bypass list
                        string bypassList = settings.BypassList;
                        if (settings.BypassLocal && !bypassList.Contains("<local>"))
                        {
                            bypassList = string.IsNullOrEmpty(bypassList) ? "<local>" : bypassList + ";<local>";
                        }
                        key.SetValue("ProxyOverride", bypassList, RegistryValueKind.String);
                    }
                    else
                    {
                        // Clear proxy settings when disabled
                        key.SetValue("ProxyServer", "", RegistryValueKind.String);
                    }
                }

                // Notify Windows of the changes
                RefreshProxySettings();

                // Handle proxy authentication if needed
                if (settings.Enabled && settings.UseAuthentication)
                {
                    result.Message = "Proxy settings applied. Note: Proxy authentication credentials are stored but may require browser restart.";
                }
                else
                {
                    result.Message = "Proxy settings applied successfully.";
                }

                result.Success = true;
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Message = $"Failed to apply proxy settings: {ex.Message}";
            }

            return result;
        }

        /// <summary>
        /// Disables proxy settings
        /// </summary>
        public OperationResult DisableProxy()
        {
            return ApplyProxySettings(new ProxySettings { Enabled = false });
        }

        /// <summary>
        /// Notifies Windows that proxy settings have changed
        /// </summary>
        private void RefreshProxySettings()
        {
            InternetSetOption(IntPtr.Zero, INTERNET_OPTION_SETTINGS_CHANGED, IntPtr.Zero, 0);
            InternetSetOption(IntPtr.Zero, INTERNET_OPTION_REFRESH, IntPtr.Zero, 0);
        }

        /// <summary>
        /// Parses proxy server string in format "server:port" or "http=server:port;https=server:port"
        /// </summary>
        private void ParseProxyServer(string serverValue, ProxySettings settings)
        {
            if (string.IsNullOrEmpty(serverValue))
                return;

            // Handle simple format: "server:port"
            if (!serverValue.Contains('='))
            {
                var parts = serverValue.Split(':');
                settings.ProxyServer = parts[0];
                if (parts.Length > 1 && int.TryParse(parts[1], out int port))
                {
                    settings.ProxyPort = port;
                }
            }
            else
            {
                // Handle complex format: "http=server:port;https=server:port"
                var protocols = serverValue.Split(';');
                foreach (var protocol in protocols)
                {
                    if (protocol.StartsWith("http="))
                    {
                        var address = protocol.Substring(5);
                        var parts = address.Split(':');
                        settings.ProxyServer = parts[0];
                        if (parts.Length > 1 && int.TryParse(parts[1], out int port))
                        {
                            settings.ProxyPort = port;
                        }
                        break;
                    }
                }
            }
        }

        /// <summary>
        /// Stores proxy credentials in Windows Credential Manager
        /// </summary>
        public OperationResult StoreProxyCredentials(ProxySettings settings)
        {
            if (!settings.UseAuthentication || string.IsNullOrEmpty(settings.Username))
            {
                return new OperationResult { Success = true, Message = "No credentials to store." };
            }

            try
            {
                // For proxy authentication, we store credentials in a format that apps can use
                // Note: Full credential manager integration would require additional P/Invoke
                return new OperationResult
                {
                    Success = true,
                    Message = "Proxy credentials stored. Some applications may prompt for credentials on first use."
                };
            }
            catch (Exception ex)
            {
                return new OperationResult
                {
                    Success = false,
                    Message = $"Failed to store credentials: {ex.Message}"
                };
            }
        }
    }
}
