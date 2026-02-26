#!/usr/bin/env python3
# LFF shell replacement – lsh.py
import os
import time
import subprocess
import getpass
import socket
import readline  # For command history and tab completion
from pathlib import Path
import sys
import signal
import argparse
import shlex
import re

CONFIG_DIR = Path.home() / ".config/lff-linux"
HISTORY_FILE = CONFIG_DIR / "history.txt"

def admin_menu():
    load_history()  # Load history at the start
    username = getpass.getuser()

    # Handle terminal resize (SIGWINCH) to redraw prompt only once per resize event
    def handle_sigwinch(signum, frame):
        readline.redisplay()
    signal.signal(signal.SIGWINCH, handle_sigwinch)

    while True:
        try:
            command = input(get_prompt()).strip()
            if command:
                append_history(command)
            if command.startswith("cd "):
                path = command[3:].strip()
                change_directory(path)
            elif command == "clear":
                clear_screen()
            elif command == "history":
                show_history()
            elif command == "exit":
                print('Exiting...')
                time.sleep(2)
                break
            elif command == "":
                continue
            elif command == (" ") or command == ("  "):
                continue
            elif command == "help":
                print('Available commands: cd <path>, clear, history, cmds, snake, calc, exit')
                print('Additionally, you can run system commands.')
            else:
                if not execute_command(command):
                    execute_system_command(command)
        except KeyboardInterrupt:
            print("")
            continue
        except EOFError:
            print("logout")
            sys.exit(0)
        except Exception as e:
            print(f"Unexpected error in admin_menu: {e}")


# Ensure config directory exists
def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Load command history from file
def load_history():
    ensure_config_dir()
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r") as file:
            for line in file:
                readline.add_history(line.strip())

# Append a command to the history file
def append_history(command):
    ensure_config_dir()
    with open(HISTORY_FILE, "a") as file:
        file.write(command + "\n")

def show_history():
    for i in range(1, readline.get_current_history_length() + 1):
        print(f"{i}: {readline.get_history_item(i)}")

def execute_command(command):
    try:
        # Handle running `lsh` inside itself
        if command == "lsh" or command == "python3 lsh.py":
            try:
                subprocess.run([sys.executable, __file__])
            except Exception as e:
                print(f"Error running lsh: {e}")
            return True

        # Parse command and arguments
        args = shlex.split(command)
        if not args:
            return False

        executable = args[0]
        # Search for executable in PATH
        def find_executable(executable):
            if os.path.isabs(executable) and os.access(executable, os.X_OK):
                return executable
            for path_dir in os.environ.get("PATH", "").split(":"):
                exe_path = os.path.join(path_dir, executable)
                if os.access(exe_path, os.X_OK):
                    return exe_path
            return None

        exe_path = find_executable(executable)
        if exe_path:
            try:
                result = subprocess.run([exe_path] + args[1:], shell=False)
                if result.returncode != 0:
                    print(f"Error: Command '{command}' failed with exit code {result.returncode}.")
            except Exception as e:
                print(f"Error running {executable}: {e}")
            return True
        else:
            print(f"Error: Command '{executable}' not found.")
            return True
    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        return False

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

def get_prompt():
    # Bash-style color prompt using ANSI escape codes
    username = getpass.getuser()
    hostname = socket.gethostname()
    current_dir = os.getcwd()
    home_dir = str(Path.home())
    if current_dir.startswith(home_dir):
        current_dir = current_dir.replace(home_dir, "~", 1)

    # Default bash-like colored prompt with readline markers for non-printing chars
    def wrap_ansi(s):
        # Wrap all ANSI escape sequences with \001 and \002
        return re.sub(r'(\033\[[0-9;]+m)', r'\001\1\002', s)

    default_ps1 = wrap_ansi(f"\033[1;32m{username}@{hostname}\033[0m:\033[1;34m{current_dir}\033[0m$ ")

    # Try to read PS1 from ~/.bashrc for compatibility
    bashrc_path = Path.home() / ".bashrc"
    ps1 = None
    if bashrc_path.exists():
        try:
            with open(bashrc_path, "r") as f:
                for line in f:
                    if line.strip().startswith("PS1="):
                        # Remove PS1= and possible quotes
                        ps1 = line.strip()[4:].strip('"\'')
                        break
        except Exception:
            pass

    # If PS1 found, try to substitute bash variables and color codes
    if ps1:
        # Expand environment variables and bash parameter expansions
        def bash_var_expand(match):
            expr = match.group(1)
            # Handle ${debian_chroot:+($debian_chroot)}
            if expr.startswith('debian_chroot:+('):
                var = os.environ.get('debian_chroot', '')
                return f'({var})' if var else ''
            # Simple env var
            return os.environ.get(expr, '')

        # Replace ${...} with env values
        ps1 = re.sub(r'\${([^}]+)}', bash_var_expand, ps1)

        # Replace \u, \h, \w, \W, \$ with Python equivalents
        ps1 = ps1.replace('\\u', username)
        ps1 = ps1.replace('\\h', hostname)
        ps1 = ps1.replace('\\w', current_dir)
        ps1 = ps1.replace('\\W', os.path.basename(current_dir))
        ps1 = ps1.replace('\\$', '$')

        # Replace literal \033 with \x1b (ESC)
        ps1 = ps1.replace('033', 'x1b')
        # Replace \[ and \] with nothing (bash uses these for non-printing chars)
        ps1 = ps1.replace('\\[', '').replace('\\]', '')

        # Replace \x1b[...m with actual ANSI codes
        ps1 = re.sub(r'\\x1b\[([0-9;]+)m', lambda m: f'\033[{m.group(1)}m', ps1)

        # Wrap all ANSI escape sequences with \001 and \002 for readline
        ps1 = re.sub(r'(\033\[[0-9;]+m)', r'\001\1\002', ps1)
        return ps1
    else:
        # Use default colored prompt
        return default_ps1

def is_interactive_command(command):
    """Determine if a command is likely to be interactive."""
    interactive_commands = ["nano", "vim", "top", "htop", "less", "more", "man"]
    # Check if the command starts with any known interactive command
    return any(command.split()[0] == cmd for cmd in interactive_commands)

def execute_system_command(command):
    """Execute a system command and stream its output in real-time. Also add to history."""
    try:
        # Add to history immediately (if not already added)
        readline.add_history(command)
        append_history(command)
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

def handle_signals():
    """Handle system signals like SIGINT and SIGTERM."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignore SIGINT (Ctrl+C)
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

def setup_environment():
    """Set up the environment for the shell, mimicking bash as closely as possible."""
    bashrc_path = Path.home() / ".bashrc"
    # Set HOME, USER, LOGNAME, SHELL, PWD
    os.environ["HOME"] = str(Path.home())
    os.environ["USER"] = getpass.getuser()
    os.environ["LOGNAME"] = os.environ.get("USER", getpass.getuser())
    os.environ["SHELL"] = os.environ.get("SHELL", "/bin/bash")
    os.environ["PWD"] = os.getcwd()

    # Set PATH from bashrc if not already set
    if "PATH" not in os.environ or not os.environ["PATH"]:
        path_val = None
        if bashrc_path.exists():
            with open(bashrc_path, "r") as f:
                for line in f:
                    m = re.match(r'\s*export\s+PATH=(.*)', line)
                    if m:
                        # Remove possible quotes
                        path_val = m.group(1).strip().strip('"\'')
                        break
        if path_val:
            os.environ["PATH"] = path_val
        else:
            # Fallback to system default
            os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    # Set locale variables from bashrc if present, else inherit or fallback
    locale_vars = [
        "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", "LC_COLLATE", "LC_MONETARY", "LC_MESSAGES", "LC_PAPER", "LC_NAME", "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT", "LC_IDENTIFICATION"
    ]
    if bashrc_path.exists():
        with open(bashrc_path, "r") as f:
            bashrc_lines = f.readlines()
        for var in locale_vars:
            for line in bashrc_lines:
                m = re.match(rf'\s*export\s+{var}=(.*)', line)
                if m:
                    val = m.group(1).strip().strip('"\'')
                    os.environ[var] = val
                    break
    # Fallback: if not set, try to inherit from current env or set to C
    for var in locale_vars:
        if var not in os.environ:
            os.environ[var] = os.environ.get(var, "C")

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
        ensure_config_dir()
        args = parse_arguments()

        if args.version:
            print("Lff SHell version 1.2.0")
            sys.exit(0)

        handle_signals()
        setup_environment()

        # Disable Tab key (make it do nothing)
        # I do not know how to make it autocomplete without breaking the shell, so for now it just does nothing
        readline.parse_and_bind('tab: ignore')

        if args.login:
            os.environ["LOGIN_SHELL"] = "1"
            clear_screen()

        if args.command:
            # Add to history immediately (like bash)
            readline.add_history(args.command)
            append_history(args.command)
            # Execute the provided command and exit
            try:
                if not execute_command(args.command):
                    execute_system_command(args.command)
            except Exception as e:
                print(f"Error executing command: {e}")
            sys.exit(0)
            
        # Start the interactive shell
        admin_menu()
    except Exception as e:
        print(f"Critical error in main: {e}")
        time.sleep(2)
        os._exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        time.sleep(2)
        os._exit(1)