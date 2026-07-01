import os
import winreg
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog
from logger import logger


class ProgramDetector:
    """Detects installed programs using multiple strategies."""

    def __init__(self):
        self.common_install_paths = [
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
            Path.home() / "AppData/Local/Programs",
            Path("C:/ProgramData"),
        ]
        self.program_executables = {
            "euroscope": ["EuroScope.exe"],
            "trackaudio": ["trackaudio.exe", "TrackAudio.exe"],
            "vacs": ["VACS.exe", "vacs-client.exe"],
        }

    def detect(self, program_name: str) -> Optional[str]:
        """Detects a program using registry, common paths, and finally a file picker."""
        result = self.registry(program_name)
        if result:
            logger.info(f"INFO: Found {program_name} via registry: {result}")
            return result

        result = self.common_paths(program_name)
        if result:
            logger.info(f"INFO: Found {program_name} in common paths: {result}")
            return result

        logger.info(f"INFO: Could not find {program_name} automatically. Please select the executable.")
        result = self.open_file_dialog(program_name)
        if result:
            logger.info(f"INFO: User selected {program_name}: {result}")
            return result

        return None

    def registry(self, program_name: str) -> Optional[str]:
        """Searches Windows Registry for installed programs."""
        program_name_lower = program_name.lower()

        uninstall_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for hive, path in uninstall_paths:
            logger.debug(f"DEBUG: Searching registry hive {hive} at path {path} for {program_name}")
            try:
                with winreg.OpenKey(hive, path) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for i in range(count):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                display_name = self._get_registry_value(subkey, "DisplayName", "")
                                if not display_name or program_name_lower not in display_name.lower():
                                    continue

                                install_loc = self._get_registry_value(subkey, "InstallLocation", "")
                                if install_loc:
                                    exe_path = self._find_executable_in_dir(install_loc, program_name)
                                    if exe_path:
                                        return exe_path

                                display_icon = self._get_registry_value(subkey, "DisplayIcon", "")
                                if display_icon:
                                    icon_path = self._extract_path(display_icon)
                                    if icon_path and os.path.isfile(icon_path) and "uninstall" not in icon_path.lower():
                                        return icon_path

                                uninstall_string = self._get_registry_value(subkey, "UninstallString", "")
                                if uninstall_string:
                                    uninstall_path = self._extract_path(uninstall_string)
                                    if uninstall_path:
                                        if os.path.isfile(uninstall_path) and "uninstall" not in uninstall_path.lower():
                                            return uninstall_path

                                        parent_dir = os.path.dirname(uninstall_path)
                                        if parent_dir:
                                            exe_path = self._find_executable_in_dir(parent_dir, program_name)
                                            if exe_path:
                                                logger.info(f"Found {program_name} via UninstallString Registry: {exe_path}")
                                                return exe_path
                        except PermissionError:
                            logger.debug(f"DEBUG: Permission denied when accessing registry key for {program_name}")
                            continue
            except FileNotFoundError:
                logger.debug(f"DEBUG: Registry uninstall path not found for {program_name} in hive {hive}")
                continue

        app_paths_roots = [
            r"Software\Microsoft\Windows\CurrentVersion\App Paths",
            r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\App Paths",
        ]
        executables = self.program_executables.get(program_name_lower, [f"{program_name}.exe"])

        for exe_name in executables:
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for root in app_paths_roots:
                    try:
                        with winreg.OpenKey(hive, root) as key:
                            with winreg.OpenKey(key, exe_name) as subkey:
                                default_path = self._get_registry_value(subkey, "", "")
                                if default_path:
                                    extracted = self._extract_path(default_path)
                                    if extracted and os.path.isfile(extracted):
                                        return extracted

                                app_dir = self._get_registry_value(subkey, "Path", "")
                                if app_dir:
                                    exe_path = self._find_executable_in_dir(app_dir, program_name)
                                    if exe_path:
                                        logger.info(f"Found {program_name} via App Paths Registry: {exe_path}")
                                        return exe_path
                    except FileNotFoundError:
                        logger.debug(f"DEBUG: File not found in registry for {program_name}")
                        continue
                    except PermissionError:
                        logger.debug(f"DEBUG: Permission denied when accessing registry key for {program_name}")
                        continue

        # Installer\Folders often contains the install root directly
        installer_folders_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\Folders"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, installer_folders_path) as key:
                value_count = winreg.QueryInfoKey(key)[1]
                for i in range(value_count):
                    try:
                        value_name, value_data, _ = winreg.EnumValue(key, i)
                        candidates = [str(value_name).strip(), str(value_data).strip()]

                        for candidate in candidates:
                            if not candidate:
                                continue

                            candidate_lower = candidate.lower()
                            if program_name_lower not in candidate_lower:
                                continue

                            exe_path = self._find_executable_in_dir(candidate, program_name)
                            if exe_path:
                                logger.info(f"Found {program_name} via Installer\\Folders Registry: {exe_path}")
                                return exe_path
                    except OSError:
                        logger.debug(f"DEBUG: OSError occurred while searching registry for {program_name}")
                        continue
        except FileNotFoundError:
            pass
        
        logger.debug(f"DEBUG: Could not find {program_name} in registry.")
        return None

    def common_paths(self, program_name: str) -> Optional[str]:
        """Searches common installation directories."""
        logger.debug(f"DEBUG: Searching common paths for {program_name}")
        program_name_lower = program_name.lower()
        executables = self.program_executables.get(program_name_lower, [f"{program_name}.exe"])

        for base_path in self.common_install_paths:
            if not base_path.exists():
                continue

            try:
                for item in base_path.rglob(f"*{program_name_lower}*"):
                    if not item.is_dir():
                        continue

                    for exe_name in executables:
                        exe_path = item / exe_name
                        if exe_path.is_file() and "uninstall" not in exe_path.name.lower():
                            return str(exe_path)
            except OSError:
                logger.debug(f"DEBUG: OSError occurred while searching common paths for {program_name}")
                continue

        logger.info(f"INFO: Could not find {program_name} in common paths.")
        return None


    def open_file_dialog(self, program_name: str) -> Optional[str]:
        """Opens a file dialog for the user to select the program executable."""
        logger.info(f"INFO: Please select the {program_name} executable manually.")

        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        root.destroy()

        logger.debug(f"DEBUG: User selected file path: {file_path}")
        return file_path if file_path else None

    @staticmethod
    def _get_registry_value(key, value_name: str, default: str) -> str:
        """Safely gets a registry value."""
        try:
            return winreg.QueryValueEx(key, value_name)[0]
        except FileNotFoundError:
            return default

    @staticmethod
    def _extract_path(value: str) -> Optional[str]:
        """Extracts a path from a registry string or command line."""
        try:
            value = value.strip()
            if not value:
                return None

            if value.startswith('"'):
                return value.split('"')[1]

            return value.split(" ")[0]
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _find_executable_in_dir(directory: str, program_name: str) -> Optional[str]:
        """Finds an executable file in a directory."""
        try:
            base_path = Path(directory)
            if not base_path.exists():
                return None

            if base_path.is_file() and base_path.suffix.lower() == ".exe":
                if "uninstall" not in base_path.name.lower():
                    return str(base_path)
                return None

            if base_path.is_dir():
                program_name_lower = program_name.lower()
                candidates = [
                    f"{program_name}.exe",
                    f"{program_name.upper()}.exe",
                    f"{program_name_lower}.exe",
                    f"{program_name_lower}-client.exe",
                    f"{program_name}-client.exe",
                ]

                for exe_name in candidates:
                    exe_path = base_path / exe_name
                    if exe_path.is_file() and "uninstall" not in exe_path.name.lower():
                        return str(exe_path)

                exe_files = [
                    f for f in base_path.glob("*.exe")
                    if f.is_file() and "uninstall" not in f.name.lower()
                ]

                if exe_files:
                    return str(exe_files[0])
        except OSError:
            logger.debug(f"DEBUG: OSError occurred while searching common paths for {program_name}")
            pass

        return None