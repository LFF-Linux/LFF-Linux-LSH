#!/usr/bin/env python3
# lpm.py - LFF Linux Package Manager module
import os
import sys
import json
import shutil
import requests
import zipfile
import subprocess
from pathlib import Path

LPM_DIR = Path.home() / ".config/lff-linux/packages"
INSTALLED_PACKAGES_FILE = Path.home() / ".config/lff-linux/installed_packages.json"
INSTALLED_MODULES_FILE = Path.home() / ".config/lff-linux/installed_modules.json"
# Helper functions for installed packages/modules/APT



def ensure_pip():
    try:
        subprocess.run(["pip3", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("pip3 not found. Installing pip...")
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "python3-pip"], check=True)
        print("pip3 installed.")

# Helper functions for installed packages/modules/APT

def load_installed_packages():
    if INSTALLED_PACKAGES_FILE.exists():
        with open(INSTALLED_PACKAGES_FILE, "r") as file:
            return json.load(file)
    return {}

def save_installed_packages(packages):
    with open(INSTALLED_PACKAGES_FILE, "w") as file:
        json.dump(packages, file, indent=4)

def load_installed_modules():
    if INSTALLED_MODULES_FILE.exists():
        with open(INSTALLED_MODULES_FILE, "r") as file:
            return json.load(file)
    return []

def save_installed_modules(modules):
    with open(INSTALLED_MODULES_FILE, "w") as file:
        json.dump(modules, file, indent=4)

def update_installed_modules():
    try:
        result = subprocess.run(["pip3", "list", "--format=json"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            try:
                installed_modules = [pkg["name"] for pkg in json.loads(result.stdout)]
                save_installed_modules(installed_modules)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing pip3 output: {e}")
        else:
            print(f"Error updating installed modules: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error updating installed modules: {e}")

# LPM core functions

def lpm_install(package_name):
    # Block root usage
    if os.geteuid() == 0:
        print("Do not run lpm as root.")
        sys.exit(1)
    ensure_pip()
    print(f"Installing package: {package_name}")
    # Upgrade pip3 packages before install
    try:
        subprocess.run(["pip3", "install", "--upgrade", "--break-system-packages", "pip"], check=True)
    except Exception:
        print("Warning: Could not upgrade pip3.")
    installed_packages = load_installed_packages()
    if package_name in installed_packages:
        print(f"Package {package_name} is already installed.")
        return
    repo_url = f"https://github.com/LFF-Linux-Packages/{package_name}/archive/refs/heads/main.zip"
    package_dir = LPM_DIR / package_name
    try:
        package_dir.mkdir(parents=True, exist_ok=True)
        response = requests.get(repo_url, stream=True)
        if response.status_code != 200:
            print(f"Failed to fetch package: {package_name}")
            return
        zip_path = package_dir / "package.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(package_dir)
        zip_path.unlink()
        # Search for config.txt in all subdirectories
        config_path = None
        config_dir = None
        for root, dirs, files in os.walk(package_dir):
            if "config.txt" in files:
                config_path = Path(root) / "config.txt"
                config_dir = Path(root)
                break
        installer_mode = False
        installer_cmd = None
        installeddirpath = None
        installedfilepath = None
        installerdeb_files = None
        username = os.environ.get("USER") or os.environ.get("LOGNAME") or os.getlogin()
        if config_path and config_path.exists():
            try:
                config_vars = {}
                with open(config_path, "r") as cf:
                    for line in cf:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        if "=" in line:
                            k, v = line.split("=", 1)
                            config_vars[k.strip()] = v.strip()
                installer_cmd = config_vars.get("installer")
                installeddirpath_raw = config_vars.get("installeddirpath")
                installedfilepath_raw = config_vars.get("installedfilepath") or config_vars.get("installeddesktopfilepath")
                installerdeb = config_vars.get("installerdeb")
                # Parse installeddirpath and installedfilepath as lists
                installeddirpaths = []
                installedfilepaths = []
                if installeddirpath_raw:
                    for dp in installeddirpath_raw.split(","):
                        dp = dp.strip().replace("{username}", username)
                        if not os.path.isabs(dp):
                            dp = str((config_dir / dp).resolve())
                        installeddirpaths.append(dp)
                if installedfilepath_raw:
                    for fp in installedfilepath_raw.split(","):
                        fp = fp.strip().replace("{username}", username)
                        if not os.path.isabs(fp):
                            fp = str((config_dir / fp).resolve())
                        installedfilepaths.append(fp)
                installeddirpath = installeddirpaths if installeddirpaths else None
                installedfilepath = installedfilepaths if installedfilepaths else None
                if installer_cmd:
                    if not os.path.isabs(installer_cmd):
                        installer_cmd = str((config_dir / installer_cmd).resolve())
                    installer_mode = True
                if installerdeb:
                    installerdeb_files = [f.strip() for f in installerdeb.split(",")]
                    installerdeb_files = [str((config_dir / f).resolve()) if not os.path.isabs(f) else f for f in installerdeb_files]
            except Exception as e:
                print(f"Error reading config.txt: {e}")

        # Handle installerdeb if present
        if installerdeb_files:
            print(f"InstallerDeb mode detected. Installing .deb files: {', '.join(installerdeb_files)}")
            try:
                subprocess.run(["sudo", "apt", "update"], check=True)
                # Use sudo apt install ./file1 ./file2 ...
                subprocess.run(["sudo", "apt", "install", "-y"] + installerdeb_files, cwd=config_dir, check=True)
                pkginfo = {
                    "installerdeb": installerdeb_files,
                    "installeddirpath": installeddirpath,
                    "installedfilepath": installedfilepath,
                    "installed": True
                }
                if installer_cmd:
                    print(f"Running installer after .deb install: {installer_cmd}")
                    if installer_cmd.endswith('.py'):
                        subprocess.run([sys.executable, installer_cmd], cwd=config_dir, check=True)
                    else:
                        subprocess.run([installer_cmd], cwd=config_dir, check=True)
                    pkginfo["installer"] = installer_cmd
                installed_packages[package_name] = pkginfo
                save_installed_packages(installed_packages)
                print(f"Package {package_name} installed via installerdeb.")
                return
            except Exception as e:
                print(f"Error installing .deb files: {e}")
                return

        # If only installer is present
        if installer_mode:
            print(f"Installer mode detected. Running installer: {installer_cmd}")
            try:
                # If the installer is a .py file, run with python3
                if installer_cmd.endswith('.py'):
                    subprocess.run([sys.executable, installer_cmd], cwd=config_dir, check=True)
                else:
                    subprocess.run([installer_cmd], cwd=config_dir, check=True)
                pkginfo = {
                    "installer": installer_cmd,
                    "installeddirpath": installeddirpath,
                    "installedfilepath": installedfilepath,
                    "installed": True
                }
                installed_packages[package_name] = pkginfo
                save_installed_packages(installed_packages)
                print(f"Package {package_name} installed via installer.")
                return
            except Exception as e:
                print(f"Error running installer: {e}")
                return
        # Normal app install
        installed_packages[package_name] = {"commands": [], "dependencies": {"python": [], "apt": []}}
        for file in package_dir.rglob("*"):
            if file.suffix in [".py", ".sh"]:
                command_name = file.stem
                installed_packages[package_name]["commands"].append(str(file))
                print(f"Adding command: {command_name}")
        save_installed_packages(installed_packages)
        print(f"Package {package_name} installed successfully.")
        print("Updating the list of installed modules...")
        update_installed_modules()
        requirements_file = None
        apt_file = None
        for root, _, files in os.walk(package_dir):
            if "requirements.txt" in files:
                requirements_file = Path(root) / "requirements.txt"
            if "apt.txt" in files:
                apt_file = Path(root) / "apt.txt"
        if requirements_file or apt_file:
            print("\nDependencies found:")
            if requirements_file:
                print(f"- Python dependencies (from {requirements_file}):")
                with open(requirements_file, "r") as f:
                    python_packages = [line.strip() for line in f if line.strip()]
                    print("\n".join(python_packages))
            else:
                python_packages = []
            if apt_file:
                print(f"- System dependencies (from {apt_file}):")
                with open(apt_file, "r") as f:
                    apt_packages = [line.strip() for line in f if line.strip()]
                    print("\n".join(apt_packages))
            else:
                apt_packages = []
            # Update pip and apt package lists before dependency install
            update_installed_modules()
            try:
                result = subprocess.run(["dpkg-query", "-W", "-f=${Package}\n"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    installed_apt_packages = result.stdout.strip().split("\n")
                else:
                    installed_apt_packages = []
            except Exception:
                installed_apt_packages = []
            installed_modules = load_installed_modules()
            python_packages_to_install = [pkg for pkg in python_packages if pkg not in installed_modules]
            apt_packages_to_install = [pkg for pkg in apt_packages if pkg not in installed_apt_packages]
            if not python_packages_to_install and not apt_packages_to_install:
                print("All dependencies are already installed.")
                return
            install_deps = input("\nDo you want to install these dependencies? (y/n): ").lower()
            if install_deps == "y":
                for package in python_packages_to_install:
                    print(f"Installing Python package: {package}")
                    try:
                        process = subprocess.Popen(["pip3", "install", "--break-system-packages", package], stdout=sys.stdout, stderr=sys.stderr)
                        process.communicate()
                        if process.returncode != 0:
                            print(f"pip3 failed. Trying pip...")
                            process = subprocess.Popen(["pip", "install", "--break-system-packages", package], stdout=sys.stdout, stderr=sys.stderr)
                            process.communicate()
                            if process.returncode != 0:
                                raise Exception(f"Failed to install {package}")
                        installed_packages[package_name]["dependencies"]["python"].append(package)
                    except Exception as e:
                        print(f"Error: {package} could not be installed because {e}.")
                        continue_install = input("Do you want to continue installation? (y/n): ").lower()
                        if continue_install == "n":
                            print("Uninstalling package...")
                            lpm_remove(package_name)
                            return
                        elif continue_install == "y":
                            print(f"Skipping {package} and continuing installation.")
                        else:
                            print("Invalid input. Skipping dependency installation.")
                            return
                for package in apt_packages_to_install:
                    print(f"Installing system package: {package}")
                    try:
                        subprocess.run(["sudo", "apt", "update"], check=True)
                        process = subprocess.Popen(["sudo", "apt", "install", "-y", package], stdout=sys.stdout, stderr=sys.stderr)
                        process.communicate()
                        if process.returncode != 0:
                            raise Exception(f"Failed to install {package}")
                        installed_packages[package_name]["dependencies"]["apt"].append(package)
                    except Exception as e:
                        print(f"Error: {package} could not be installed because {e}.")
                        continue_install = input("Do you want to continue installation? (y/n): ").lower()
                        if continue_install == "n":
                            print("Uninstalling package...")
                            lpm_remove(package_name)
                            return
                        elif continue_install == "y":
                            print(f"Skipping {package} and continuing installation.")
                        else:
                            print("Invalid input. Skipping dependency installation.")
                            return
            elif install_deps == "n":
                print("Skipping dependency installation.")
            else:
                print("Invalid input. Skipping dependency installation.")
        else:
            print("No dependencies found.")
        save_installed_packages(installed_packages)
        update_installed_modules()
        print("Installation complete.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading package: {e}")
    except Exception as e:
        print(f"Error installing package: {e}")

def lpm_remove(package_name):
    # Block root usage
    if os.geteuid() == 0:
        print("Do not run lpm as root. Exiting.")
        sys.exit(1)
    print(f"Removing package: {package_name}")
    package_dir = LPM_DIR / package_name
    installed_packages = load_installed_packages()
    if not package_dir.exists() and package_name not in installed_packages:
        print(f"Package {package_name} is not installed.")
        return
    try:
        installer_mode = False
        installeddirpath = None
        installedfilepath = None
        username = os.environ.get("USER") or os.environ.get("LOGNAME") or os.getlogin()
        if package_name in installed_packages:
            pkgdata = installed_packages[package_name]
            if "installer" in pkgdata or "installerdeb" in pkgdata:
                installer_mode = True
                installeddirpath = pkgdata.get("installeddirpath")
                installedfilepath = pkgdata.get("installedfilepath")
                # Normalize to lists
                if installeddirpath:
                    if isinstance(installeddirpath, str):
                        installeddirpaths = [installeddirpath.replace("{username}", username)]
                    else:
                        installeddirpaths = [dp.replace("{username}", username) for dp in installeddirpath]
                else:
                    installeddirpaths = []
                if installedfilepath:
                    if isinstance(installedfilepath, str):
                        installedfilepaths = [installedfilepath.replace("{username}", username)]
                    else:
                        installedfilepaths = [fp.replace("{username}", username) for fp in installedfilepath]
                else:
                    installedfilepaths = []
        if installer_mode:
            print("Installer mode removal.")
            for dp in installeddirpaths:
                try:
                    if dp.startswith(str(Path.home())):
                        shutil.rmtree(dp)
                        print(f"Removed directory: {dp}")
                    else:
                        subprocess.run(["sudo", "rm", "-rf", dp], check=True)
                        print(f"Removed directory (sudo): {dp}")
                except Exception as e:
                    print(f"Error removing directory {dp}: {e}")
            for fp in installedfilepaths:
                try:
                    if fp.startswith(str(Path.home())):
                        os.remove(fp)
                        print(f"Removed file: {fp}")
                    else:
                        subprocess.run(["sudo", "rm", "-f", fp], check=True)
                        print(f"Removed file (sudo): {fp}")
                except Exception as e:
                    print(f"Error removing file {fp}: {e}")
            if package_dir.exists():
                shutil.rmtree(package_dir)
            del installed_packages[package_name]
            save_installed_packages(installed_packages)
            print(f"Package {package_name} removed successfully.")
            return
        # Normal app removal
        if package_dir.exists():
            shutil.rmtree(package_dir)
        if package_name in installed_packages:
            del installed_packages[package_name]
            save_installed_packages(installed_packages)
        print(f"Package {package_name} removed successfully.")
    except Exception as e:
        print(f"Error removing package: {e}")

def lpm_search():
    print("Searching for available packages...")
    org_url = "https://api.github.com/orgs/LFF-Linux-Packages/repos"
    try:
        response = requests.get(org_url)
        if response.status_code != 200:
            print("Failed to fetch package list.")
            return
        repos = response.json()
        for repo in repos:
            print(repo["name"])
    except Exception as e:
        print(f"Error fetching package list: {e}")

    # Removed: lpm_update
# Standalone CLI entry
def main():
    # Block root usage
    if os.geteuid() == 0:
        print("Do not run lpm as root. Exiting.")
        sys.exit(1)
    ensure_pip()
    if len(sys.argv) < 2:
        print("Usage: lpm.py <command> [args]")
        print("Commands:")
        print("  install <package>")
        print("  remove <package>")
        print("  search")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "install" and len(sys.argv) == 3:
        lpm_install(sys.argv[2])
    elif cmd == "remove" and len(sys.argv) == 3:
        lpm_remove(sys.argv[2])
    elif cmd == "search":
        lpm_search()
    else:
        print("Unknown command or missing arguments.")
        sys.exit(1)

if __name__ == "__main__":
    main()
