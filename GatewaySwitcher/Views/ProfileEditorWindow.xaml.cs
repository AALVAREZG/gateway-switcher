using System.Windows;
using GatewaySwitcher.Models;

namespace GatewaySwitcher.Views
{
    /// <summary>
    /// Dialog for editing network profile settings
    /// </summary>
    public partial class ProfileEditorWindow : Window
    {
        public NetworkProfile Profile { get; private set; }
        private readonly bool _isNew;

        public ProfileEditorWindow(NetworkProfile profile, bool isNew)
        {
            InitializeComponent();

            _isNew = isNew;

            // Clone the profile for editing
            Profile = new NetworkProfile
            {
                Id = profile.Id,
                Name = profile.Name,
                IsDefault = profile.IsDefault,
                CreatedAt = profile.CreatedAt,
                LastModified = profile.LastModified,
                NetworkSettings = profile.NetworkSettings.Clone(),
                ProxySettings = profile.ProxySettings.Clone()
            };

            DataContext = Profile;

            // Set title based on mode
            TitleText.Text = isNew ? "Create New Profile" : "Edit Profile";
            Title = isNew ? "Create Profile" : "Edit Profile";

            // Set proxy password if exists
            if (!string.IsNullOrEmpty(Profile.ProxySettings.Password))
            {
                ProxyPasswordBox.Password = Profile.ProxySettings.Password;
            }

            // Focus on name field
            Loaded += (s, e) =>
            {
                ProfileNameTextBox.Focus();
                ProfileNameTextBox.SelectAll();
            };
        }

        private void Save_Click(object sender, RoutedEventArgs e)
        {
            // Validate
            if (string.IsNullOrWhiteSpace(Profile.Name))
            {
                MessageBox.Show("Please enter a profile name.", "Validation Error",
                    MessageBoxButton.OK, MessageBoxImage.Warning);
                ProfileNameTextBox.Focus();
                return;
            }

            // Validate IP settings if not using DHCP
            if (!Profile.NetworkSettings.UseDhcp)
            {
                if (string.IsNullOrWhiteSpace(Profile.NetworkSettings.IpAddress))
                {
                    MessageBox.Show("Please enter an IP address or enable DHCP.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                if (!IsValidIpAddress(Profile.NetworkSettings.IpAddress))
                {
                    MessageBox.Show("Please enter a valid IP address.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                if (!string.IsNullOrEmpty(Profile.NetworkSettings.SubnetMask) &&
                    !IsValidIpAddress(Profile.NetworkSettings.SubnetMask))
                {
                    MessageBox.Show("Please enter a valid subnet mask.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                if (!string.IsNullOrEmpty(Profile.NetworkSettings.Gateway) &&
                    !IsValidIpAddress(Profile.NetworkSettings.Gateway))
                {
                    MessageBox.Show("Please enter a valid gateway address.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            // Validate DNS if not using DHCP DNS
            if (!Profile.NetworkSettings.UseDhcpDns)
            {
                if (!string.IsNullOrEmpty(Profile.NetworkSettings.PrimaryDns) &&
                    !IsValidIpAddress(Profile.NetworkSettings.PrimaryDns))
                {
                    MessageBox.Show("Please enter a valid primary DNS address.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                if (!string.IsNullOrEmpty(Profile.NetworkSettings.SecondaryDns) &&
                    !IsValidIpAddress(Profile.NetworkSettings.SecondaryDns))
                {
                    MessageBox.Show("Please enter a valid secondary DNS address.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            // Validate proxy settings if enabled
            if (Profile.ProxySettings.Enabled)
            {
                if (string.IsNullOrWhiteSpace(Profile.ProxySettings.ProxyServer))
                {
                    MessageBox.Show("Please enter a proxy server address.", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                if (Profile.ProxySettings.ProxyPort <= 0 || Profile.ProxySettings.ProxyPort > 65535)
                {
                    MessageBox.Show("Please enter a valid port number (1-65535).", "Validation Error",
                        MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }

                // Save proxy password
                Profile.ProxySettings.Password = ProxyPasswordBox.Password;
            }

            DialogResult = true;
            Close();
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private bool IsValidIpAddress(string ipAddress)
        {
            if (string.IsNullOrWhiteSpace(ipAddress))
                return false;

            return System.Net.IPAddress.TryParse(ipAddress, out _);
        }
    }
}
