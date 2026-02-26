#!/usr/bin/env python3
"""
Who Dat Launcher - Simple GUI for starting the web application
"""

import sys
import os
import subprocess
import webbrowser
from pathlib import Path
import threading
import time

def check_config():
    """Check if config.py has been set up"""
    config_file = Path(__file__).parent / 'config.py'
    if not config_file.exists():
        return False, "config.py not found"
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
            if 'your_license_key_here' in content:
                return False, "Please update config.py with your MaxMind license key"
        return True, "Configuration OK"
    except:
        return False, "Error reading config.py"

def start_flask_app():
    """Start the Flask application"""
    try:
        app_file = Path(__file__).parent / 'app.py'
        subprocess.run([sys.executable, str(app_file)])
    except Exception as e:
        print(f"Error starting app: {e}")
        input("Press Enter to exit...")

def main():
    print("🦉" + "=" * 48)
    print("🦉 Who Dat - IP Geolocation Resolver")
    print("🦉" + "=" * 48)
    
    # Check configuration
    config_ok, config_msg = check_config()
    if not config_ok:
        print(f"❌ Configuration Error: {config_msg}")
        print("\nPlease:")
        print("1. Edit config.py")
        print("2. Replace 'your_license_key_here' with your MaxMind license key")
        print("3. Run this launcher again")
        input("\nPress Enter to exit...")
        return
    
    print("✅ Configuration OK")
    print("\n🌐 Starting Who Dat Web Interface...")
    print("📝 This will open in your web browser automatically")
    print("⏹️  Close this window or press Ctrl+C to stop the server")
    print("\n🦉 Who Dat? Find out who that IP belongs to!")
    print("🦉" + "=" * 48)
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:5001')
        except:
            pass
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask app
    start_flask_app()

if __name__ == '__main__':
    main()
