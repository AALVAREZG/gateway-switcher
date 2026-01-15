using System;
using Newtonsoft.Json;

namespace GatewaySwitcher.Models
{
    /// <summary>
    /// Represents a complete network configuration profile
    /// </summary>
    public class NetworkProfile
    {
        [JsonProperty("id")]
        public string Id { get; set; } = Guid.NewGuid().ToString();

        [JsonProperty("name")]
        public string Name { get; set; } = "New Profile";

        [JsonProperty("isDefault")]
        public bool IsDefault { get; set; }

        [JsonProperty("createdAt")]
        public DateTime CreatedAt { get; set; } = DateTime.Now;

        [JsonProperty("lastModified")]
        public DateTime LastModified { get; set; } = DateTime.Now;

        [JsonProperty("networkSettings")]
        public NetworkSettings NetworkSettings { get; set; } = new NetworkSettings();

        [JsonProperty("proxySettings")]
        public ProxySettings ProxySettings { get; set; } = new ProxySettings();

        public NetworkProfile Clone()
        {
            return new NetworkProfile
            {
                Id = Guid.NewGuid().ToString(),
                Name = this.Name + " (Copy)",
                IsDefault = false,
                CreatedAt = DateTime.Now,
                LastModified = DateTime.Now,
                NetworkSettings = this.NetworkSettings.Clone(),
                ProxySettings = this.ProxySettings.Clone()
            };
        }
    }

    /// <summary>
    /// Network adapter configuration settings
    /// </summary>
    public class NetworkSettings
    {
        [JsonProperty("useDhcp")]
        public bool UseDhcp { get; set; } = true;

        [JsonProperty("ipAddress")]
        public string IpAddress { get; set; } = "";

        [JsonProperty("subnetMask")]
        public string SubnetMask { get; set; } = "255.255.255.0";

        [JsonProperty("gateway")]
        public string Gateway { get; set; } = "";

        [JsonProperty("useDhcpDns")]
        public bool UseDhcpDns { get; set; } = true;

        [JsonProperty("primaryDns")]
        public string PrimaryDns { get; set; } = "";

        [JsonProperty("secondaryDns")]
        public string SecondaryDns { get; set; } = "";

        [JsonProperty("adapterName")]
        public string AdapterName { get; set; } = "";

        public NetworkSettings Clone()
        {
            return new NetworkSettings
            {
                UseDhcp = this.UseDhcp,
                IpAddress = this.IpAddress,
                SubnetMask = this.SubnetMask,
                Gateway = this.Gateway,
                UseDhcpDns = this.UseDhcpDns,
                PrimaryDns = this.PrimaryDns,
                SecondaryDns = this.SecondaryDns,
                AdapterName = this.AdapterName
            };
        }
    }

    /// <summary>
    /// Proxy configuration settings
    /// </summary>
    public class ProxySettings
    {
        [JsonProperty("enabled")]
        public bool Enabled { get; set; }

        [JsonProperty("proxyServer")]
        public string ProxyServer { get; set; } = "";

        [JsonProperty("proxyPort")]
        public int ProxyPort { get; set; } = 8080;

        [JsonProperty("useAuthentication")]
        public bool UseAuthentication { get; set; }

        [JsonProperty("username")]
        public string Username { get; set; } = "";

        [JsonProperty("password")]
        public string Password { get; set; } = "";

        [JsonProperty("bypassList")]
        public string BypassList { get; set; } = "localhost;127.0.0.1";

        [JsonProperty("bypassLocal")]
        public bool BypassLocal { get; set; } = true;

        public string FullProxyAddress => string.IsNullOrEmpty(ProxyServer) ? "" : $"{ProxyServer}:{ProxyPort}";

        public ProxySettings Clone()
        {
            return new ProxySettings
            {
                Enabled = this.Enabled,
                ProxyServer = this.ProxyServer,
                ProxyPort = this.ProxyPort,
                UseAuthentication = this.UseAuthentication,
                Username = this.Username,
                Password = this.Password,
                BypassList = this.BypassList,
                BypassLocal = this.BypassLocal
            };
        }
    }
}
