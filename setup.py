"""Setup script for Gateway Switcher."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gateway-switcher",
    version="1.0.0",
    author="Gateway Switcher Team",
    description="Network profile and gateway switcher for Windows 10/11",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AALVAREZG/gateway-switcher",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.6.0",
        "pywin32>=306",
    ],
    entry_points={
        "console_scripts": [
            "gateway-switcher=gateway_switcher.main:main",
        ],
        "gui_scripts": [
            "gateway-switcher-gui=gateway_switcher.main:main",
        ],
    },
)
