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
import shutil  # Dodajte ovaj red

PLUGIN_VERSION = "1.5"
PLUGIN_NAME = "CiefpSettingsT2miAbertis"
ICON_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/icon.png"

class CiefpSettingsT2miAbertis(Screen):
    skin = """ 
    <screen name="CiefpSettingsT2miAbertis" position="center,center" size="1200,600" title="CiefpSettings T2mi Abertis Installer (v{version}) ">
        <!-- Menu section -->
        <widget name="info" position="10,10" size="580,450" font="Regular;22" valign="center" halign="left" />

        <!-- Background section -->
        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/background.png" position="590,10" size="600,450" alphatest="on" />

        <!-- Status section -->
        <widget name="status" position="10,470" size="1180,55" font="Bold;22" valign="center" halign="center" backgroundColor="#cccccc" foregroundColor="#000000" />
        <widget name="key_red" position="10,530" size="380,60" font="Bold;24" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="410,530" size="380,60" font="Bold;24" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="810,530" size="380,60" font="Bold;24" halign="center" backgroundColor="#D6A200" foregroundColor="#000000" />
    </screen>
    """.format(version=PLUGIN_VERSION)

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

    def createRequiredDirectories(self):
        try:
            print("Creating required directories...")
            self["info"].setText("Creating required directories...")

            # Lista potrebnih direktorija
            required_directories = [
                "/etc/astra",
                "/etc/astra/scripts",
                "/etc/tuxbox/config",
                "/etc/tuxbox/config/oscam-emu"
            ]

            # Stvaranje direktorija
            for directory in required_directories:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory, exist_ok=True)
                        print(f"Created directory: {directory}")
                    except PermissionError:
                        self["status"].setText(f"Permission denied: Unable to create directory {directory}.")
                        print(f"Permission denied: Unable to create directory {directory}.")
                        return False
                    except Exception as e:
                        self["status"].setText(f"Error creating directory {directory}: {str(e)}")
                        print(f"Error creating directory {directory}: {str(e)}")
                        return False

            self["info"].setText("All required directories created successfully.")
            print("All required directories created successfully.")
            return True

        except Exception as e:
            self["status"].setText(f"Error during directory creation: {str(e)}")
            print(f"Error during directory creation: {str(e)}")
            return False

    def isFileSame(self, source_path, dest_path):
        try:
            if not os.path.exists(source_path) or not os.path.exists(dest_path):
                return False

            with open(source_path, 'rb') as src_file, open(dest_path, 'rb') as dst_file:
                return src_file.read() == dst_file.read()

        except Exception as e:
            self["status"].setText(f"Error comparing files: {str(e)}")
            return False

    def startInstallation(self):
        try:
            print("Starting installation process...")
            self["info"].setText("Cleaning previous installation...")
            self.cleanPreviousInstallation()

            # Stvaranje potrebnih direktorija
            if not self.createRequiredDirectories():
                self["status"].setText("Failed to create required directories. Installation aborted.")
                print("Failed to create required directories. Installation aborted.")
                return

            # Instalacija Astra-SM
            self["info"].setText("Installing Astra-SM...")
            print("Installing Astra-SM...")
            result = self.runCommand("opkg update && opkg install astra-sm")
            if "not found" in result or "failed" in result.lower():
                self["status"].setText("Failed to install Astra-SM. Check opkg sources.")
                print("Failed to install Astra-SM. Check opkg sources.")
                return
            self["status"].setText("Astra-SM installed successfully.")
            print("Astra-SM installed successfully.")

            # Instalacija novih datoteka
            installed_files = self.installFilesFromPluginData()
            if not installed_files:
                self["status"].setText("Failed to install new files.")
                print("Failed to install new files.")
                return

            # Prikazivanje završnog statusa
            self["info"].setText("\n".join([
                "Installation successful! Installed files:",
                *[f"- {file}" for file in installed_files],
                "\nInstallation complete. Please reboot your system."
            ]))
            print("Installation complete. Please reboot your system.")

            # Potvrda ponovnog pokretanja sustava
            self.session.openWithCallback(self.rebootPrompt, MessageBox,
                                          "Installation complete! Do you want to reboot now?", MessageBox.TYPE_YESNO)

        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")
            print(f"Error during installation: {str(e)}")

    def cleanPreviousInstallation(self):
        try:
            print("Cleaning previous installation...")
            cleanup_paths = [
                "/etc/astra/astra.conf",
                "/etc/sysctl.conf",
                "/etc/astra/scripts/abertis",
                "/etc/tuxbox/config/softcam.key",
                "/etc/tuxbox/config/oscam-emu/softcam.key"
            ]

            for path in cleanup_paths:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Removed old file: {path}")

            self["info"].setText("Previous installation cleaned successfully.")
            print("Previous installation cleaned successfully.")
        except Exception as e:
            self["status"].setText(f"Error cleaning previous installation: {str(e)}")
            print(f"Error cleaning previous installation: {str(e)}")

    def installFilesFromPluginData(self):
        installed_files = []
        try:
            print("Installing configuration files...")
            self["info"].setText("Installing configuration files...")
            data_dir = resolveFilename(SCOPE_PLUGINS, "Extensions/CiefpSettingsT2miAbertis/data/")

            # Instalacija sysctl.conf
            dest_path = "/etc/sysctl.conf"
            source_path = os.path.join(data_dir, "sysctl.conf")
            if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                print(f"Copying {source_path} to {dest_path}...")
                if not self.copyFile(source_path, dest_path):
                    self["status"].setText(f"Failed to copy {source_path} to {dest_path}.")
                    print(f"Failed to copy {source_path} to {dest_path}.")
                    return []
                installed_files.append("sysctl.conf")
                print(f"{source_path} copied successfully to {dest_path}.")

            # Instalacija astra.conf
            dest_path = "/etc/astra/astra.conf"
            source_path = os.path.join(data_dir, "astra.conf")
            if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                print(f"Copying {source_path} to {dest_path}...")
                if not self.copyFile(source_path, dest_path):
                    self["status"].setText(f"Failed to copy {source_path} to {dest_path}.")
                    print(f"Failed to copy {source_path} to {dest_path}.")
                    return []
                installed_files.append("astra.conf")
                print(f"{source_path} copied successfully to {dest_path}.")

            # Instalacija Abertis skripte (za ARM ili MIPS)
            system_info = platform.machine()
            if system_info in ["arm", "armv7", "armv7l"]:
                script_arch = "arm"
            elif system_info == "mips":
                script_arch = "mips"
            else:
                self["status"].setText(f"Unsupported architecture: {system_info}")
                print(f"Unsupported architecture: {system_info}")
                return []

            script_dir = os.path.join(data_dir, script_arch)
            source_path = os.path.join(script_dir, "abertis")
            dest_path = "/etc/astra/scripts/abertis"
            if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                print(f"Copying {source_path} to {dest_path}...")
                if not self.copyFile(source_path, dest_path, chmod=0o755):
                    self["status"].setText(f"Failed to copy {source_path} to {dest_path}.")
                    print(f"Failed to copy {source_path} to {dest_path}.")
                    return []
                installed_files.append("abertis")
                print(f"{source_path} copied successfully to {dest_path}.")

            # Instalacija SoftCam.Key
            softcam_dest_paths = [
                "/etc/tuxbox/config/softcam.key",
                "/etc/tuxbox/config/oscam-emu/softcam.key"
            ]
            source_path = os.path.join(data_dir, "SoftCam.Key")
            for dest_path in softcam_dest_paths:
                if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                    print(f"Copying {source_path} to {dest_path}...")
                    if not self.copyFile(source_path, dest_path):
                        self["status"].setText(f"Failed to copy {source_path} to {dest_path}.")
                        print(f"Failed to copy {source_path} to {dest_path}.")
                        return []
                    installed_files.append(f"softcam.key ({dest_path})")
                    print(f"{source_path} copied successfully to {dest_path}.")

            self["info"].setText("All files installed successfully.")
            print("All files installed successfully.")
            return installed_files

        except Exception as e:
            self["status"].setText(f"Error during file installation: {str(e)}")
            print(f"Error during file installation: {str(e)}")
            return []

    def copyFile(self, source_path, dest_path, chmod=None):
        try:
            print(f"Creating destination directory for {dest_path}...")
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)  # Stvaranje odredišnog direktorija
            print(f"Copying {source_path} to {dest_path}...")
            shutil.copy2(source_path, dest_path)  # Kopiranje datoteke sa čuvanjem atributa
            if chmod:
                os.chmod(dest_path, chmod)
            print(f"{source_path} copied successfully to {dest_path}.")
            return True
        except Exception as e:
            self["status"].setText(f"Error copying {source_path} to {dest_path}: {str(e)}")
            print(f"Error copying {source_path} to {dest_path}: {str(e)}")
            return False

    def runCommand(self, command):
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                return stderr.decode("utf-8", errors="ignore")  # Ignoriraj greške kod dekodiranja
            return stdout.decode("utf-8", errors="ignore")
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
