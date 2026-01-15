using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using GatewaySwitcher.Helpers;
using GatewaySwitcher.Models;
using GatewaySwitcher.Services;

namespace GatewaySwitcher.ViewModels
{
    /// <summary>
    /// Main ViewModel for the application
    /// </summary>
    public class MainViewModel : BaseViewModel
    {
        private readonly ProfileManager _profileManager;
        private readonly NetworkConfigurationService _networkService;

        private ObservableCollection<NetworkProfile> _profiles = new();
        private ObservableCollection<NetworkAdapterInfo> _adapters = new();
        private NetworkProfile? _selectedProfile;
        private NetworkAdapterInfo? _selectedAdapter;
        private string _statusMessage = "";
        private bool _isLoading;

        public MainViewModel()
        {
            _profileManager = new ProfileManager();
            _networkService = new NetworkConfigurationService();

            // Initialize commands
            ApplyProfileCommand = new AsyncRelayCommand(ApplyProfileAsync, _ => SelectedProfile != null && !IsLoading);
            AddProfileCommand = new RelayCommand(_ => AddProfile());
            EditProfileCommand = new RelayCommand(_ => EditSelectedProfile(), _ => SelectedProfile != null);
            DeleteProfileCommand = new AsyncRelayCommand(DeleteProfileAsync, _ => SelectedProfile != null && !SelectedProfile.IsDefault);
            DuplicateProfileCommand = new AsyncRelayCommand(DuplicateProfileAsync, _ => SelectedProfile != null);
            UpdateDefaultCommand = new RelayCommand(_ => UpdateDefaultProfile());
            RefreshAdaptersCommand = new RelayCommand(_ => LoadAdapters());
            ExitCommand = new RelayCommand(_ => Application.Current.Shutdown());

            _profileManager.ProfileApplied += (s, e) => StatusMessage = $"Applied: {e.Profile.Name}";
            _profileManager.ProfilesChanged += (s, e) => RefreshProfiles();
        }

        #region Properties

        public ObservableCollection<NetworkProfile> Profiles
        {
            get => _profiles;
            set => SetProperty(ref _profiles, value);
        }

        public ObservableCollection<NetworkAdapterInfo> Adapters
        {
            get => _adapters;
            set => SetProperty(ref _adapters, value);
        }

        public NetworkProfile? SelectedProfile
        {
            get => _selectedProfile;
            set
            {
                if (SetProperty(ref _selectedProfile, value))
                {
                    CommandManager.InvalidateRequerySuggested();
                }
            }
        }

        public NetworkAdapterInfo? SelectedAdapter
        {
            get => _selectedAdapter;
            set
            {
                if (SetProperty(ref _selectedAdapter, value) && value != null)
                {
                    _profileManager.Collection.Settings.SelectedAdapterName = value.Name;
                    _ = _profileManager.SaveAsync();
                }
            }
        }

        public string StatusMessage
        {
            get => _statusMessage;
            set => SetProperty(ref _statusMessage, value);
        }

        public bool IsLoading
        {
            get => _isLoading;
            set
            {
                if (SetProperty(ref _isLoading, value))
                {
                    CommandManager.InvalidateRequerySuggested();
                }
            }
        }

        public bool IsFirstRun => _profileManager.IsFirstRun;

        #endregion

        #region Commands

        public ICommand ApplyProfileCommand { get; }
        public ICommand AddProfileCommand { get; }
        public ICommand EditProfileCommand { get; }
        public ICommand DeleteProfileCommand { get; }
        public ICommand DuplicateProfileCommand { get; }
        public ICommand UpdateDefaultCommand { get; }
        public ICommand RefreshAdaptersCommand { get; }
        public ICommand ExitCommand { get; }

        #endregion

        #region Events

        public event EventHandler<NetworkProfile>? ProfileEditRequested;
        public event EventHandler? AddProfileRequested;
        public event EventHandler? UpdateDefaultRequested;

        #endregion

        #region Methods

        /// <summary>
        /// Initializes the ViewModel
        /// </summary>
        public async Task InitializeAsync()
        {
            IsLoading = true;
            StatusMessage = "Loading...";

            try
            {
                LoadAdapters();
                await _profileManager.LoadAsync();

                // Handle first run
                if (_profileManager.IsFirstRun && SelectedAdapter != null)
                {
                    await _profileManager.InitializeFirstRunAsync(SelectedAdapter.Name);
                    StatusMessage = "Created default profile from current settings.";
                }

                RefreshProfiles();

                // Select saved adapter
                var savedAdapter = Adapters.FirstOrDefault(a =>
                    a.Name == _profileManager.Collection.Settings.SelectedAdapterName);
                if (savedAdapter != null)
                {
                    SelectedAdapter = savedAdapter;
                }

                // Select active profile
                var activeProfile = _profileManager.GetActiveProfile();
                if (activeProfile != null)
                {
                    SelectedProfile = Profiles.FirstOrDefault(p => p.Id == activeProfile.Id);
                }

                StatusMessage = "Ready";
            }
            catch (Exception ex)
            {
                StatusMessage = $"Error: {ex.Message}";
            }
            finally
            {
                IsLoading = false;
            }
        }

        /// <summary>
        /// Loads available network adapters
        /// </summary>
        private void LoadAdapters()
        {
            var adapters = _networkService.GetNetworkAdapters();
            Adapters = new ObservableCollection<NetworkAdapterInfo>(adapters);

            // Auto-select first connected adapter
            if (SelectedAdapter == null)
            {
                SelectedAdapter = Adapters.FirstOrDefault(a => a.IsConnected) ?? Adapters.FirstOrDefault();
            }
        }

        /// <summary>
        /// Refreshes the profiles list
        /// </summary>
        private void RefreshProfiles()
        {
            Profiles = new ObservableCollection<NetworkProfile>(_profileManager.Collection.Profiles);
        }

        /// <summary>
        /// Applies the selected profile
        /// </summary>
        private async Task ApplyProfileAsync(object? parameter)
        {
            if (SelectedProfile == null) return;

            IsLoading = true;
            StatusMessage = $"Applying {SelectedProfile.Name}...";

            try
            {
                // Ensure adapter is set
                if (string.IsNullOrEmpty(SelectedProfile.NetworkSettings.AdapterName) && SelectedAdapter != null)
                {
                    SelectedProfile.NetworkSettings.AdapterName = SelectedAdapter.Name;
                }

                var result = await _profileManager.ApplyProfileAsync(SelectedProfile.Id);
                StatusMessage = result.Message;

                if (!result.Success)
                {
                    MessageBox.Show(result.Message, "Apply Profile", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
            catch (Exception ex)
            {
                StatusMessage = $"Error: {ex.Message}";
                MessageBox.Show($"Failed to apply profile: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                IsLoading = false;
            }
        }

        /// <summary>
        /// Opens the add profile dialog
        /// </summary>
        private void AddProfile()
        {
            AddProfileRequested?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Opens the edit profile dialog
        /// </summary>
        private void EditSelectedProfile()
        {
            if (SelectedProfile != null)
            {
                ProfileEditRequested?.Invoke(this, SelectedProfile);
            }
        }

        /// <summary>
        /// Deletes the selected profile
        /// </summary>
        private async Task DeleteProfileAsync(object? parameter)
        {
            if (SelectedProfile == null || SelectedProfile.IsDefault) return;

            var result = MessageBox.Show(
                $"Are you sure you want to delete the profile '{SelectedProfile.Name}'?",
                "Confirm Delete",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (result == MessageBoxResult.Yes)
            {
                await _profileManager.DeleteProfileAsync(SelectedProfile.Id);
                RefreshProfiles();
                StatusMessage = "Profile deleted.";
            }
        }

        /// <summary>
        /// Duplicates the selected profile
        /// </summary>
        private async Task DuplicateProfileAsync(object? parameter)
        {
            if (SelectedProfile == null) return;

            var clone = await _profileManager.DuplicateProfileAsync(SelectedProfile.Id);
            RefreshProfiles();
            SelectedProfile = Profiles.FirstOrDefault(p => p.Id == clone.Id);
            StatusMessage = $"Created copy: {clone.Name}";
        }

        /// <summary>
        /// Opens the update default profile dialog
        /// </summary>
        private void UpdateDefaultProfile()
        {
            UpdateDefaultRequested?.Invoke(this, EventArgs.Empty);
        }

        /// <summary>
        /// Updates default profile with password verification
        /// </summary>
        public async Task<OperationResult> UpdateDefaultProfileWithPasswordAsync(string password)
        {
            if (SelectedAdapter == null)
            {
                return new OperationResult { Success = false, Message = "No adapter selected." };
            }

            return await _profileManager.UpdateDefaultProfileAsync(password, SelectedAdapter.Name);
        }

        /// <summary>
        /// Saves a new or updated profile
        /// </summary>
        public async Task SaveProfileAsync(NetworkProfile profile, bool isNew)
        {
            if (SelectedAdapter != null)
            {
                profile.NetworkSettings.AdapterName = SelectedAdapter.Name;
            }

            if (isNew)
            {
                await _profileManager.AddProfileAsync(profile);
            }
            else
            {
                await _profileManager.UpdateProfileAsync(profile);
            }

            RefreshProfiles();
            SelectedProfile = Profiles.FirstOrDefault(p => p.Id == profile.Id);
        }

        #endregion
    }
}
