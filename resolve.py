import sqlite3
import geoip2.database
import geoip2.errors
import os
import argparse
import re
import sys
from tqdm import tqdm
from file_parser import extract_ips_from_file

def validate_ip(ip):
    """Validate IP address format"""
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, ip) is not None

def count_lines(filename):
    """Count lines in file for progress bar"""
    with open(filename, 'r') as f:
        return sum(1 for _ in f)

def main():
    parser = argparse.ArgumentParser(description='Resolve IP addresses to geolocation data')
    parser.add_argument('ip_file', help='Path to input IP file (supports .txt, .csv, .tsv, .xlsx, .xls)')
    parser.add_argument('db_file', help='Output SQLite database file')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for database inserts')
    
    args = parser.parse_args()
    
    IP_FILE = args.ip_file
    DB_FILE = args.db_file
    batch_size = args.batch_size

    # Extract IPs from file (supports multiple formats)
    print(f"Extracting IPs from {IP_FILE}...")
    ips, file_type, confidence = extract_ips_from_file(IP_FILE)
    
    if not ips:
        print(f"Error: No valid IP addresses found in {file_type} file")
        sys.exit(1)
    
    conf_str = f'{confidence:.1f}%' if confidence is not None else 'N/A'
    print(f"Found {len(ips)} IPs in {file_type} (confidence: {conf_str})")

    # Open MaxMind databases
    geoip_asn = geoip2.database.Reader("GeoLite2-ASN.mmdb")
    geoip_city = geoip2.database.Reader("GeoLite2-City.mmdb")

    # Connect to SQLite and optimize for bulk inserts
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ensure table structure includes 'region' (state/province)
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

    # Check if 'region' column exists; add it if missing
    cursor.execute("PRAGMA table_info(ip_info);")
    columns = [row[1] for row in cursor.fetchall()]
    if "region" not in columns:
        cursor.execute("ALTER TABLE ip_info ADD COLUMN region TEXT;")
        conn.commit()

    # Optimize database for faster inserts
    cursor.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for speed
    cursor.execute("PRAGMA synchronous = OFF;")

    # Process IPs in batches
    batch = []

    if not os.path.exists(IP_FILE):
        print(f"Error: File {IP_FILE} not found.")
        sys.exit(1)

    print(f"Processing {len(ips)} IP addresses...")

    # Process IPs from extracted list
    for ip in tqdm(ips, desc="Resolving IPs", unit="ip"):
        try:
            city_resp = geoip_city.city(ip)
            city = city_resp.city.name or "N/A"
            country = city_resp.country.name or "N/A"
            region = city_resp.subdivisions.most_specific.name or "N/A"  # Extract state/province
            latitude = city_resp.location.latitude or 0.0
            longitude = city_resp.location.longitude or 0.0
        except geoip2.errors.AddressNotFoundError:
            city, country, region, latitude, longitude = "N/A", "N/A", "N/A", 0.0, 0.0

        try:
            asn_resp = geoip_asn.asn(ip)
            isp = asn_resp.autonomous_system_organization or "N/A"
        except geoip2.errors.AddressNotFoundError:
            isp = "N/A"

        # Add to batch
        batch.append((ip, isp, city, region, country, latitude, longitude))

        # Insert in batches for efficiency
        if len(batch) >= batch_size:
            cursor.executemany("INSERT OR IGNORE INTO ip_info VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
            conn.commit()
            batch = []

    # Final batch insert
    if batch:
        cursor.executemany("INSERT OR IGNORE INTO ip_info VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
        conn.commit()

    # Close resources
    geoip_asn.close()
    geoip_city.close()
    conn.close()

    print(f"\nFinished processing {len(ips)} IP addresses from {file_type}.")
    print(f"Results saved to {DB_FILE}")


if __name__ == "__main__":
    main()

