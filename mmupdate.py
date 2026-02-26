import requests
import hashlib
import tarfile
import os
import sys
from pathlib import Path

# MaxMind license key
try:
    from config import license_key
    if license_key == "your_license_key_here":
        print("Error: Please update config.py with your actual MaxMind license key")
        sys.exit(1)
except ImportError:
    print("Error: config.py file not found. Please create it with your license key.")
    sys.exit(1)

def download_and_verify(db_name, db_url, sha256_url):
    """Download and verify a MaxMind database"""
    try:
        print(f"Downloading {db_name} database...")
        
        # Use session for connection reuse and better error handling
        session = requests.Session()
        session.headers.update({'User-Agent': 'Who-Dat/1.0'})
        
        # Download database file
        db_response = session.get(db_url, timeout=300)
        db_response.raise_for_status()
        
        tar_filename = f"{db_name}.tar.gz"
        with open(tar_filename, "wb") as db_file:
            db_file.write(db_response.content)
        
        print(f"Downloading {db_name} checksum...")
        sha256_response = session.get(sha256_url, timeout=300)
        sha256_response.raise_for_status()
        
        sha256_filename = f"{db_name}.tar.gz.sha256"
        with open(sha256_filename, "wb") as sha256_file:
            sha256_file.write(sha256_response.content)
        
        # Verify SHA256 checksum
        with open(tar_filename, "rb") as db_file:
            db_content = db_file.read()
            actual_sha256 = hashlib.sha256(db_content).hexdigest()
        
        with open(sha256_filename, "r") as sha256_file:
            sha256_content = sha256_file.read().strip()
            # Extract just the hash (first part before any whitespace)
            expected_sha256 = sha256_content.split()[0] if sha256_content else ""
        
        if actual_sha256 != expected_sha256:
            print(f"SHA256 checksum verification failed for {db_name} database")
            print(f"Expected: {expected_sha256}")
            print(f"Actual:   {actual_sha256}")
            return False
        
        # Extract the .mmdb file
        print(f"Extracting {db_name} database...")
        with tarfile.open(tar_filename, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.name.endswith('.mmdb'):
                    member.name = Path(member.name).name  # Extract to current directory
                    tar.extract(member, filter='data')
                    break
        
        # Cleanup temporary files
        os.remove(tar_filename)
        os.remove(sha256_filename)
        print(f"Successfully updated {db_name} database")
        return True
        
    except requests.RequestException as e:
        print(f"Network error downloading {db_name}: {e}")
        # Cleanup partial files on error
        for filename in [f"{db_name}.tar.gz", f"{db_name}.tar.gz.sha256"]:
            try:
                os.remove(filename)
            except:
                pass
        return False
    except Exception as e:
        print(f"Error processing {db_name}: {e}")
        # Cleanup partial files on error
        for filename in [f"{db_name}.tar.gz", f"{db_name}.tar.gz.sha256"]:
            try:
                os.remove(filename)
            except:
                pass
        return False

# Download and verify GeoLite2-City database
city_db_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={license_key}&suffix=tar.gz"
city_sha256_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={license_key}&suffix=tar.gz.sha256"

download_and_verify("GeoLite2-City", city_db_url, city_sha256_url)

# Download and verify GeoLite2-ASN database
asn_db_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key={license_key}&suffix=tar.gz"
asn_sha256_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key={license_key}&suffix=tar.gz.sha256"

download_and_verify("GeoLite2-ASN", asn_db_url, asn_sha256_url)

print("Database update completed.")
