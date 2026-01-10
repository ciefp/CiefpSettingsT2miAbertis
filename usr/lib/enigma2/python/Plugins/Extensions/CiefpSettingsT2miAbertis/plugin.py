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
import shutil
import time

PLUGIN_VERSION = "1.8"
PLUGIN_NAME = "CiefpSettingsT2miAbertis"
ICON_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/icon.png"

class CiefpSettingsT2miAbertis(Screen):
    skin = """ 
    <screen name="CiefpSettingsT2miAbertis" position="center,center" size="1600,800" title="CiefpSettings T2mi Abertis Installer (v{version}) ">
        <!-- Menu section -->
        <widget name="info" position="10,10" size="780,650" font="Regular;24" valign="center" halign="left" />

        <!-- Background section -->
        <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSettingsT2miAbertis/background.png" position="790,10" size="800,650" alphatest="on" />

        <!-- Status section -->
        <widget name="status" position="10,670" size="1580,50" font="Bold;24" valign="center" halign="center" backgroundColor="#cccccc" foregroundColor="#000000" />
        <widget name="key_red" position="10,730" size="500,60" font="Bold;26" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
        <widget name="key_green" position="550,730" size="500,60" font="Bold;26" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
        <widget name="key_yellow" position="1090,730" size="500,60" font="Bold;26" halign="center" backgroundColor="#D6A200" foregroundColor="#000000" />
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
        print("[CiefpSettingsT2miAbertis] Showing installation prompt")
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
            print("[CiefpSettingsT2miAbertis] Starting update process")
            self["status"].setText("Updating plugin...")
            start_time = time.time()
            self.runCommand('wget -q "--no-check-certificate" https://raw.githubusercontent.com/ciefp/CiefpSettingsT2miAbertis/main/installer.sh -O - | /bin/sh')
            print(f"[CiefpSettingsT2miAbertis] Update completed in {time.time() - start_time:.2f} seconds")
            self["status"].setText("Update complete.")
        except Exception as e:
            self["status"].setText(f"Update failed: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Update failed: {str(e)}")

    def createRequiredDirectories(self):
        try:
            print("[CiefpSettingsT2miAbertis] Starting directory creation")
            self["info"].setText("Creating required directories...")
            start_time = time.time()

            required_directories = [
                "/etc/astra",
                "/etc/astra/scripts",
                "/etc/tuxbox/config",
                "/etc/tuxbox/config/oscam-emu"
            ]

            for directory in required_directories:
                if not os.path.exists(directory):
                    print(f"[CiefpSettingsT2miAbertis] Creating directory: {directory}")
                    os.makedirs(directory, exist_ok=True)
                else:
                    print(f"[CiefpSettingsT2miAbertis] Directory already exists: {directory}")

            elapsed_time = time.time() - start_time
            self["info"].setText("All required directories created successfully.")
            print(f"[CiefpSettingsT2miAbertis] Directory creation completed in {elapsed_time:.2f} seconds")
            return True

        except Exception as e:
            self["status"].setText(f"Error during directory creation: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Error during directory creation: {str(e)}")
            return False

    def isFileSame(self, source_path, dest_path):
        try:
            if not os.path.exists(source_path) or not os.path.exists(dest_path):
                return False

            print(f"[CiefpSettingsT2miAbertis] Comparing files: {source_path} and {dest_path}")
            start_time = time.time()
            with open(source_path, 'rb') as src_file, open(dest_path, 'rb') as dst_file:
                result = src_file.read() == dst_file.read()
            print(f"[CiefpSettingsT2miAbertis] File comparison completed in {time.time() - start_time:.2f} seconds")
            return result

        except Exception as e:
            self["status"].setText(f"Error comparing files: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Error comparing files: {str(e)}")
            return False

    def startInstallation(self):
        try:
            print("[CiefpSettingsT2miAbertis] Starting installation process")
            self["info"].setText("Cleaning previous installation...")
            self.cleanPreviousInstallation()

            if not self.createRequiredDirectories():
                self["status"].setText("Failed to create required directories. Installation aborted.")
                print("[CiefpSettingsT2miAbertis] Failed to create required directories")
                return

            self["info"].setText("Updating package list...")
            self["status"].setText("The installation is in progress, please wait.")
            print("[CiefpSettingsT2miAbertis] Installing Astra-SM...")
            max_attempts = 2
            attempt = 1
            astra_sm_installed = False

            # Prvo pokušaj ažuriranje paketa
            while attempt <= max_attempts:
                print(f"[CiefpSettingsT2miAbertis] Attempt {attempt} of {max_attempts} to update package list")
                start_time = time.time()
                update_result = self.runCommand("opkg update", timeout=45)
                elapsed_time = time.time() - start_time
                print(f"[CiefpSettingsT2miAbertis] Attempt {attempt} (update) completed in {elapsed_time:.2f} seconds")
                print(f"[CiefpSettingsT2miAbertis] Update output: {update_result}")

                if "not found" not in update_result and "failed" not in update_result.lower() and "timed out" not in update_result.lower():
                    print("[CiefpSettingsT2miAbertis] Package list updated successfully")
                    break
                else:
                    print(f"[CiefpSettingsT2miAbertis] Attempt {attempt} (update) failed: {update_result}")
                    if attempt == max_attempts:
                        self["info"].setText("Failed to update package list. Trying to install Astra-SM anyway...")
                        print("[CiefpSettingsT2miAbertis] All attempts to update package list failed")
                    else:
                        self["info"].setText(f"Package list update failed (attempt {attempt}). Retrying...")
                        time.sleep(2)
                attempt += 1

            # Pauza pre instalacije Astra-SM
            time.sleep(5)

            # Pokušaj instalaciju Astra-SM bez obzira na uspeh ažuriranja
            self["info"].setText("Installing Astra-SM...")
            attempt = 1
            while attempt <= max_attempts:
                print(f"[CiefpSettingsT2miAbertis] Attempt {attempt} of {max_attempts} to install Astra-SM")
                start_time = time.time()
                install_result = self.runCommand("opkg install astra-sm", timeout=45)
                elapsed_time = time.time() - start_time
                print(f"[CiefpSettingsT2miAbertis] Attempt {attempt} (install) completed in {elapsed_time:.2f} seconds")
                print(f"[CiefpSettingsT2miAbertis] Install output: {install_result}")

                if "not found" not in install_result and "failed" not in install_result.lower() and "timed out" not in install_result.lower():
                    self["status"].setText("Astra-SM installed successfully.")
                    astra_sm_installed = True
                    break
                else:
                    print(f"[CiefpSettingsT2miAbertis] Attempt {attempt} (install) failed: {install_result}")
                    if attempt == max_attempts:
                        self["status"].setText("Failed to install Astra-SM. Please install it manually later.")
                        print("[CiefpSettingsT2miAbertis] All attempts to install Astra-SM failed")
                    else:
                        self["info"].setText(f"Astra-SM installation failed (attempt {attempt}). Retrying...")
                        time.sleep(2)
                attempt += 1

            # Nastavi sa kopiranjem fajlova
            self["info"].setText("Installing configuration files...")
            installed_files = self.installFilesFromPluginData()
            if not installed_files:
                self["status"].setText("Failed to install configuration files.")
                print("[CiefpSettingsT2miAbertis] Failed to install new files")
                return

            self["info"].setText("\n".join([
                "Installation successful! Installed files:",
                *[f"- {file}" for file in installed_files],
                "\nInstallation complete. Please reboot your system."
            ]))
            if astra_sm_installed:
                self["status"].setText("Installation completed successfully.")
            else:
                self["status"].setText("Configuration files installed. Please install Astra-SM manually and reboot.")

            self.session.openWithCallback(self.rebootPrompt, MessageBox,
                                          "Installation complete! Do you want to reboot now?", MessageBox.TYPE_YESNO)

        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Installation error: {str(e)}")

    def cleanPreviousInstallation(self):
        try:
            print("[CiefpSettingsT2miAbertis] Cleaning previous installation")
            start_time = time.time()
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
                    print(f"[CiefpSettingsT2miAbertis] Removed old file: {path}")

            elapsed_time = time.time() - start_time
            self["info"].setText("Previous installation cleaned successfully.")
            print(f"[CiefpSettingsT2miAbertis] Cleaning completed in {elapsed_time:.2f} seconds")
        except Exception as e:
            self["status"].setText(f"Error cleaning previous installation: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Error cleaning previous installation: {str(e)}")

    def installFilesFromPluginData(self):
        installed_files = []
        try:
            print("[CiefpSettingsT2miAbertis] Installing configuration files")
            self["info"].setText("Installing configuration files...")
            data_dir = resolveFilename(SCOPE_PLUGINS, "Extensions/CiefpSettingsT2miAbertis/data/")
            start_time = time.time()

            dest_path = "/etc/sysctl.conf"
            source_path = os.path.join(data_dir, "sysctl.conf")
            if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                if self.copyFile(source_path, dest_path):
                    installed_files.append("sysctl.conf")

            dest_path = "/etc/astra/astra.conf"
            source_path = os.path.join(data_dir, "astra.conf")
            if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                if self.copyFile(source_path, dest_path):
                    installed_files.append("astra.conf")

            system_info = platform.machine()
            script_arch = "arm" if system_info in ["arm", "armv7", "armv7l"] else "mips" if system_info == "mips" else None
            if not script_arch:
                self["status"].setText(f"Unsupported architecture: {system_info}")
                print(f"[CiefpSettingsT2miAbertis] Unsupported architecture: {system_info}")
                return []

            script_dir = os.path.join(data_dir, script_arch)
            source_path = os.path.join(script_dir, "abertis")
            dest_path = "/etc/astra/scripts/abertis"
            if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                if self.copyFile(source_path, dest_path, chmod=0o755):
                    installed_files.append("abertis")

            softcam_dest_paths = [
                "/etc/tuxbox/config/softcam.key",
                "/etc/tuxbox/config/oscam-emu/softcam.key"
            ]
            source_path = os.path.join(data_dir, "SoftCam.Key")
            for dest_path in softcam_dest_paths:
                if not os.path.exists(dest_path) or not self.isFileSame(source_path, dest_path):
                    if self.copyFile(source_path, dest_path):
                        installed_files.append(f"softcam.key ({dest_path})")

            elapsed_time = time.time() - start_time
            self["info"].setText("All files installed successfully.")
            print(f"[CiefpSettingsT2miAbertis] File installation completed in {elapsed_time:.2f} seconds")
            return installed_files

        except Exception as e:
            self["status"].setText(f"Error during file installation: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Error during file installation: {str(e)}")
            return []

    def copyFile(self, source_path, dest_path, chmod=None):
        try:
            print(f"[CiefpSettingsT2miAbertis] Copying {source_path} to {dest_path}")
            start_time = time.time()
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(source_path, dest_path)
            if chmod:
                os.chmod(dest_path, chmod)
            elapsed_time = time.time() - start_time
            print(f"[CiefpSettingsT2miAbertis] Copied {source_path} to {dest_path} in {elapsed_time:.2f} seconds")
            return True
        except Exception as e:
            self["status"].setText(f"Error copying {source_path} to {dest_path}: {str(e)}")
            print(f"[CiefpSettingsT2miAbertis] Error copying {source_path} to {dest_path}: {str(e)}")
            return False

    def runCommand(self, command, timeout=120):
        try:
            print(f"[CiefpSettingsT2miAbertis] Executing command: {command}")
            start_time = time.time()
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=timeout)
            elapsed_time = time.time() - start_time
            output = stdout.decode("utf-8", errors="ignore") if process.returncode == 0 else stderr.decode("utf-8", errors="ignore")
            print(f"[CiefpSettingsT2miAbertis] Command '{command}' completed in {elapsed_time:.2f} seconds with return code {process.returncode}")
            print(f"[CiefpSettingsT2miAbertis] Command output: {output}")
            if process.returncode != 0:
                return output
            return output
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"[CiefpSettingsT2miAbertis] Command '{command}' timed out after {timeout} seconds")
            return f"Command timed out after {timeout} seconds"
        except Exception as e:
            print(f"[CiefpSettingsT2miAbertis] Error executing command '{command}': {str(e)}")
            return f"Error executing command: {str(e)}"

    def rebootPrompt(self, confirmed):
        if confirmed:
            print("[CiefpSettingsT2miAbertis] Initiating system reboot")
            self.close()
            self.runCommand("reboot")

    def exitPlugin(self):
        print("[CiefpSettingsT2miAbertis] Exiting plugin")
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