from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import sqlite3
import geoip2.database
import geoip2.errors
import os
import re
import threading
import time
from werkzeug.utils import secure_filename
import tempfile
from pathlib import Path
import requests
import hashlib
import tarfile
import sys
from file_parser import extract_ips_from_file, preview_file

app = Flask(__name__)
app.secret_key = 'who_dat_secret_key'

# Global variables for progress tracking
progress = {'current': 0, 'total': 0, 'status': 'idle', 'message': ''}
processing_thread = None

def validate_ip(ip):
    """Validate IP address format"""
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, ip) is not None

def count_lines(filename):
    """Count lines in file"""
    with open(filename, 'r') as f:
        return sum(1 for _ in f)

def update_progress(current, total, status, message=""):
    global progress
    progress['current'] = current
    progress['total'] = total
    progress['status'] = status
    progress['message'] = message

def process_ips_async(ip_file, db_file, batch_size=1000):
    """Process IPs asynchronously"""
    try:
        update_progress(0, 0, 'loading', 'Extracting IPs from file...')
        
        # Extract IPs from file (supports multiple formats)
        ips, file_type, confidence = extract_ips_from_file(ip_file)
        
        if not ips:
            update_progress(0, 0, 'error', f'No valid IPs found in {file_type} file')
            return
            
        total_ips = len(ips)
        update_progress(0, total_ips, 'loading', f'Found {total_ips} IPs in {file_type} (confidence: {confidence:.1f}%)')
        
        # Open MaxMind databases
        geoip_asn = geoip2.database.Reader("GeoLite2-ASN.mmdb")
        geoip_city = geoip2.database.Reader("GeoLite2-City.mmdb")
        
        # Connect to SQLite
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Ensure table structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ip_info (
                ip TEXT PRIMARY KEY,
                isp TEXT,
                city TEXT,
                region TEXT,
                country TEXT,
                latitude REAL,
                longitude REAL
            )
        """)
        
        # Check if 'region' column exists
        cursor.execute("PRAGMA table_info(ip_info);")
        columns = [row[1] for row in cursor.fetchall()]
        if "region" not in columns:
            cursor.execute("ALTER TABLE ip_info ADD COLUMN region TEXT;")
            conn.commit()
        
        # Optimize database
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = OFF;")
        
        # Count total IPs
        update_progress(0, total_ips, 'processing', f'Processing {total_ips} IP addresses from {file_type}...')
        
        # Process IPs from extracted list
        batch = []
        processed = 0
        
        for ip in ips:
            try:
                city_resp = geoip_city.city(ip)
                city = city_resp.city.name or "N/A"
                country = city_resp.country.name or "N/A"
                region = city_resp.subdivisions.most_specific.name or "N/A"
                latitude = city_resp.location.latitude or 0.0
                longitude = city_resp.location.longitude or 0.0
            except geoip2.errors.AddressNotFoundError:
                city, country, region, latitude, longitude = "N/A", "N/A", "N/A", 0.0, 0.0
            
            try:
                asn_resp = geoip_asn.asn(ip)
                isp = asn_resp.autonomous_system_organization or "N/A"
            except geoip2.errors.AddressNotFoundError:
                isp = "N/A"
            
            batch.append((ip, isp, city, region, country, latitude, longitude))
            
            # Insert in batches
            if len(batch) >= batch_size:
                cursor.executemany("INSERT OR IGNORE INTO ip_info VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                conn.commit()
                batch = []
            
            processed += 1
            if processed % 10 == 0:  # Update progress every 10 IPs
                update_progress(processed, total_ips, 'processing', f'Processed {processed}/{total_ips} IPs...')
        
        # Final batch insert
        if batch:
            cursor.executemany("INSERT OR IGNORE INTO ip_info VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
            conn.commit()
        
        # Close resources
        geoip_asn.close()
        geoip_city.close()
        conn.close()
        
        update_progress(total_ips, total_ips, 'completed', f'Completed! Processed {total_ips} IP addresses.')
        
        # Auto-reset progress after 5 seconds to prevent continuous polling
        threading.Timer(5.0, lambda: update_progress(0, 0, 'idle', '')).start()
        
    except Exception as e:
        update_progress(0, 0, 'error', f'Error: {str(e)}')

def update_databases_async():
    """Update MaxMind databases asynchronously"""
    try:
        from config import license_key
        if license_key == "your_license_key_here":
            update_progress(0, 0, 'error', 'Please update config.py with your license key')
            return
        
        def download_and_verify(db_name, db_url, sha256_url):
            try:
                update_progress(0, 0, 'downloading', f'Downloading {db_name} database...')
                
                # Use session for connection reuse and better error handling
                session = requests.Session()
                session.headers.update({'User-Agent': 'Who-Dat/1.0'})
                
                db_response = session.get(db_url, timeout=300)
                db_response.raise_for_status()
                
                tar_filename = f"{db_name}.tar.gz"
                with open(tar_filename, "wb") as db_file:
                    db_file.write(db_response.content)
                
                update_progress(0, 0, 'downloading', f'Downloading {db_name} checksum...')
                sha256_response = session.get(sha256_url, timeout=300)
                sha256_response.raise_for_status()
                
                sha256_filename = f"{db_name}.tar.gz.sha256"
                with open(sha256_filename, "wb") as sha256_file:
                    sha256_file.write(sha256_response.content)
                    
                # Verify SHA256
                with open(tar_filename, "rb") as db_file:
                    db_content = db_file.read()
                    actual_sha256 = hashlib.sha256(db_content).hexdigest()
                
                with open(sha256_filename, "r") as sha256_file:
                    sha256_content = sha256_file.read().strip()
                    # Extract just the hash (first part before any whitespace)
                    expected_sha256 = sha256_content.split()[0] if sha256_content else ""
                
                if actual_sha256 != expected_sha256:
                    print(f"SHA256 checksum verification failed for {db_name}")
                    print(f"Expected: {expected_sha256}")
                    print(f"Actual:   {actual_sha256}")
                    raise Exception(f"SHA256 checksum verification failed for {db_name}")
                
                # Extract
                update_progress(0, 0, 'extracting', f'Extracting {db_name} database...')
                with tarfile.open(tar_filename, 'r:gz') as tar:
                    for member in tar.getmembers():
                        if member.name.endswith('.mmdb'):
                            member.name = Path(member.name).name
                            tar.extract(member, filter='data')
                            break
                
                # Cleanup
                os.remove(tar_filename)
                os.remove(sha256_filename)
                return True
                
            except Exception as e:
                # Cleanup partial files on error
                for filename in [f"{db_name}.tar.gz", f"{db_name}.tar.gz.sha256"]:
                    try:
                        os.remove(filename)
                    except:
                        pass
                raise Exception(f"Error processing {db_name}: {str(e)}")
        
        # Update City database
        city_db_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={license_key}&suffix=tar.gz"
        city_sha256_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={license_key}&suffix=tar.gz.sha256"
        
        if not download_and_verify("GeoLite2-City", city_db_url, city_sha256_url):
            return
        
        # Update ASN database
        asn_db_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key={license_key}&suffix=tar.gz"
        asn_sha256_url = f"https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key={license_key}&suffix=tar.gz.sha256"
        
        if not download_and_verify("GeoLite2-ASN", asn_db_url, asn_sha256_url):
            return
        
        update_progress(100, 100, 'completed', 'Database update completed successfully!')
        
        # Auto-reset progress after 5 seconds to prevent continuous polling
        threading.Timer(5.0, lambda: update_progress(0, 0, 'idle', '')).start()
        
    except Exception as e:
        update_progress(0, 0, 'error', f'Update error: {str(e)}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview_file_route():
    """Preview uploaded file structure"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    # Save file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(tempfile.gettempdir(), filename)
    file.save(filepath)
    
    # Get preview
    preview = preview_file(filepath)
    
    # Clean up
    try:
        os.remove(filepath)
    except:
        pass
    
    return jsonify(preview)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(tempfile.gettempdir(), filename)
        file.save(filepath)
        
        # Extract IPs from file first to validate
        ips, file_type, confidence = extract_ips_from_file(filepath)
        
        if not ips:
            flash(f'No valid IP addresses found in {file_type} file')
            return redirect(url_for('index'))
        
        # Start processing in background
        global processing_thread
        processing_thread = threading.Thread(target=process_ips_async, args=(filepath, 'output.db'))
        processing_thread.start()
        
        flash(f'File uploaded successfully! Found {len(ips)} IPs in {file_type} file.')
        return redirect(url_for('index'))

@app.route('/update_databases', methods=['POST'])
def update_databases():
    global processing_thread
    processing_thread = threading.Thread(target=update_databases_async)
    processing_thread.start()
    
    flash('Database update started...')
    return redirect(url_for('index'))

@app.route('/progress')
def get_progress():
    return jsonify(progress)

@app.route('/results')
def show_results():
    try:
        conn = sqlite3.connect('output.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ip_info")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT ip, isp, city, region, country FROM ip_info ORDER BY ip LIMIT 100")
        results = cursor.fetchall()
        
        conn.close()
        
        return render_template('results.html', total_count=total_count, results=results)
    except Exception as e:
        flash(f'Error reading results: {str(e)}')
        return redirect(url_for('index'))

@app.route('/download')
def download_results():
    try:
        return send_file('output.db', as_attachment=True, download_name='ip_geolocation.db')
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
