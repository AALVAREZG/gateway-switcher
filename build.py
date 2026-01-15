#!/usr/bin/env python3
"""Build script for creating Gateway Switcher executable."""

import subprocess
import sys
from pathlib import Path


def build_executable():
    """Build the standalone executable using PyInstaller."""
    print("Building Gateway Switcher executable...")

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=GatewaySwitcher",
        "--onefile",
        "--windowed",
        "--uac-admin",
        "--add-data=gateway_switcher/resources;gateway_switcher/resources",
        "--hidden-import=PyQt6.sip",
        "--hidden-import=win32api",
        "--hidden-import=win32con",
        "run.py"
    ]

    # Add icon if exists
    icon_path = Path("gateway_switcher/resources/icons/app.ico")
    if icon_path.exists():
        cmd.insert(-1, f"--icon={icon_path}")

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    print("\nBuild complete!")
    print("Executable location: dist/GatewaySwitcher.exe")


if __name__ == "__main__":
    build_executable()
