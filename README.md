# Gateway Switcher

A Windows 10/11 application for easily switching between network gateway profiles. Manage multiple network configurations including IP addresses, gateways, DNS servers, and proxy settings with a single click.

**Built with Python and PyQt6 for a modern, responsive UI.**

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
- Python 3.10 or later
- Administrator privileges (required for changing network settings)

## Installation

### Option 1: Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/AALVAREZG/gateway-switcher.git
   cd gateway-switcher
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python run.py
   ```

### Option 2: Build Standalone Executable

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   python build.py
   ```

3. The executable will be in:
   ```
   dist/GatewaySwitcher.exe
   ```

### Option 3: Install as Package

```bash
pip install .
gateway-switcher
```

## Usage

### First Run

1. Launch the application (requires Administrator privileges)
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
2. Click **Apply Selected Profile** or double-click the profile

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
gateway_switcher/
├── models/
│   ├── __init__.py
│   └── profile.py           # NetworkProfile, ProxySettings dataclasses
├── services/
│   ├── __init__.py
│   ├── network_service.py   # IP/Gateway/DNS management via netsh
│   ├── proxy_service.py     # Proxy settings via Windows Registry
│   └── profile_manager.py   # Profile CRUD operations
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Main application window
│   ├── profile_editor.py    # Profile editor dialog
│   ├── password_dialog.py   # Password confirmation dialog
│   ├── system_tray.py       # System tray icon and menu
│   └── styles.py            # Application styling
├── utils/
│   ├── __init__.py
│   └── admin.py             # Administrator privilege utilities
├── resources/
│   └── icons/               # Application icons
├── __init__.py
└── main.py                  # Application entry point
```

## Configuration Storage

Profiles are stored in:
```
%LOCALAPPDATA%\GatewaySwitcher\profiles.json
```

## Technical Details

- **Language**: Python 3.10+
- **UI Framework**: PyQt6
- **Network Configuration**: Uses `netsh` commands for IP/DNS changes
- **Proxy Settings**: Uses Windows Registry (`winreg`)
- **Windows API**: pywin32 for admin elevation and API calls
- **Data Models**: Python dataclasses with JSON serialization

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt6 | >=6.6.0 | Modern Qt-based UI framework |
| pywin32 | >=306 | Windows API access |

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
- The app will prompt for elevation on startup

### Changes not taking effect
- Some network changes may require a network adapter restart
- Try disabling and re-enabling your network adapter

### Proxy not working in all applications
- Some applications don't respect system proxy settings
- Authentication credentials may need to be entered in specific applications

### PyQt6 installation issues
If you encounter issues installing PyQt6:
```bash
pip install --upgrade pip
pip install PyQt6
```

### pywin32 installation issues
```bash
pip install pywin32
python -c "import win32api"  # Test installation
```
