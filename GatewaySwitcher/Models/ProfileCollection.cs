using System.Collections.Generic;
using Newtonsoft.Json;

namespace GatewaySwitcher.Models
{
    /// <summary>
    /// Container for all network profiles and application settings
    /// </summary>
    public class ProfileCollection
    {
        [JsonProperty("version")]
        public string Version { get; set; } = "1.0";

        [JsonProperty("activeProfileId")]
        public string? ActiveProfileId { get; set; }

        [JsonProperty("profiles")]
        public List<NetworkProfile> Profiles { get; set; } = new List<NetworkProfile>();

        [JsonProperty("settings")]
        public AppSettings Settings { get; set; } = new AppSettings();
    }

    /// <summary>
    /// Application-wide settings
    /// </summary>
    public class AppSettings
    {
        [JsonProperty("startWithWindows")]
        public bool StartWithWindows { get; set; }

        [JsonProperty("startMinimized")]
        public bool StartMinimized { get; set; } = true;

        [JsonProperty("showNotifications")]
        public bool ShowNotifications { get; set; } = true;

        [JsonProperty("selectedAdapterName")]
        public string SelectedAdapterName { get; set; } = "";

        [JsonProperty("firstRunCompleted")]
        public bool FirstRunCompleted { get; set; }
    }
}
