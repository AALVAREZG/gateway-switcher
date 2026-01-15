"""Administrator privilege utilities."""

import ctypes
import sys
import os


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin() -> bool:
    """
    Re-launch the current script with administrator privileges.
    Returns True if elevation was requested, False otherwise.
    """
    if is_admin():
        return False

    try:
        # Get the current script path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script = sys.executable
            params = " ".join(sys.argv[1:])
        else:
            # Running as Python script
            script = sys.executable
            params = f'"{sys.argv[0]}" ' + " ".join(sys.argv[1:])

        # Request elevation
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            script,
            params,
            None,
            1  # SW_SHOWNORMAL
        )

        # If return value is greater than 32, elevation was successful
        return ret > 32

    except Exception as e:
        print(f"Failed to elevate: {e}")
        return False


def require_admin() -> None:
    """Ensure the application is running with admin privileges."""
    if not is_admin():
        if run_as_admin():
            # Elevation requested, exit current process
            sys.exit(0)
        else:
            # Elevation failed or was cancelled
            print("Administrator privileges are required to change network settings.")
            sys.exit(1)
