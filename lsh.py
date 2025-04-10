#!/usr/bin/env python3
# LFF shell replacement – lsh.py
import os
import time
import random
import curses
import subprocess
import requests
import zipfile
import shutil
import json
import getpass
import socket
import readline  # For command history
from pathlib import Path
import sys
import signal
import argparse

LPM_DIR = Path.home() / ".config/lff-linux/packages"
INSTALLED_PACKAGES_FILE = Path.home() / ".config/lff-linux/installed_packages.json"
HISTORY_FILE = Path.home() / ".config/lff-linux/history.txt"
INSTALLED_MODULES_FILE = Path.home() / ".config/lff-linux/installed_modules.json"
INSTALLED_APT_PACKAGES_FILE = Path.home() / ".config/lff-linux/installed_apt_packages.json"

# Load command history from file
def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r") as file:
            for line in file:
                readline.add_history(line.strip())

# Save command history to file
def save_history():
    with open(HISTORY_FILE, "w") as file:
        for i in range(readline.get_current_history_length()):
            file.write(readline.get_history_item(i + 1) + "\n")

# Display command history
def show_history():
    for i in range(1, readline.get_current_history_length() + 1):
        print(f"{i}: {readline.get_history_item(i)}")

def read_file(filename, default_value):
    try:
        with open(filename, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return default_value

def write_file(filename, value):
    with open(filename, "w") as file:
        file.write(value)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_installed_packages():
    if INSTALLED_PACKAGES_FILE.exists():
        with open(INSTALLED_PACKAGES_FILE, "r") as file:
            return json.load(file)
    return {}

def save_installed_packages(packages):
    with open(INSTALLED_PACKAGES_FILE, "w") as file:
        json.dump(packages, file, indent=4)

def load_installed_modules():
    """Load the list of globally installed modules."""
    if INSTALLED_MODULES_FILE.exists():
        with open(INSTALLED_MODULES_FILE, "r") as file:
            return json.load(file)
    return []

def save_installed_modules(modules):
    """Save the list of globally installed modules."""
    with open(INSTALLED_MODULES_FILE, "w") as file:
        json.dump(modules, file, indent=4)

def update_installed_modules():
    """Update the installed modules list by checking the system."""
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

def load_installed_apt_packages():
    """Load the list of globally installed APT packages."""
    if INSTALLED_APT_PACKAGES_FILE.exists():
        with open(INSTALLED_APT_PACKAGES_FILE, "r") as file:
            return json.load(file)
    return []

def save_installed_apt_packages(packages):
    """Save the list of globally installed APT packages."""
    with open(INSTALLED_APT_PACKAGES_FILE, "w") as file:
        json.dump(packages, file, indent=4)

def update_installed_apt_packages():
    """Update the installed APT packages list by checking the system."""
    try:
        result = subprocess.run(["dpkg-query", "-W", "-f=${Package}\n"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            installed_apt_packages = result.stdout.strip().split("\n")
            save_installed_apt_packages(installed_apt_packages)
        else:
            print(f"Error updating installed APT packages: {result.stderr.strip()}")
    except Exception as e:
        print(f"Error updating installed APT packages: {e}")

def play_snake():
    def play_game(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(100)

        height, width = stdscr.getmaxyx()

        snake_x = width // 4
        snake_y = height // 2
        snake = [
            [snake_y, snake_x],
            [snake_y, snake_x - 1],
            [snake_y, snake_x - 2]
        ]
        direction = curses.KEY_RIGHT

        food_size = 3
        food_x = random.randint(food_size, width - food_size)
        food_y = random.randint(food_size, height - food_size)
        food = [food_y, food_x]

        score = 0

        while True:
            key = stdscr.getch()

            if key == ord('q'):
                curses.endwin()
                clear_screen()
                print("Quitting...")
                time.sleep(2)
                clear_screen()
                admin_menu()

            if key == curses.KEY_DOWN and direction != curses.KEY_UP:
                direction = curses.KEY_DOWN
            elif key == curses.KEY_UP and direction != curses.KEY_DOWN:
                direction = curses.KEY_UP
            elif key == curses.KEY_LEFT and direction != curses.KEY_RIGHT:
                direction = curses.KEY_LEFT
            elif key == curses.KEY_RIGHT and direction != curses.KEY_LEFT:
                direction = curses.KEY_RIGHT

            head = snake[0][:]
            if direction == curses.KEY_DOWN:
                head[0] += 1
            elif direction == curses.KEY_UP:
                head[0] -= 1
            elif direction == curses.KEY_LEFT:
                head[1] -= 1
            elif direction == curses.KEY_RIGHT:
                head[1] += 1

            snake.insert(0, head)
            if head == food:
                food_x = random.randint(food_size, width - food_size)
                food_y = random.randint(food_size, height - food_size)
                food = [food_y, food_x]
                score += 1
            else:
                tail = snake.pop()

            if (
                head[0] == 0
                or head[0] == height - 1
                or head[1] == 0
                or head in snake[1:]
            ):
                curses.endwin()
                clear_screen()
                print("Game Over!")
                print("Score:", score)
                time.sleep(2)
                print("Would you like to try again? (y/n)")
                if input('> ').lower() == 'y':
                    clear_screen()
                    play_snake()
                else:
                    clear_screen()
                    print('Quitting...')
                    time.sleep(2)
                    clear_screen()
                    admin_menu()

            new_height, new_width = stdscr.getmaxyx()
            if new_height != height or new_width != width:
                height, width = new_height, new_width

            stdscr.erase()
            stdscr.border()
            stdscr.addch(food[0], food[1], '*', curses.A_BOLD)
            for segment in snake:
                stdscr.addch(segment[0], segment[1], '#', curses.A_BOLD)
            stdscr.addstr(0, 2, "Score: " + str(score), curses.A_BOLD)
            stdscr.refresh()

    curses.wrapper(play_game)

def calculator():
    def calculate(n1, n2, op):
        if op == '+':
            result = n1 + n2
        elif op == '-':
            result = n1 - n2
        elif op == '*':
            result = n1 * n2
        elif op == '/':
            result = n1 / n2
        elif op == '^':
            result = n1 ** n2
        else:
            raise ValueError('Invalid operator')

        if result.is_integer():
            result = int(result)

        return result

    while True:
        try:
            number1 = float(input('Enter first number: '))
            op = input('Enter operator (+,-,*,/,^): ')
            number2 = float(input('Enter second number: '))
            result = calculate(number1, number2, op)
            print('=', result)
            if input('Continue? (y/n): ').lower() != 'y':
                break
        except Exception as e:
            print('Error:', e)
            print('Restarting application...')

def lpm_install(package_name):
    clear_screen()
    print(f"Installing package: {package_name}")

    # Check if the package is already installed
    installed_packages = load_installed_packages()
    if package_name in installed_packages:
        print(f"Package {package_name} is already installed.")
        return

    repo_url = f"https://github.com/LFF-Linux-Packages/{package_name}/archive/refs/heads/main.zip"
    package_dir = LPM_DIR / package_name

    try:
        # Create package directory if it doesn't exist
        package_dir.mkdir(parents=True, exist_ok=True)

        # Download the package
        response = requests.get(repo_url, stream=True)
        if response.status_code != 200:
            print(f"Failed to fetch package: {package_name}")
            return
        zip_path = package_dir / "package.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # Extract the package
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(package_dir)
        zip_path.unlink()  # Remove the zip file

        # Add commands to installed packages
        installed_packages[package_name] = {"commands": [], "dependencies": {"python": [], "apt": []}}
        for file in package_dir.rglob("*"):
            if file.suffix in [".py", ".sh"]:
                command_name = file.stem
                installed_packages[package_name]["commands"].append(str(file))
                print(f"Adding command: {command_name}")
        save_installed_packages(installed_packages)

        print(f"Package {package_name} installed successfully.")

        # Update the list of installed modules and APT packages
        print("Updating the list of installed modules and APT packages...")
        update_installed_modules()
        update_installed_apt_packages()
        
        # Recursively search for requirements.txt and apt.txt
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

            # Load installed modules and APT packages
            installed_modules = load_installed_modules()
            installed_apt_packages = load_installed_apt_packages()

            # Filter out already installed dependencies
            python_packages_to_install = [pkg for pkg in python_packages if pkg not in installed_modules]
            apt_packages_to_install = [pkg for pkg in apt_packages if pkg not in installed_apt_packages]

            if not python_packages_to_install and not apt_packages_to_install:
                print("All dependencies are already installed.")
                return

            # Ask the user if they want to install dependencies
            install_deps = input("\nDo you want to install these dependencies? (y/n): ").lower()
            if install_deps == "y":
                # Install Python dependencies
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

                # Install APT dependencies
                for package in apt_packages_to_install:
                    print(f"Installing system package: {package}")
                    try:
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
        update_installed_modules()  # Update the installed modules list
        update_installed_apt_packages()  # Update the installed APT packages list
        print("Installation complete.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading package: {e}")
    except Exception as e:
        print(f"Error installing package: {e}")

def lpm_remove(package_name):
    clear_screen()
    print(f"Removing package: {package_name}")
    package_dir = LPM_DIR / package_name

    if not package_dir.exists():
        print(f"Package {package_name} is not installed.")
        return

    try:
        # Remove the package directory
        shutil.rmtree(package_dir)

        # Remove from installed packages
        installed_packages = load_installed_packages()
        if package_name in installed_packages:
            del installed_packages[package_name]
            save_installed_packages(installed_packages)

        print(f"Package {package_name} removed successfully.")
    except Exception as e:
        print(f"Error removing package: {e}")

def lpm_search():
    clear_screen()
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

def lpm_update():
    clear_screen()
    print("Updating all installed packages...")
    installed_packages = load_installed_packages()
    update_installed_modules()  # Update the installed modules list
    update_installed_apt_packages()  # Update the installed APT packages list
    installed_modules = load_installed_modules()
    installed_apt_packages = load_installed_apt_packages()

    all_updates_successful = True  # Track if all updates are successful

    for package_name, package_data in installed_packages.items():
        print(f"Updating package: {package_name}")
        package_dir = LPM_DIR / package_name

        # Validate package_data structure
        if not isinstance(package_data, dict) or "dependencies" not in package_data:
            print(f"Error: Invalid data structure for package '{package_name}'. Skipping...")
            all_updates_successful = False
            continue

        # Re-download the package
        repo_url = f"https://github.com/LFF-Linux-Packages/{package_name}/archive/refs/heads/main.zip"
        try:
            response = requests.get(repo_url, stream=True)
            if response.status_code != 200:
                print(f"Failed to fetch package: {package_name}. Skipping...")
                all_updates_successful = False
                continue
            zip_path = package_dir / "package.zip"
            with open(zip_path, "wb") as f:
                f.write(response.content)

            # Extract the package
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(package_dir)
            zip_path.unlink()  # Remove the zip file
            print(f"Package {package_name} re-downloaded successfully.")
        except Exception as e:
            print(f"Error re-downloading package {package_name}: {e}")
            all_updates_successful = False
            continue

        # Recursively search for requirements.txt and apt.txt
        requirements_file = None
        apt_file = None
        for root, _, files in os.walk(package_dir):
            if "requirements.txt" in files:
                requirements_file = Path(root) / "requirements.txt"
            if "apt.txt" in files:
                apt_file = Path(root) / "apt.txt"

        dependencies = package_data.get("dependencies", {})
        installed_python = dependencies.get("python", [])
        installed_apt = dependencies.get("apt", [])

        new_python_packages = []
        new_apt_packages = []

        if requirements_file:
            with open(requirements_file, "r") as f:
                python_packages = [line.strip() for line in f if line.strip()]
                new_python_packages = [pkg for pkg in python_packages if pkg not in installed_python and pkg not in installed_modules]

        if apt_file:
            with open(apt_file, "r") as f:
                apt_packages = [line.strip() for line in f if line.strip()]
                new_apt_packages = [pkg for pkg in apt_packages if pkg not in installed_apt and pkg not in installed_apt_packages]

        if new_python_packages or new_apt_packages:
            print(f"New dependencies found for {package_name}:")
            if new_python_packages:
                print(f"- Python: {', '.join(new_python_packages)}")
            if new_apt_packages:
                print(f"- APT: {', '.join(new_apt_packages)}")

            install_deps = input("Do you want to install these new dependencies? (y/n): ").lower()
            if install_deps == "y":
                for package in new_python_packages:
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
                        installed_python.append(package)
                    except Exception as e:
                        print(f"Error: {package} could not be installed because {e}.")
                        all_updates_successful = False

                for package in new_apt_packages:
                    print(f"Installing system package: {package}")
                    try:
                        process = subprocess.Popen(["sudo", "apt", "install", "-y", package], stdout=sys.stdout, stderr=sys.stderr)
                        process.communicate()
                        if process.returncode != 0:
                            raise Exception(f"Failed to install {package}")
                        installed_apt.append(package)
                    except Exception as e:
                        print(f"Error: {package} could not be installed because {e}.")
                        all_updates_successful = False
            elif install_deps == "n":
                print(f"Skipping new dependencies for {package_name}.")
            else:
                print("Invalid input. Skipping new dependencies.")
                all_updates_successful = False

        # Update the dependencies in the installed packages
        package_data["dependencies"]["python"] = installed_python
        package_data["dependencies"]["apt"] = installed_apt

    save_installed_packages(installed_packages)
    update_installed_modules()  # Update the installed modules list again
    update_installed_apt_packages()  # Update the installed APT packages list again

    if all_updates_successful:
        print("All packages updated successfully.")
    else:
        print("Some packages failed to update. Please check the errors above.")

def execute_command(command):
    try:
        installed_packages = load_installed_packages()
        for package_name, package_data in installed_packages.items():
            # Ensure package_data has the expected structure
            if not isinstance(package_data, dict) or "commands" not in package_data:
                print(f"Error: Invalid data structure for package '{package_name}'. Skipping...")
                continue

            # Iterate over the commands in the package
            for file_path in package_data["commands"]:
                file = Path(file_path)
                if file.stem == command:
                    try:
                        if file.suffix == ".py":
                            exec(open(file).read(), globals())
                        elif file.suffix == ".sh":
                            subprocess.run(["bash", str(file)])
                        return True
                    except Exception as e:
                        print(f"Error executing LPM-Installed command '{command}': {e}")
                        return True  # Prevent fallback to system command

        # Handle running `lsh` inside itself
        if command == "lsh":
            try:
                subprocess.run([sys.executable, __file__])
            except Exception as e:
                print(f"Error running lsh: {e}")
            return True
        if command == "python3 lsh.py" or command == "/bin/python3 /home/core/Python/lsh.py":
            try:
                subprocess.run([sys.executable, __file__])
            except Exception as e:
                print(f"Error running lsh: {e}")
            return True
        # Handle running other shells like sh, bash, ash, etc.
        if command in ["sh", "bash", "ash", "zsh", "dash"]:
            try:
                subprocess.run([command])
            except FileNotFoundError:
                print(f"Error: {command} is not installed or not in PATH.")
            except Exception as e:
                print(f"Error running {command}: {e}")
            return True

        return False
    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        return False

def get_prompt():
    username = getpass.getuser()
    hostname = socket.gethostname()
    current_dir = os.getcwd()
    home_dir = str(Path.home())
    if current_dir.startswith(home_dir):
        current_dir = current_dir.replace(home_dir, "~", 1)
    return f"{username}@{hostname}:{current_dir}$ "

def is_interactive_command(command):
    """Determine if a command is likely to be interactive."""
    interactive_commands = ["nano", "vim", "top", "htop", "less", "more", "man"]
    # Check if the command starts with any known interactive command
    return any(command.split()[0] == cmd for cmd in interactive_commands)

def execute_system_command(command):
    """Execute a system command and stream its output in real-time."""
    try:
        if is_interactive_command(command):
            # Run interactive commands with terminal inheritance
            subprocess.run(command, shell=True)
        else:
            # Stream non-interactive commands in real-time
            process = subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
            process.communicate()
            if process.returncode != 0:
                print(f"Error: Command '{command}' failed with exit code {process.returncode}.")
    except Exception as e:
        print(f"Error executing system command '{command}': {e}")

def change_directory(path):
    try:
        if path == "~":
            os.chdir(Path.home())
        else:
            os.chdir(os.path.expanduser(path))
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {path}: Not a directory")
    except PermissionError:
        print(f"cd: {path}: Permission denied")

def show_installed_commands():
    """Display all commands installed by lpm."""
    installed_packages = load_installed_packages()
    print("Installed commands:")
    for package_name, package_data in installed_packages.items():
        if "commands" in package_data:
            print(f"\nPackage: {package_name}")
            for command_path in package_data["commands"]:
                command_name = Path(command_path).stem
                print(f"  - {command_name}")
            print("")

def admin_menu():
    load_history()  # Load history at the start
    username = getpass.getuser()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f'Welcome {username}! Type "help" to view commands.')
    while True:
        try:
            command = input(get_prompt()).strip()
            if command.startswith("cd "):
                path = command[3:].strip()
                change_directory(path)
            elif command == "clear":
                clear_screen()
            elif command == "history":
                show_history()
            elif command == "cmds":
                show_installed_commands()
            elif command == 'snake':
                play_snake()
            elif command == 'calc':
                calculator()
            elif command == 'lpm':
                print('LFF Linux Package Manager')
                print('Available commands: install, remove, search, update')
            elif command == ('lpm install'):
                print('Usage: lpm install <package_name>')
            elif command == ('lpm remove'): 
                print('Usage: lpm remove <package_name>')
            elif command.startswith('lpm install '):
                package_name = command.split(' ', 2)[2]
                lpm_install(package_name)
            elif command.startswith('lpm remove '):
                package_name = command.split(' ', 2)[2]
                lpm_remove(package_name)
            elif command == 'lpm search':
                lpm_search()
            elif command == 'lpm update':
                lpm_update()
            elif command == "exit":
                print('Exiting...')
                time.sleep(2)
                break
            elif command == "":
                continue
            elif command == (" ") or command == ("  "):
                continue
            elif command == "help":
                print('Available commands: cd <path>, clear, history, cmds, snake, calc, lpm install <package>, lpm remove <package>, lpm search, lpm update, exit')
                print('Additionally, you can run installed package commands directly or system commands.')
            else:
                if not execute_command(command):
                    execute_system_command(command)
        except KeyboardInterrupt:
            # Ignore Ctrl+C and print a new prompt
            print("\n[!] Interrupted. Press 'Ctrl+D' to exit.")
        except EOFError:
            # Exit the shell on Ctrl+D
            print("logout")
            save_history()  # Save history before exiting
            break
        except Exception as e:
            print(f"Unexpected error in admin_menu: {e}")
    save_history()  # Save history on exit

def handle_signals():
    """Handle system signals like SIGINT and SIGTERM."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignore SIGINT (Ctrl+C)
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

def setup_environment():
    """Set up the environment for the shell."""
    os.environ["SHELL"] = __file__
    os.environ["USER"] = getpass.getuser()
    os.environ["HOME"] = str(Path.home())
    # Ensure compatibility with VS Code's integrated terminal
    os.environ["TERM"] = "xterm-256color"
    os.environ["COLORTERM"] = "truecolor"

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="LFF Shell Replacement")
    parser.add_argument("-l", "--login", action="store_true", help="Run as a login shell")
    parser.add_argument("-c", "--command", type=str, help="Execute a single command and exit")
    parser.add_argument("--version", action="store_true", help="Display version information and exit")
    return parser.parse_args()

def main():
    try:
        args = parse_arguments()

        if args.version:
            print("Lff SHell version 1.1.0")
            sys.exit(0)

        handle_signals()
        setup_environment()

        if args.login:
            os.environ["LOGIN_SHELL"] = "1"
            clear_screen()

        if args.command:
            # Execute the provided command and exit
            try:
                if not execute_command(args.command):
                    execute_system_command(args.command)
            except Exception as e:
                print(f"Error executing command: {e}")
            sys.exit(0)

        update_installed_apt_packages()
        update_installed_modules()
        # Start the interactive shell
        admin_menu()
    except Exception as e:
        print(f"Critical error in main: {e}")
        time.sleep(2)
        os._exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Exiting LFF Shell...")
        time.sleep(1)
        os._exit(0)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        time.sleep(2)
        os._exit(1)
