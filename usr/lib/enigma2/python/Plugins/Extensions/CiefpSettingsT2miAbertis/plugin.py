import urllib.request
import subprocess
import os
import platform
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Plugins.Plugin import PluginDescriptor

PLUGIN_VERSION = "1.4"
PLUGIN_NAME = "CiefpSettingsT2miAbertis"
ICON_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/icon.png"
ASTRA_CONF_URL = "https://raw.githubusercontent.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/refs/heads/main/astra%20abertis%20script%20arm%20(%20UHD%204K%20)/etc/astra/astra.conf"
SYSCTL_CONF_URL = "https://raw.githubusercontent.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/refs/heads/main/etc/sysctl.conf"
SOFTCAM_KEY_URL = "https://raw.githubusercontent.com/MOHAMED19OS/SoftCam_Emu/refs/heads/main/SoftCam.Key"
ABERTIS_ARM_URL = "https://github.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/raw/refs/heads/main/astra%20abertis%20script%20arm%20(%20UHD%204K%20)/etc/astra/scripts/abertis"
ABERTIS_MIPS_URL = "https://github.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/raw/refs/heads/main/astra%20abertis%20script%20mips%20(%20HD%20)/etc/astra/scripts/abertis"

class CiefpSettingsT2miAbertis(Screen):
    skin = """
    <screen name="CiefpSettingsT2miAbertis" position="center,center" size="1200,600" title="CiefpSettings T2mi Abertis Installer">
        <!-- Menu section -->
        <widget name="info" position="10,10" size="590,450" font="Regular;22" valign="center" halign="left" />

        <!-- Background section -->
        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/background.png" position="610,10" size="600,450" alphatest="on" />

        <!-- Status section -->
        <widget name="status" position="10,460" size="1180,60" font="Bold;22" valign="center" halign="center" backgroundColor="#cccccc" foregroundColor="#000000" />
        <widget name="key_red" position="10,530" size="380,60" font="Bold;24" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="410,530" size="380,60" font="Bold;24" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="810,530" size="380,60" font="Bold;24" halign="center" backgroundColor="#D6A200" foregroundColor="#000000" />
    </screen>
    """

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.setupUI()
        self.showPrompt()

    def setupUI(self):
        self["info"] = Label("Initializing plugin...")
        self["status"] = Label("")
        self["key_red"] = Button("Exit")
        self["key_green"] = Button("Install")
        self["key_yellow"] = Button("Update")
        self["actions"] = ActionMap(["ColorActions", "SetupActions"], {
            "red": self.exitPlugin,
            "green": self.startInstallation,
            "yellow": self.runUpdate,
            "cancel": self.close
        }, -1)

    def showPrompt(self):
        self["info"].setText(
            "This plugin will install the following components:\n"
            "- Astra-SM\n"
            "- Configuration files (sysctl.conf, astra.conf)\n"
            "- SoftCam.Key\n"
            "- Abertis script\n\n"
            "Do you want to proceed with the installation?"
        )
        self["status"].setText("Awaiting your choice.")
        
    def runUpdate(self):
        try:
            self["status"].setText("Updating plugin...")
            self.runCommand('wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpSettingsT2miAbertis/main/installer.sh -O - | /bin/sh')
            self["status"].setText("Update complete.")
        except Exception as e:
            self["status"].setText(f"Update failed: {str(e)}")

    def startInstallation(self):
        installed_files = []
        try:
            self["info"].setText("Checking system compatibility...")
            system_info = platform.machine()
            py_ver = platform.python_version_tuple()
            python_version = f"{py_ver[0]}.{py_ver[1]}.{py_ver[2]}"
            
            if py_ver[0] != '3' or int(py_ver[1]) < 9:
                self["status"].setText(f"Python 3.9+ is required. Current version: {python_version}.")
                return

            if system_info in ["arm", "armv7", "armv7l"]:
                system_info = "arm"
            elif system_info not in ["mips"]:
                self["status"].setText("Unsupported architecture: " + system_info)
                return

            self["info"].setText(f"Detected Python version: {python_version}. Adjusting installation accordingly.")

            self["info"].setText("Installing Astra-SM...")
            result = self.runCommand("opkg update && opkg install astra-sm")
            if "not found" in result or "failed" in result.lower():
                self["status"].setText("Failed to install Astra-SM. Check opkg sources.")
                return
            self["status"].setText("Astra-SM installed successfully.")
            installed_files.append("astra-sm")

            if py_ver[1] == '12' and py_ver[2] == '4':
                self.installFilesForPythonVersion(python_version, system_info, specific=True)
            else:
                self.installFilesForPythonVersion(python_version, system_info)

            self["info"].setText("\n".join([
                "Installation successful! Installed files:",
                *[f"- {file}" for file in installed_files],
                "\nInstallation complete. Please reboot your system."
            ]))

            self.session.openWithCallback(self.rebootPrompt, MessageBox, "Installation complete! Do you want to reboot now?", MessageBox.TYPE_YESNO)
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")

    def installFilesForPythonVersion(self, python_version, system_info, specific=False):
        installed_files = []

        try:
            self["info"].setText(f"Installing configuration files for Python {python_version}...")

            if not self.downloadAndSave(SYSCTL_CONF_URL, "/etc/sysctl.conf"):
                self["status"].setText("Failed to download sysctl.conf.")
                return
            installed_files.append("sysctl.conf")

            os.makedirs("/etc/astra", exist_ok=True)
            if not self.downloadAndSave(ASTRA_CONF_URL, "/etc/astra/astra.conf"):
                self["status"].setText("Failed to download astra.conf.")
                return
            installed_files.append("astra.conf")

            os.makedirs("/etc/astra/scripts", exist_ok=True)
            script_url = ABERTIS_ARM_URL if system_info == "arm" else ABERTIS_MIPS_URL
            if not self.downloadAndSave(script_url, "/etc/astra/scripts/abertis", chmod=0o755):
                self["status"].setText("Failed to download Abertis script.")
                return
            installed_files.append("abertis")

            if specific:
                os.makedirs("/etc/tuxbox/config/oscam-emu", exist_ok=True)
                self.downloadAndSave(SOFTCAM_KEY_URL, "/etc/tuxbox/config/softcam.key")
                installed_files.append("softcam.key (/etc/tuxbox/config/)")

                self.downloadAndSave(SOFTCAM_KEY_URL, "/etc/tuxbox/config/oscam-emu/softcam.key")
                installed_files.append("softcam.key (/etc/tuxbox/config/oscam-emu/)")

            self["info"].setText("All files installed successfully for Python version " + python_version)
            return installed_files

        except Exception as e:
            self["status"].setText(f"Error during file installation: {str(e)}")
            return []

    def downloadAndSave(self, url, dest_path, chmod=None):
        try:
            self["info"].setText(f"Downloading {dest_path}...")
            urllib.request.urlretrieve(url, dest_path)

            if chmod:
                os.chmod(dest_path, chmod)

            self["status"].setText(f"{dest_path} saved successfully.")
            return True
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")
            return False

    def runCommand(self, command):
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                return stderr.decode("utf-8")
            return stdout.decode("utf-8")
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def rebootPrompt(self, confirmed):
        if confirmed:
            self.close()
            self.runCommand("reboot")

    def exitPlugin(self):
        self.close()


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=PLUGIN_NAME,
            description=f"Installer for T2MI Abertis configuration (Version {PLUGIN_VERSION})",
            where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
            icon=ICON_PATH,
            fnc=lambda session, **kwargs: session.open(CiefpSettingsT2miAbertis)
        )
    ]
