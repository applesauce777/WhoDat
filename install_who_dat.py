#!/usr/bin/env python3
"""
Who Dat - Cross-Platform Installer
Automatically detects OS and installs Who Dat IP Resolver with appropriate shortcuts.

Usage:
    python install_who_dat.py [--no-shortcuts] [--install-dir PATH]
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

__version__ = "1.0.0"

# ANSI colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'
    
    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.CYAN = cls.NC = ''

# Disable colors on Windows if not supported
if sys.platform == 'win32':
    try:
        os.system('color')
    except:
        Colors.disable()


def print_banner():
    print(f"""
{Colors.CYAN}==============================================={Colors.NC}
{Colors.CYAN}   🦉 Who Dat v{__version__} - Installer{Colors.NC}
{Colors.CYAN}   IP Geolocation Resolver{Colors.NC}
{Colors.CYAN}==============================================={Colors.NC}
""")


def print_step(num, total, msg):
    print(f"{Colors.YELLOW}[{num}/{total}] {msg}{Colors.NC}")


def print_success(msg):
    print(f"  {Colors.GREEN}✓ {msg}{Colors.NC}")


def print_error(msg):
    print(f"  {Colors.RED}✗ {msg}{Colors.NC}")


def get_platform():
    if sys.platform == 'win32':
        return 'windows'
    elif sys.platform == 'darwin':
        return 'macos'
    else:
        return 'linux'


def get_default_install_dir(platform):
    home = Path.home()
    if platform == 'windows':
        return home / 'AppData' / 'Local' / 'WhoDat'
    else:
        return home / '.local' / 'share' / 'who-dat'


def check_python():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Python 3.7+ required. Found: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_dependencies(install_dir):
    req_file = install_dir / 'requirements.txt'
    try:
        if req_file.exists():
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(req_file), '-q'],
                          check=True, capture_output=True)
        else:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 
                          'flask', 'geoip2', 'requests', 'pandas', 'openpyxl', 'tqdm', '-q'],
                          check=True, capture_output=True)
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def copy_files(source_dir, install_dir):
    files_to_copy = ['app.py', 'resolve.py', 'mmupdate.py', 'file_parser.py', 
                     'config.py', 'requirements.txt', 'README.md', 'launcher.py']
    copied = 0
    
    for filename in files_to_copy:
        src = source_dir / filename
        if src.exists():
            shutil.copy2(src, install_dir / filename)
            copied += 1
    
    # Copy icons folder if exists
    icons_src = source_dir / 'icons'
    icons_dst = install_dir / 'icons'
    if icons_src.exists():
        if icons_dst.exists():
            shutil.rmtree(icons_dst)
        shutil.copytree(icons_src, icons_dst)
        copied += 1
    
    # Copy templates folder if exists
    templates_src = source_dir / 'templates'
    templates_dst = install_dir / 'templates'
    if templates_src.exists():
        if templates_dst.exists():
            shutil.rmtree(templates_dst)
        shutil.copytree(templates_src, templates_dst)
        copied += 1
    
    print_success(f"Copied {copied} files to {install_dir}")
    return True


def create_windows_shortcuts(install_dir):
    """Create Windows shortcuts and batch file."""
    # Create launcher for web app only
    web_batch_path = install_dir / 'who-dat-web.bat'
    web_batch_content = f'@echo off\ncd /d "{install_dir}" && python launcher.py\n'
    web_batch_path.write_text(web_batch_content)
    
    # CLI batch file (no desktop shortcut needed)
    cli_batch_path = install_dir / 'who-dat-cli.bat'
    cli_batch_content = f'@echo off\ncd /d "{install_dir}" && echo Who Dat CLI Ready && echo. && echo Usage: python resolve.py input.txt output.db\n'
    cli_batch_path.write_text(cli_batch_content)
    
    # Create PowerShell shortcut for web app only
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$WebShortcut = $WshShell.CreateShortcut("$Desktop\\Who Dat Web.lnk")
$WebShortcut.TargetPath = "{install_dir}\\who-dat-web.bat"
$WebShortcut.WorkingDirectory = "{install_dir}"
$WebShortcut.Save()
'''
    
    try:
        subprocess.run(['powershell', '-Command', ps_script], 
                      check=True, capture_output=True)
        print_success("Created Desktop shortcut for Web app")
    except:
        print_error("Could not create shortcut (run as admin or create manually)")
    
    return True


def create_macos_app(install_dir):
    """Create macOS .app bundle."""
    home = Path.home()
    web_app_dir = home / 'Applications' / 'Who Dat Web.app'
    
    # Create Web app only - CLI users don't need icons
    create_single_macos_app(web_app_dir, install_dir, 'Web', 'app.py', 'Start Who Dat Web Interface')
    
    # CLI wrapper only (no .app bundle needed)
    bin_dir = home / '.local' / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    wrapper = bin_dir / 'who-dat'
    wrapper.write_text(f'#!/bin/bash\ncd "{install_dir}" && python3 resolve.py "$@"\n')
    wrapper.chmod(0o755)
    print_success("Created CLI wrapper: ~/.local/bin/who-dat")
    
    return True


def create_single_macos_app(app_dir, install_dir, app_type, script_file, description):
    """Create a single macOS .app bundle."""
    contents = app_dir / 'Contents'
    macos = contents / 'MacOS'
    resources = contents / 'Resources'
    
    for d in [macos, resources]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Info.plist
    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>WhoDat{app_type}</string>
    <key>CFBundleIdentifier</key><string>com.whodat.{app_type.lower()}</string>
    <key>CFBundleName</key><string>Who Dat {app_type}</string>
    <key>CFBundleVersion</key><string>{__version__}</string>
    <key>CFBundlePackageType</key><string>APPL</string>
</dict>
</plist>'''
    (contents / 'Info.plist').write_text(plist)
    
    # Launcher
    launcher = f'''#!/bin/bash
osascript -e 'tell app "Terminal" to do script "cd {install_dir} && echo Who Dat {app_type} v{__version__} && echo {description} && python3 {"launcher.py" if app_type == "Web" else script_file}"'
'''
    launcher_path = macos / f'WhoDat{app_type}'
    launcher_path.write_text(launcher)
    launcher_path.chmod(0o755)
    
    print_success(f"Created {app_dir}")


def get_terminal_command():
    """Detect available terminal emulator."""
    terminals = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'mate-terminal', 'lxterminal', 'xterm']
    for term in terminals:
        if shutil.which(term):
            return term
    return 'x-terminal-emulator'  # Fallback to Debian/Ubuntu symlink

def get_python_command():
    """Detect python command, preferring venv if active."""
    # Check if VIRTUAL_ENV is set
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        venv_python = Path(venv_path) / 'bin' / 'python'
        if venv_python.exists():
            return str(venv_python)
    
    # Check for common venv locations
    home = Path.home()
    venv_locations = [
        home / 'venvs' / 'myenv' / 'bin' / 'python',
        home / '.venv' / 'bin' / 'python',
        home / 'venv' / 'bin' / 'python',
    ]
    
    for venv_python in venv_locations:
        if venv_python.exists():
            return str(venv_python)
    
    # Fallback to system python
    return sys.executable

def create_linux_desktop(install_dir):
    """Create Linux .desktop file and CLI wrapper."""
    home = Path.home()
    
    # Detect available terminal and python
    terminal = get_terminal_command()
    python_cmd = get_python_command()
    
    # Web app .desktop file
    desktop_dir = home / '.local' / 'share' / 'applications'
    desktop_dir.mkdir(parents=True, exist_ok=True)
 # Web .desktop file only - CLI users don't need GUI shortcuts
    web_desktop_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Who Dat Web
Comment=IP geolocation web interface - Who dat IP?
Exec={terminal} --hold -e bash -c "cd {install_dir} && {python_cmd} launcher.py"
Icon={install_dir}/icons/who-dat.png
Terminal=false
Categories=Network;Science;
'''
    
    web_desktop_file = desktop_dir / 'who-dat-web.desktop'
    web_desktop_file.write_text(web_desktop_content)
    print_success("Created Web .desktop launcher")
    
    # CLI wrapper only (no desktop shortcut needed)
    bin_dir = home / '.local' / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    wrapper = bin_dir / 'who-dat'
    wrapper.write_text(f'#!/bin/bash\ncd "{install_dir}" && python3 resolve.py "$@"\n')
    wrapper.chmod(0o755)
    print_success("Created CLI wrapper: ~/.local/bin/who-dat")
    
    # Desktop shortcut for web app only
    desktop_home = home / 'Desktop'
    if desktop_home.exists():
        shutil.copy2(web_desktop_file, desktop_home / 'Who Dat Web.desktop')
        (desktop_home / 'Who Dat Web.desktop').chmod(0o755)
        print_success("Created Desktop shortcut for Web app")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Who Dat IP Resolver Installer')
    parser.add_argument('--install-dir', type=Path, help='Custom installation directory')
    parser.add_argument('--no-shortcuts', action='store_true', help='Skip shortcut creation')
    args = parser.parse_args()
    
    print_banner()
    
    platform = get_platform()
    print(f"Detected platform: {Colors.CYAN}{platform}{Colors.NC}")
    print()
    
    # Determine directories
    source_dir = Path(__file__).parent.resolve()
    install_dir = args.install_dir or get_default_install_dir(platform)
    
    total_steps = 5 if args.no_shortcuts else 6
    
    # Step 1: Check Python
    print_step(1, total_steps, "Checking Python...")
    if not check_python():
        sys.exit(1)
    
    # Step 2: Create install directory
    print_step(2, total_steps, "Creating installation directory...")
    install_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Directory: {install_dir}")
    
    # Step 3: Copy files
    print_step(3, total_steps, "Copying files...")
    copy_files(source_dir, install_dir)
    
    # Step 4: Install dependencies
    print_step(4, total_steps, "Installing dependencies...")
    install_dependencies(install_dir)
    
    # Step 5: Create platform-specific launchers
    if not args.no_shortcuts:
        print_step(5, total_steps, "Creating shortcuts...")
        if platform == 'windows':
            create_windows_shortcuts(install_dir)
        elif platform == 'macos':
            create_macos_app(install_dir)
        else:
            create_linux_desktop(install_dir)
    
    # Done
    print(f"""
{Colors.CYAN}==============================================={Colors.NC}
{Colors.GREEN}   🦉 Who Dat Installation Complete!{Colors.NC}
{Colors.CYAN}==============================================={Colors.NC}

{Colors.YELLOW}Installation directory:{Colors.NC}
  {install_dir}

{Colors.YELLOW}Web Interface Usage:{Colors.NC}
  Double-click "Who Dat Web" on desktop
  Or run: python launcher.py
  Then open: http://localhost:5000

{Colors.YELLOW}CLI Usage:{Colors.NC}
  who-dat input.txt output.db
  python resolve.py input.csv output.db --batch-size 500

{Colors.YELLOW}Database Updates:{Colors.NC}
  python mmupdate.py

{Colors.YELLOW}Configuration:{Colors.NC}
  Edit config.py to set your MaxMind license key

{Colors.CYAN}🦉 Who Dat? Find out who that IP belongs to!{Colors.NC}
""")


if __name__ == '__main__':
    main()
