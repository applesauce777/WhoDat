import pandas as pd
import re
from pathlib import Path

def detect_ip_column(df):
    """Automatically detect the column containing IP addresses"""
    ip_pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    
    # Score each column based on how many valid IPs it contains
    column_scores = {}
    
    for column in df.columns:
        score = 0
        total_non_empty = 0
        
        for value in df[column].dropna():
            if pd.notna(value):
                total_non_empty += 1
                # Convert to string and check if it's an IP
                str_value = str(value).strip()
                if ip_pattern.match(str_value):
                    score += 1
        
        # Calculate percentage of valid IPs
        if total_non_empty > 0:
            percentage = (score / total_non_empty) * 100
            column_scores[column] = percentage
    
    # Return the column with the highest percentage of valid IPs
    if column_scores:
        best_column = max(column_scores, key=column_scores.get)
        if column_scores[best_column] > 50:  # At least 50% should be valid IPs
            return best_column, column_scores[best_column]
    
    return None, 0

def extract_ips_from_file(file_path):
    """Extract IP addresses from various file formats"""
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.txt':
            # Handle plain text file (one IP per line)
            with open(file_path, 'r') as f:
                ips = [line.strip() for line in f if line.strip()]
            return ips, 'text', None
            
        elif file_extension in ['.csv', '.tsv']:
            # Handle CSV/TSV files
            delimiter = '\t' if file_extension == '.tsv' else ','
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            ip_column, confidence = detect_ip_column(df)
            if ip_column:
                ips = [str(ip).strip() for ip in df[ip_column].dropna() if str(ip).strip()]
                return ips, f'csv/tsv (column: {ip_column})', confidence
            else:
                return [], 'csv/tsv', 0
                
        elif file_extension in ['.xlsx', '.xls']:
            # Handle Excel files
            df = pd.read_excel(file_path)
            
            ip_column, confidence = detect_ip_column(df)
            if ip_column:
                ips = [str(ip).strip() for ip in df[ip_column].dropna() if str(ip).strip()]
                return ips, f'excel (column: {ip_column})', confidence
            else:
                return [], 'excel', 0
                
        else:
            return [], f'unsupported format: {file_extension}', 0
            
    except Exception as e:
        return [], f'error: {str(e)}', 0

def preview_file(file_path, max_rows=10):
    """Preview file contents to help users understand the structure"""
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.txt':
            with open(file_path, 'r') as f:
                lines = f.readlines()[:max_rows]
            return {
                'type': 'text',
                'preview': lines,
                'total_lines': len(open(file_path, 'r').readlines())
            }
            
        elif file_extension in ['.csv', '.tsv']:
            delimiter = '\t' if file_extension == '.tsv' else ','
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            ip_column, confidence = detect_ip_column(df)
            
            return {
                'type': 'csv/tsv',
                'preview': df.head(max_rows).to_dict('records'),
                'columns': list(df.columns),
                'total_rows': len(df),
                'ip_column': ip_column,
                'confidence': confidence
            }
            
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            
            ip_column, confidence = detect_ip_column(df)
            
            return {
                'type': 'excel',
                'preview': df.head(max_rows).to_dict('records'),
                'columns': list(df.columns),
                'total_rows': len(df),
                'ip_column': ip_column,
                'confidence': confidence
            }
            
        else:
            return {'type': 'unsupported', 'error': f'Unsupported file format: {file_extension}'}
            
    except Exception as e:
        return {'type': 'error', 'error': str(e)}
