using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using GatewaySwitcher.Models;
using Newtonsoft.Json;

namespace GatewaySwitcher.Services
{
    /// <summary>
    /// Service for managing network profiles (load, save, CRUD operations)
    /// </summary>
    public class ProfileManager
    {
        private readonly string _configPath;
        private ProfileCollection _collection;
        private readonly NetworkConfigurationService _networkService;
        private readonly ProxyConfigurationService _proxyService;

        public event EventHandler<ProfileEventArgs>? ProfileApplied;
        public event EventHandler? ProfilesChanged;

        public ProfileManager()
        {
            string appDataPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "GatewaySwitcher");

            if (!Directory.Exists(appDataPath))
            {
                Directory.CreateDirectory(appDataPath);
            }

            _configPath = Path.Combine(appDataPath, "profiles.json");
            _collection = new ProfileCollection();
            _networkService = new NetworkConfigurationService();
            _proxyService = new ProxyConfigurationService();
        }

        public ProfileCollection Collection => _collection;
        public bool IsFirstRun => !_collection.Settings.FirstRunCompleted;

        /// <summary>
        /// Loads profiles from disk
        /// </summary>
        public async Task LoadAsync()
        {
            try
            {
                if (File.Exists(_configPath))
                {
                    string json = await File.ReadAllTextAsync(_configPath);
                    _collection = JsonConvert.DeserializeObject<ProfileCollection>(json) ?? new ProfileCollection();
                }
                else
                {
                    _collection = new ProfileCollection();
                }
            }
            catch (Exception)
            {
                _collection = new ProfileCollection();
            }
        }

        /// <summary>
        /// Saves profiles to disk
        /// </summary>
        public async Task SaveAsync()
        {
            try
            {
                string json = JsonConvert.SerializeObject(_collection, Formatting.Indented);
                await File.WriteAllTextAsync(_configPath, json);
                ProfilesChanged?.Invoke(this, EventArgs.Empty);
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to save profiles: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Creates a default profile from current system settings
        /// </summary>
        public NetworkProfile CreateDefaultProfileFromSystem(string adapterName)
        {
            var networkSettings = _networkService.GetCurrentSettings(adapterName);
            var proxySettings = _proxyService.GetCurrentSettings();

            var profile = new NetworkProfile
            {
                Name = "Default (Current Settings)",
                IsDefault = true,
                NetworkSettings = networkSettings,
                ProxySettings = proxySettings
            };

            return profile;
        }

        /// <summary>
        /// Initializes the application on first run
        /// </summary>
        public async Task<NetworkProfile?> InitializeFirstRunAsync(string adapterName)
        {
            if (_collection.Settings.FirstRunCompleted)
                return null;

            var defaultProfile = CreateDefaultProfileFromSystem(adapterName);
            _collection.Profiles.Add(defaultProfile);
            _collection.ActiveProfileId = defaultProfile.Id;
            _collection.Settings.SelectedAdapterName = adapterName;
            _collection.Settings.FirstRunCompleted = true;

            await SaveAsync();
            return defaultProfile;
        }

        /// <summary>
        /// Updates the default profile with current system settings (requires password)
        /// </summary>
        public async Task<OperationResult> UpdateDefaultProfileAsync(string password, string adapterName)
        {
            const string REQUIRED_PASSWORD = "ca26";

            if (password != REQUIRED_PASSWORD)
            {
                return new OperationResult
                {
                    Success = false,
                    Message = "Invalid password. Default profile update denied."
                };
            }

            var defaultProfile = _collection.Profiles.FirstOrDefault(p => p.IsDefault);
            if (defaultProfile == null)
            {
                return new OperationResult
                {
                    Success = false,
                    Message = "No default profile found."
                };
            }

            defaultProfile.NetworkSettings = _networkService.GetCurrentSettings(adapterName);
            defaultProfile.ProxySettings = _proxyService.GetCurrentSettings();
            defaultProfile.LastModified = DateTime.Now;

            await SaveAsync();

            return new OperationResult
            {
                Success = true,
                Message = "Default profile updated with current system settings."
            };
        }

        /// <summary>
        /// Adds a new profile
        /// </summary>
        public async Task<NetworkProfile> AddProfileAsync(NetworkProfile profile)
        {
            _collection.Profiles.Add(profile);
            await SaveAsync();
            return profile;
        }

        /// <summary>
        /// Updates an existing profile
        /// </summary>
        public async Task UpdateProfileAsync(NetworkProfile profile)
        {
            var existing = _collection.Profiles.FirstOrDefault(p => p.Id == profile.Id);
            if (existing != null)
            {
                int index = _collection.Profiles.IndexOf(existing);
                profile.LastModified = DateTime.Now;
                _collection.Profiles[index] = profile;
                await SaveAsync();
            }
        }

        /// <summary>
        /// Deletes a profile
        /// </summary>
        public async Task<bool> DeleteProfileAsync(string profileId)
        {
            var profile = _collection.Profiles.FirstOrDefault(p => p.Id == profileId);
            if (profile == null)
                return false;

            // Prevent deleting default profile
            if (profile.IsDefault)
                return false;

            _collection.Profiles.Remove(profile);

            // Clear active profile if deleted
            if (_collection.ActiveProfileId == profileId)
            {
                _collection.ActiveProfileId = _collection.Profiles.FirstOrDefault()?.Id;
            }

            await SaveAsync();
            return true;
        }

        /// <summary>
        /// Gets a profile by ID
        /// </summary>
        public NetworkProfile? GetProfile(string profileId)
        {
            return _collection.Profiles.FirstOrDefault(p => p.Id == profileId);
        }

        /// <summary>
        /// Gets the currently active profile
        /// </summary>
        public NetworkProfile? GetActiveProfile()
        {
            if (string.IsNullOrEmpty(_collection.ActiveProfileId))
                return null;

            return _collection.Profiles.FirstOrDefault(p => p.Id == _collection.ActiveProfileId);
        }

        /// <summary>
        /// Applies a profile to the system
        /// </summary>
        public async Task<OperationResult> ApplyProfileAsync(string profileId)
        {
            var profile = GetProfile(profileId);
            if (profile == null)
            {
                return new OperationResult
                {
                    Success = false,
                    Message = "Profile not found."
                };
            }

            // Set adapter name if not already set
            if (string.IsNullOrEmpty(profile.NetworkSettings.AdapterName))
            {
                profile.NetworkSettings.AdapterName = _collection.Settings.SelectedAdapterName;
            }

            // Apply network settings
            var networkResult = await _networkService.ApplyNetworkSettings(profile.NetworkSettings);
            if (!networkResult.Success)
            {
                return networkResult;
            }

            // Apply proxy settings
            var proxyResult = _proxyService.ApplyProxySettings(profile.ProxySettings);
            if (!proxyResult.Success)
            {
                return new OperationResult
                {
                    Success = false,
                    Message = $"Network settings applied but proxy failed: {proxyResult.Message}"
                };
            }

            // Update active profile
            _collection.ActiveProfileId = profileId;
            await SaveAsync();

            ProfileApplied?.Invoke(this, new ProfileEventArgs(profile));

            return new OperationResult
            {
                Success = true,
                Message = $"Profile '{profile.Name}' applied successfully."
            };
        }

        /// <summary>
        /// Duplicates a profile
        /// </summary>
        public async Task<NetworkProfile> DuplicateProfileAsync(string profileId)
        {
            var original = GetProfile(profileId);
            if (original == null)
                throw new Exception("Profile not found.");

            var clone = original.Clone();
            await AddProfileAsync(clone);
            return clone;
        }
    }

    public class ProfileEventArgs : EventArgs
    {
        public NetworkProfile Profile { get; }

        public ProfileEventArgs(NetworkProfile profile)
        {
            Profile = profile;
        }
    }
}
