using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.NetworkInformation;
using System.Threading.Tasks;
using GatewaySwitcher.Models;

namespace GatewaySwitcher.Services
{
    /// <summary>
    /// Service for configuring network adapter settings (IP, gateway, DNS)
    /// </summary>
    public class NetworkConfigurationService
    {
        /// <summary>
        /// Gets a list of available network adapters
        /// </summary>
        public List<NetworkAdapterInfo> GetNetworkAdapters()
        {
            var adapters = new List<NetworkAdapterInfo>();

            foreach (NetworkInterface ni in NetworkInterface.GetAllNetworkInterfaces())
            {
                if (ni.NetworkInterfaceType == NetworkInterfaceType.Ethernet ||
                    ni.NetworkInterfaceType == NetworkInterfaceType.Wireless80211)
                {
                    var props = ni.GetIPProperties();
                    var ipv4 = props.UnicastAddresses
                        .FirstOrDefault(a => a.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);

                    var gateway = props.GatewayAddresses
                        .FirstOrDefault(g => g.Address.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork);

                    var dnsServers = props.DnsAddresses
                        .Where(d => d.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork)
                        .Select(d => d.ToString())
                        .ToList();

                    adapters.Add(new NetworkAdapterInfo
                    {
                        Name = ni.Name,
                        Description = ni.Description,
                        Status = ni.OperationalStatus,
                        IpAddress = ipv4?.Address.ToString() ?? "",
                        SubnetMask = ipv4?.IPv4Mask?.ToString() ?? "",
                        Gateway = gateway?.Address.ToString() ?? "",
                        DnsServers = dnsServers,
                        IsDhcpEnabled = props.GetIPv4Properties()?.IsDhcpEnabled ?? false
                    });
                }
            }

            return adapters;
        }

        /// <summary>
        /// Gets the current network configuration for a specific adapter
        /// </summary>
        public NetworkSettings GetCurrentSettings(string adapterName)
        {
            var adapter = GetNetworkAdapters().FirstOrDefault(a => a.Name == adapterName);
            if (adapter == null)
            {
                return new NetworkSettings();
            }

            return new NetworkSettings
            {
                AdapterName = adapter.Name,
                UseDhcp = adapter.IsDhcpEnabled,
                IpAddress = adapter.IpAddress,
                SubnetMask = adapter.SubnetMask,
                Gateway = adapter.Gateway,
                UseDhcpDns = adapter.IsDhcpEnabled,
                PrimaryDns = adapter.DnsServers.Count > 0 ? adapter.DnsServers[0] : "",
                SecondaryDns = adapter.DnsServers.Count > 1 ? adapter.DnsServers[1] : ""
            };
        }

        /// <summary>
        /// Applies network settings to the specified adapter
        /// </summary>
        public async Task<OperationResult> ApplyNetworkSettings(NetworkSettings settings)
        {
            var result = new OperationResult();

            try
            {
                string adapterName = settings.AdapterName;
                if (string.IsNullOrEmpty(adapterName))
                {
                    result.Success = false;
                    result.Message = "No network adapter specified.";
                    return result;
                }

                if (settings.UseDhcp)
                {
                    // Enable DHCP for IP address
                    var dhcpResult = await RunNetshCommand($"interface ip set address \"{adapterName}\" dhcp");
                    if (!dhcpResult.Success)
                    {
                        result.Success = false;
                        result.Message = $"Failed to enable DHCP: {dhcpResult.Message}";
                        return result;
                    }
                }
                else
                {
                    // Set static IP configuration
                    if (string.IsNullOrEmpty(settings.IpAddress) || string.IsNullOrEmpty(settings.SubnetMask))
                    {
                        result.Success = false;
                        result.Message = "IP address and subnet mask are required for static configuration.";
                        return result;
                    }

                    string gateway = string.IsNullOrEmpty(settings.Gateway) ? "none" : settings.Gateway;
                    var staticResult = await RunNetshCommand(
                        $"interface ip set address \"{adapterName}\" static {settings.IpAddress} {settings.SubnetMask} {gateway}");

                    if (!staticResult.Success)
                    {
                        result.Success = false;
                        result.Message = $"Failed to set static IP: {staticResult.Message}";
                        return result;
                    }
                }

                // Configure DNS
                if (settings.UseDhcpDns)
                {
                    var dnsResult = await RunNetshCommand($"interface ip set dns \"{adapterName}\" dhcp");
                    if (!dnsResult.Success)
                    {
                        result.Success = false;
                        result.Message = $"Failed to set DHCP DNS: {dnsResult.Message}";
                        return result;
                    }
                }
                else
                {
                    // Set primary DNS
                    if (!string.IsNullOrEmpty(settings.PrimaryDns))
                    {
                        var dns1Result = await RunNetshCommand(
                            $"interface ip set dns \"{adapterName}\" static {settings.PrimaryDns} primary");
                        if (!dns1Result.Success)
                        {
                            result.Success = false;
                            result.Message = $"Failed to set primary DNS: {dns1Result.Message}";
                            return result;
                        }

                        // Set secondary DNS
                        if (!string.IsNullOrEmpty(settings.SecondaryDns))
                        {
                            var dns2Result = await RunNetshCommand(
                                $"interface ip add dns \"{adapterName}\" {settings.SecondaryDns} index=2");
                            if (!dns2Result.Success)
                            {
                                result.Success = false;
                                result.Message = $"Failed to set secondary DNS: {dns2Result.Message}";
                                return result;
                            }
                        }
                    }
                }

                result.Success = true;
                result.Message = "Network settings applied successfully.";
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Message = $"Error applying network settings: {ex.Message}";
            }

            return result;
        }

        /// <summary>
        /// Runs a netsh command and returns the result
        /// </summary>
        private async Task<OperationResult> RunNetshCommand(string arguments)
        {
            var result = new OperationResult();

            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "netsh",
                    Arguments = arguments,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    Verb = "runas"
                };

                using (var process = new Process { StartInfo = startInfo })
                {
                    process.Start();
                    string output = await process.StandardOutput.ReadToEndAsync();
                    string error = await process.StandardError.ReadToEndAsync();
                    await process.WaitForExitAsync();

                    if (process.ExitCode == 0)
                    {
                        result.Success = true;
                        result.Message = output;
                    }
                    else
                    {
                        result.Success = false;
                        result.Message = string.IsNullOrEmpty(error) ? output : error;
                    }
                }
            }
            catch (Exception ex)
            {
                result.Success = false;
                result.Message = ex.Message;
            }

            return result;
        }
    }

    /// <summary>
    /// Information about a network adapter
    /// </summary>
    public class NetworkAdapterInfo
    {
        public string Name { get; set; } = "";
        public string Description { get; set; } = "";
        public OperationalStatus Status { get; set; }
        public string IpAddress { get; set; } = "";
        public string SubnetMask { get; set; } = "";
        public string Gateway { get; set; } = "";
        public List<string> DnsServers { get; set; } = new List<string>();
        public bool IsDhcpEnabled { get; set; }

        public string StatusText => Status == OperationalStatus.Up ? "Connected" : "Disconnected";
        public bool IsConnected => Status == OperationalStatus.Up;
    }

    /// <summary>
    /// Result of a network operation
    /// </summary>
    public class OperationResult
    {
        public bool Success { get; set; }
        public string Message { get; set; } = "";
    }
}
