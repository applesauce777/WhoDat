# 🦉 Who Dat - Zero-Config Installation

## Quick Start (Recommended)

Just run the installer and double-click to start:

```bash
python install_who_dat.py
```

That's it! The installer will:
- ✅ Install all dependencies automatically
- ✅ Create desktop shortcuts for both Web and CLI interfaces
- ✅ Set up command-line tools
- ✅ Configure everything for your platform

## After Installation

### Web Interface (Easiest)
- Double-click "Who Dat Web" on your desktop
- Opens automatically in your browser at http://localhost:5000
- Upload files, preview structure, process with progress tracking

### Command Line
- Double-click "Who Dat CLI" on your desktop
- Or use the command: `who-dat input.txt output.db`

### Configuration
1. Edit `config.py` in the installation directory
2. Replace `your_license_key_here` with your MaxMind license key
3. Use the "Update Databases" button in the web interface

## Manual Installation

If you prefer manual setup:

```bash
pip install -r requirements.txt
python app.py  # Web interface
python resolve.py input.txt output.db  # CLI
```

## Features

- 🌐 **Web Interface** - User-friendly GUI with file upload
- 📊 **Multiple Formats** - Supports TXT, CSV, Excel files
- 🔍 **Smart Detection** - Automatically finds IP columns
- 📈 **Progress Tracking** - Real-time progress bars
- 💾 **Database Export** - Download SQLite results
- 🔄 **Auto Updates** - One-click MaxMind database updates
- 🖥️ **Cross-Platform** - Windows, macOS, Linux

## File Support

- **Text files** (.txt) - One IP per line
- **CSV files** (.csv) - Comma-separated values
- **Excel files** (.xlsx, .xls) - Microsoft Excel
- **TSV files** (.tsv) - Tab-separated values

## Troubleshooting

### "Configuration Error" 
- Edit `config.py` and add your MaxMind license key
- Get a free key from https://www.maxmind.com

### "No valid IPs found"
- Use the file preview feature to check column detection
- Ensure IP addresses are in a valid format (xxx.xxx.xxx.xxx)

### Dependencies Issues
- Run the installer again: `python install_resolver.py`
- Or manually: `pip install -r requirements.txt`

## Advanced Usage

### CLI Options
```bash
python resolve.py input.csv output.db --batch-size 500
python mmupdate.py  # Update databases
```

### Web Interface Features
- File upload with preview
- Automatic IP column detection
- Real-time progress tracking
- Searchable results table
- Database download

## Installation Directory

- **Windows**: `%LOCALAPPDATA%\IPResolver`
- **macOS**: `~/.local/share/ip-resolver`
- **Linux**: `~/.local/share/ip-resolver`
