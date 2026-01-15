using System;
using System.Linq;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using GatewaySwitcher.Helpers;
using GatewaySwitcher.Services;
using GatewaySwitcher.Views;
using Hardcodet.Wpf.TaskbarNotification;

namespace GatewaySwitcher
{
    /// <summary>
    /// Application entry point with system tray support
    /// </summary>
    public partial class App : Application
    {
        private TaskbarIcon? _notifyIcon;
        private MainWindow? _mainWindow;
        private static Mutex? _mutex;
        private ProfileManager? _profileManager;

        protected override async void OnStartup(StartupEventArgs e)
        {
            // Ensure single instance
            const string mutexName = "GatewaySwitcher_SingleInstance";
            _mutex = new Mutex(true, mutexName, out bool createdNew);

            if (!createdNew)
            {
                MessageBox.Show("Gateway Switcher is already running.\nCheck the system tray.", "Gateway Switcher",
                    MessageBoxButton.OK, MessageBoxImage.Information);
                Current.Shutdown();
                return;
            }

            base.OnStartup(e);

            // Initialize profile manager
            _profileManager = new ProfileManager();
            await _profileManager.LoadAsync();

            // Create and configure system tray icon
            _notifyIcon = CreateNotifyIcon();
            ConfigureNotifyIcon();

            // Create main window
            _mainWindow = new MainWindow();

            // Check if started minimized
            bool startMinimized = e.Args.Length > 0 && e.Args[0] == "--minimized";

            if (!startMinimized)
            {
                _mainWindow.Show();
            }
            else
            {
                _notifyIcon?.ShowBalloonTip("Gateway Switcher", "Running in system tray.", BalloonIcon.Info);
            }
        }

        private TaskbarIcon CreateNotifyIcon()
        {
            TaskbarIcon? notifyIcon = null;

            try
            {
                // Try to get the XAML-defined icon first
                notifyIcon = (TaskbarIcon)FindResource("NotifyIcon");
            }
            catch
            {
                // Create icon programmatically if XAML resource fails
            }

            if (notifyIcon == null)
            {
                notifyIcon = new TaskbarIcon
                {
                    ToolTipText = "Gateway Switcher"
                };
            }

            // Set icon using helper (works even if resource icons are missing)
            try
            {
                var icon = IconHelper.CreateAppIcon();
                notifyIcon.Icon = icon;
            }
            catch
            {
                // Icon creation failed, continue without custom icon
            }

            return notifyIcon;
        }

        private void ConfigureNotifyIcon()
        {
            if (_notifyIcon == null) return;

            // Double-click to open
            _notifyIcon.TrayMouseDoubleClick += (s, e) => ShowMainWindow();

            // Create context menu
            var contextMenu = new ContextMenu();

            // Open menu item
            var openItem = new MenuItem { Header = "Open Gateway Switcher", FontWeight = FontWeights.Bold };
            openItem.Click += (s, e) => ShowMainWindow();
            contextMenu.Items.Add(openItem);

            contextMenu.Items.Add(new Separator());

            // Profiles submenu
            var profilesItem = new MenuItem { Header = "Switch Profile" };
            UpdateProfilesMenu(profilesItem);
            contextMenu.Items.Add(profilesItem);

            // Subscribe to profile changes
            if (_profileManager != null)
            {
                _profileManager.ProfilesChanged += (s, e) => UpdateProfilesMenu(profilesItem);
            }

            contextMenu.Items.Add(new Separator());

            // Exit menu item
            var exitItem = new MenuItem { Header = "Exit" };
            exitItem.Click += (s, e) => ExitApplication();
            contextMenu.Items.Add(exitItem);

            _notifyIcon.ContextMenu = contextMenu;
        }

        private void UpdateProfilesMenu(MenuItem profilesMenuItem)
        {
            if (_profileManager == null) return;

            profilesMenuItem.Items.Clear();

            foreach (var profile in _profileManager.Collection.Profiles)
            {
                var item = new MenuItem
                {
                    Header = profile.Name,
                    IsChecked = profile.Id == _profileManager.Collection.ActiveProfileId,
                    Tag = profile.Id
                };
                item.Click += async (s, e) =>
                {
                    if (s is MenuItem mi && mi.Tag is string profileId)
                    {
                        var result = await _profileManager.ApplyProfileAsync(profileId);
                        _notifyIcon?.ShowBalloonTip(
                            "Gateway Switcher",
                            result.Message,
                            result.Success ? BalloonIcon.Info : BalloonIcon.Warning);

                        // Refresh menu
                        UpdateProfilesMenu(profilesMenuItem);

                        // Refresh main window if open
                        if (_mainWindow?.IsVisible == true)
                        {
                            await _mainWindow.RefreshAsync();
                        }
                    }
                };
                profilesMenuItem.Items.Add(item);
            }

            if (!profilesMenuItem.Items.Cast<object>().Any())
            {
                profilesMenuItem.Items.Add(new MenuItem { Header = "(No profiles)", IsEnabled = false });
            }
        }

        protected override void OnExit(ExitEventArgs e)
        {
            _notifyIcon?.Dispose();
            _mutex?.ReleaseMutex();
            _mutex?.Dispose();
            base.OnExit(e);
        }

        public void ShowMainWindow()
        {
            if (_mainWindow == null)
            {
                _mainWindow = new MainWindow();
            }

            _mainWindow.Show();
            _mainWindow.WindowState = WindowState.Normal;
            _mainWindow.Activate();
        }

        public void HideMainWindow()
        {
            _mainWindow?.Hide();
        }

        public void ExitApplication()
        {
            _notifyIcon?.Dispose();
            Current.Shutdown();
        }

        public void ShowNotification(string title, string message, bool isError = false)
        {
            _notifyIcon?.ShowBalloonTip(title, message, isError ? BalloonIcon.Error : BalloonIcon.Info);
        }
    }
}
