
# CiefpSettings T2mi Abertis Plugin

This plugin is intended for easy installation of the necessary configurations and scripts for using T2MI Abertis functionality on Enigma2 devices.

## What does the plugin do?

- **Automatically checks system compatibility (Python 3 and ARM processor).**
- **Installs **Astra-SM** via `opkg`.**
- **Downloads and places configuration files:**
- **astra.conf** in `/etc/astra/`.**
- **abertis** script in `/etc/astra/scripts/`.**
- **softcam.key** in two locations: `/etc/tuxbox/config/` and `/etc/tuxbox/config/oscam-emu/`.**
- **sysctl.conf** in `/etc/`.**
- **At the end of the installation, it displays an overview of the installed files and suggests a system reboot.**

## Installation successful! Installed files:
- **astra-sm**
- **astra.conf**
- **abertis**
- **softcam.key (/etc/tuxbox/config/)**
- **softcam.key (/etc/tuxbox/config/oscam-emu/)**

Installation complete. Please reboot your system.

## Why use this plugin?

Automatic installation and configuration without the need for manual intervention.

Quick and easy provisioning of support for Abertis and T2MI services.

## Note:
This version only supports ARM processors and is intended for devices using Python 3.
installation is done via telnet with the wget command

# ..::ciefpsettings::..
