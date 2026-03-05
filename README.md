# 🦉 WhoDat - IP Geolocation Resolver

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-Support%20Me-ff5f5f)](https://ko-fi.com/applesauce777)

> **Find out who that IP belongs to!** 🦉  
> An IP geolocation tool that answers the question "Who dat IP?" using MaxMind's GeoLite2 databases. Great for network analysis, security investigations, and geographic data visualization.

## ✨ Features

- 📁 **Smart File Upload** - Supports TXT, CSV, Excel, TSV files with automatic IP column detection
- 🔄 **One-Click Database Updates** - Built-in MaxMind database management
- 📊 **Real-time Progress Tracking** - Live progress bars
- 🔍 **Searchable Results** - Interactive table with filtering and search capabilities
- 💾 **Export Options** - Download results as SQLite database
- ⚡ **Batch Processing** - Efficient handling of large IP lists
- 🛡️ **IP Validation** - Automatic filtering of invalid IP addresses
- 🌍 **Geographic Data** - ISP, city, region, country, lat/long information

## 🚀 Quick Start

### Zero-Config Installation

```bash
# Clone the repository
git clone https://github.com/applesauce777/WhoDat.git
cd WhoDat

# Run the installer (cross-platform)
python install_who_dat.py

# Launch the web interface
python launcher.py
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure MaxMind license key:**
```python
# Edit config.py
LICENSE_KEY = "your_free_license_key_from_maxmind"
```

3. **Download databases:**
```bash
python mmupdate.py
```

4. **Start the web app:**
```bash
python app.py
# Visit http://localhost:5001
```

## 📖 Usage

### Web Interface (Recommended)

The **WhoDat** web interface provides:
- 📁 **Drag-and-drop file upload** with preview functionality
- 🔄 **Database update button** with progress tracking
- 📊 **Real-time processing** with animated owl states
- 🔍 **Searchable results table** with filtering
- 💾 **One-click download** of processed data

### Command Line Interface

```bash
# Basic usage
python resolve.py ips.txt output.db

# Advanced usage with custom batch size
python resolve.py ips.txt output.db --batch-size 500

# Process multiple formats
python resolve.py data.csv output.db
python resolve.py data.xlsx output.db
```

## 📊 Output Format

Results are stored in SQLite with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| ip | TEXT | IP address (primary key) |
| isp | TEXT | Internet Service Provider |
| city | TEXT | City name |
| region | TEXT | State/province/region |
| country | TEXT | Country name |
| latitude | REAL | Geographic latitude |
| longitude | REAL | Geographic longitude |

## 🛠️ Development

### Project Structure
```
WhoDat/
├── app.py              # Flask web application
├── resolve.py          # CLI interface
├── mmupdate.py         # Database updater
├── config.py           # Configuration
├── file_parser.py      # Multi-format file handler
├── launcher.py         # User-friendly launcher
├── install_who_dat.py # Cross-platform installer
├── requirements.txt    # Dependencies
├── templates/          # HTML templates
├── static/            # Static assets (owl logo)
└── icons/             # Application icons
```

## 📋 Requirements

- **Python 3.6+**
- **MaxMind License Key** (free from [maxmind.com](https://www.maxmind.com))
- **Internet Connection** (for database updates)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Support

- ☕ **Buy Me a Coffee:** [Ko-Fi](https://ko-fi.com/applesauce777)

## 🙏 Acknowledgments

- **MaxMind** - GeoLite2 databases for accurate geolocation
- **Flask** - Web framework

---

<div align="center">

**🦉 WhoDat? Find out who that IP belongs to! 🦉**

</div>
