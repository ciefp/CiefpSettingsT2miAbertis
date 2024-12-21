import urllib.request
import subprocess
import os
import platform
import zipfile
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Plugins.Plugin import PluginDescriptor

PLUGIN_VERSION = "1.2"  # Verzija plugina
PLUGIN_NAME = "CiefpSettingsT2miAbertis"
ICON_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/icon.png"
ASTRA_CONF_URL = "https://raw.githubusercontent.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/refs/heads/main/astra%20abertis%20script%20arm%20(%20UHD%204K%20)/etc/astra/astra.conf"
SYSCTL_CONF_URL = "https://raw.githubusercontent.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/refs/heads/main/etc/sysctl.conf"
SOFTCAM_KEY_URL = "https://raw.githubusercontent.com/MOHAMED19OS/SoftCam_Emu/refs/heads/main/SoftCam.Key"
ABERTIS_ARM_URL = "https://github.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/raw/refs/heads/main/astra%20abertis%20script%20arm%20(%20UHD%204K%20)/etc/astra/scripts/abertis"
ABERTIS_MIPS_URL = "https://github.com/ciefp/ciefpsettings-enigma2-Abertis-t2mi/raw/refs/heads/main/astra%20abertis%20script%20mips%20(%20HD%20)/etc/astra/scripts/abertis"

class CiefpSettingsT2miAbertis(Screen):
    skin = """
    <screen name="CiefpSettingsT2miAbertis" position="center,center" size="900,600" title="CiefpSettings T2mi Abertis Installer">
        <widget name="info" position="10,10" size="880,500" font="Regular;20" valign="center" halign="left" />
        <widget name="status" position="10,520" size="880,40" font="Regular;20" valign="center" halign="left" />
        <widget name="key_red" position="10,570" size="200,40" font="Regular;18" halign="center" backgroundColor="#9F1313" />
        <widget name="key_green" position="690,570" size="200,40" font="Regular;18" halign="center" backgroundColor="#1F771F" />
        <widget name="version_label" position="10,600" size="880,40" font="Regular;18" valign="center" halign="center" />
    </screen>
    """

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        self.setupUI()
        self.startInstallation()

    def setupUI(self):
        self["info"] = Label("Initializing plugin installation...")
        self["status"] = Label("")
        self["key_red"] = Button("Exit")
        self["key_green"] = Button("Reboot")
        self["version_label"] = Label(f"Plugin Version: {PLUGIN_VERSION}")  # Prikazivanje verzije plugina
        self["actions"] = ActionMap(["ColorActions", "SetupActions"], {
            "red": self.exitPlugin,
            "green": self.rebootSystem
        }, -1)

    def startInstallation(self):
        installed_files = []
        try:
            self["info"].setText("Checking system compatibility...")
            system_info = platform.machine()
            is_py3 = (platform.python_version_tuple()[0] == '3')

            if not is_py3:
                self["status"].setText("Python3 is required for this plugin.")
                return

            if system_info in ["arm", "armv7", "armv7l"]:
                system_info = "arm"
            elif system_info not in ["mips"]:
                self["status"].setText("Unsupported architecture: " + system_info)
                return

            self["info"].setText("Installing Astra-SM...")
            self.runCommand("opkg update && opkg install astra-sm")
            self["status"].setText("Astra-SM installed successfully.")
            installed_files.append("astra-sm")

            self["info"].setText("Downloading and copying configuration files...")

            # Preuzimanje i kopiranje sysctl.conf
            self.downloadAndSave(SYSCTL_CONF_URL, "/etc/sysctl.conf")
            installed_files.append("sysctl.conf")

            # Preuzimanje i čuvanje astra.conf fajla
            os.makedirs("/etc/astra", exist_ok=True)
            self.downloadAndSave(ASTRA_CONF_URL, "/etc/astra/astra.conf")
            installed_files.append("astra.conf")

            # Preuzimanje i kopiranje Abertis skripte
            os.makedirs("/etc/astra/scripts", exist_ok=True)
            self.downloadAndSave(ABERTIS_ARM_URL, "/etc/astra/scripts/abertis", chmod=0o755)
            installed_files.append("abertis")

            # Preuzimanje i čuvanje softcam.key fajla na prvu lokaciju
            os.makedirs("/etc/tuxbox/config/oscam-emu", exist_ok=True)
            self.downloadAndSave(SOFTCAM_KEY_URL, "/etc/tuxbox/config/softcam.key")
            installed_files.append("softcam.key (/etc/tuxbox/config/)")

            # Kopiranje softcam.key fajla na drugu lokaciju
            self.downloadAndSave(SOFTCAM_KEY_URL, "/etc/tuxbox/config/oscam-emu/softcam.key")
            installed_files.append("softcam.key (/etc/tuxbox/config/oscam-emu/)")

            self["info"].setText("\n".join([
                "Installation successful! Installed files:",
                *[f"- {file}" for file in installed_files],
                "\nInstallation complete. Please reboot your system."
            ]))
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")

    def downloadAndSave(self, url, dest_path, chmod=None):
        try:
            self["info"].setText(f"Downloading {dest_path}...")
            urllib.request.urlretrieve(url, dest_path)  # Preuzimanje fajla sa URL-a

            # Ako su prava (chmod) postavljena, menjamo prava fajla
            if chmod:
                os.chmod(dest_path, chmod)

            self["status"].setText(f"{dest_path} saved successfully.")  # Prikazivanje uspeha
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")  # Prikazivanje greške ako nešto nije u redu

    def runCommand(self, command):
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(stderr.decode("utf-8"))
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")

    def exitPlugin(self):
        self.close()

    def rebootSystem(self):
        self.session.openWithCallback(self.rebootCallback, MessageBox, "Do you want to reboot now?", MessageBox.TYPE_YESNO)

    def rebootCallback(self, confirmed):
        if confirmed:
            self.runCommand("reboot")


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=PLUGIN_NAME,
            description=f"Installer for T2MI Abertis configuration (Version {PLUGIN_VERSION})",  # Prikazivanje verzije u opisu plugina
            where=[PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU],
            icon=ICON_PATH,
            fnc=lambda session, **kwargs: session.open(CiefpSettingsT2miAbertis)
        )
    ]
