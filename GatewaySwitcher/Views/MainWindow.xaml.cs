using System;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using GatewaySwitcher.Models;
using GatewaySwitcher.ViewModels;

namespace GatewaySwitcher.Views
{
    /// <summary>
    /// Main application window
    /// </summary>
    public partial class MainWindow : Window
    {
        private readonly MainViewModel _viewModel;

        public MainWindow()
        {
            InitializeComponent();

            _viewModel = new MainViewModel();
            DataContext = _viewModel;

            // Subscribe to events
            _viewModel.ProfileEditRequested += OnProfileEditRequested;
            _viewModel.AddProfileRequested += OnAddProfileRequested;
            _viewModel.UpdateDefaultRequested += OnUpdateDefaultRequested;

            Loaded += MainWindow_Loaded;
        }

        private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            await _viewModel.InitializeAsync();
        }

        public async Task RefreshAsync()
        {
            await _viewModel.InitializeAsync();
        }

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            // Minimize to tray instead of closing
            e.Cancel = true;
            Hide();

            ((App)Application.Current).ShowNotification(
                "Gateway Switcher",
                "Running in system tray. Double-click to open.");
        }

        private void MinimizeToTray_Click(object sender, RoutedEventArgs e)
        {
            Hide();
            ((App)Application.Current).ShowNotification(
                "Gateway Switcher",
                "Running in system tray. Double-click to open.");
        }

        private void EditProfile_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is string profileId)
            {
                var profile = _viewModel.Profiles.FirstOrDefault(p => p.Id == profileId);
                if (profile != null)
                {
                    _viewModel.SelectedProfile = profile;
                    ShowProfileEditor(profile, false);
                }
            }
        }

        private void OnProfileEditRequested(object? sender, NetworkProfile profile)
        {
            ShowProfileEditor(profile, false);
        }

        private void OnAddProfileRequested(object? sender, EventArgs e)
        {
            var newProfile = new NetworkProfile { Name = "New Profile" };
            ShowProfileEditor(newProfile, true);
        }

        private void OnUpdateDefaultRequested(object? sender, EventArgs e)
        {
            ShowPasswordDialog();
        }

        private void ShowProfileEditor(NetworkProfile profile, bool isNew)
        {
            var editor = new ProfileEditorWindow(profile, isNew)
            {
                Owner = this
            };

            if (editor.ShowDialog() == true)
            {
                _ = _viewModel.SaveProfileAsync(editor.Profile, isNew);
            }
        }

        private async void ShowPasswordDialog()
        {
            var dialog = new PasswordDialog
            {
                Owner = this
            };

            if (dialog.ShowDialog() == true)
            {
                var result = await _viewModel.UpdateDefaultProfileWithPasswordAsync(dialog.Password);
                MessageBox.Show(result.Message,
                    result.Success ? "Success" : "Error",
                    MessageBoxButton.OK,
                    result.Success ? MessageBoxImage.Information : MessageBoxImage.Warning);

                if (result.Success)
                {
                    await _viewModel.InitializeAsync();
                }
            }
        }
    }
}
