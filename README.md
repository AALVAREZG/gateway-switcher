# Gateway Switcher

A Windows 10/11 application for easily switching between network gateway profiles. Manage multiple network configurations including IP addresses, gateways, DNS servers, and proxy settings with a single click.

## Features

- **Multiple Network Profiles**: Store and manage multiple network configurations
- **Quick Profile Switching**: Switch between profiles from the system tray
- **Comprehensive Network Settings**:
  - IP Address (Static or DHCP)
  - Subnet Mask
  - Default Gateway
  - DNS Servers (Primary & Secondary)
- **Proxy Configuration**:
  - Enable/Disable proxy
  - Proxy server and port
  - Authentication support (username/password)
  - Bypass list for local addresses
- **System Tray Integration**: Runs in the background with easy access
- **First-Run Setup**: Automatically captures current network settings as the default profile
- **Password-Protected Default Profile**: Update the default profile with password confirmation (ca26)

## Requirements

- Windows 10 or Windows 11
- .NET 6.0 Runtime or later
- Administrator privileges (required for changing network settings)

## Installation

### Build from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/gateway-switcher.git
   cd gateway-switcher
   ```

2. Build the solution:
   ```bash
   dotnet build GatewaySwitcher.sln -c Release
   ```

3. The executable will be in:
   ```
   GatewaySwitcher/bin/Release/net6.0-windows/
   ```

### Generate Application Icons (Optional)

Run the PowerShell script to generate custom icons:
```powershell
cd GatewaySwitcher/Resources
.\IconGenerator.ps1
```

## Usage

### First Run

1. Launch `GatewaySwitcher.exe` (requires Administrator privileges)
2. Select your network adapter from the dropdown
3. The app will automatically create a "Default" profile with your current network settings

### Creating Profiles

1. Click **+ Add** to create a new profile
2. Enter a profile name
3. Configure network settings:
   - Enable DHCP or set static IP, subnet mask, and gateway
   - Configure DNS servers (auto or manual)
4. Configure proxy settings if needed
5. Click **Save Profile**

### Switching Profiles

**From Main Window:**
1. Select a profile from the list
2. Click **Apply Selected Profile**

**From System Tray:**
1. Right-click the tray icon
2. Go to **Switch Profile**
3. Select the desired profile

### Updating Default Profile

To update the default profile with current system settings:
1. Click **Update Default** in the main window
2. Enter the password: `ca26`
3. Confirm to save current settings to the default profile

### System Tray

- **Double-click** the tray icon to open the main window
- **Right-click** for quick access menu:
  - Open Gateway Switcher
  - Switch Profile (submenu with all profiles)
  - Exit

## Project Structure

```
GatewaySwitcher/
├── Models/
│   ├── NetworkProfile.cs      # Profile data model
│   └── ProfileCollection.cs   # Collection of profiles
├── Services/
│   ├── NetworkConfigurationService.cs  # IP/Gateway/DNS management
│   ├── ProxyConfigurationService.cs    # Proxy settings management
│   └── ProfileManager.cs               # Profile CRUD operations
├── ViewModels/
│   ├── BaseViewModel.cs       # MVVM base class
│   └── MainViewModel.cs       # Main window logic
├── Views/
│   ├── MainWindow.xaml/.cs           # Main application window
│   ├── ProfileEditorWindow.xaml/.cs  # Profile editor dialog
│   └── PasswordDialog.xaml/.cs       # Password confirmation dialog
├── Helpers/
│   ├── Converters.cs          # XAML value converters
│   ├── RelayCommand.cs        # ICommand implementations
│   └── IconHelper.cs          # Icon generation utilities
├── Resources/
│   └── IconGenerator.ps1      # PowerShell script for icons
├── App.xaml/.cs               # Application entry point
├── app.manifest               # UAC administrator manifest
└── GatewaySwitcher.csproj     # Project file
```

## Configuration Storage

Profiles are stored in:
```
%LOCALAPPDATA%\GatewaySwitcher\profiles.json
```

## Technical Details

- **Framework**: .NET 6.0 with WPF
- **Network Configuration**: Uses `netsh` commands for IP/DNS changes
- **Proxy Settings**: Uses Windows Registry (Internet Settings)
- **System Tray**: Hardcodet.NotifyIcon.Wpf library
- **JSON Serialization**: Newtonsoft.Json

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

### "Access Denied" when applying profiles
- Ensure you're running the application as Administrator
- The app.manifest requires admin privileges, but you may need to right-click and "Run as Administrator"

### Changes not taking effect
- Some network changes may require a network adapter restart
- Try disabling and re-enabling your network adapter

### Proxy not working in all applications
- Some applications don't respect system proxy settings
- Authentication credentials may need to be entered in specific applications
