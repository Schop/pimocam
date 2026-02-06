import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'settings.db')

# Settings metadata with defaults, descriptions, and validation
SETTINGS_METADATA = {
    'CONTOUR_THRESHOLD': {
        'value': 300,
        'type': 'int',
        'min': 100,
        'max': 5000,
        'description': 'Minimum contour area for motion detection. Lower values = more sensitive to small birds.',
        'category': 'Motion Detection'
    },
    'BLUR_KERNEL': {
        'value': 15,
        'type': 'int',
        'min': 5,
        'max': 51,
        'description': 'Gaussian blur kernel size (must be odd). Smaller = more detail, larger = smoother.',
        'category': 'Motion Detection'
    },
    'THRESH_VALUE': {
        'value': 35,
        'type': 'int',
        'min': 10,
        'max': 100,
        'description': 'Threshold for detecting changes. Lower = more sensitive to subtle movements.',
        'category': 'Motion Detection'
    },
    'DILATE_ITERATIONS': {
        'value': 2,
        'type': 'int',
        'min': 0,
        'max': 10,
        'description': 'Number of dilation iterations to fill gaps in detected motion areas.',
        'category': 'Motion Detection'
    },
    'MOTION_COOLDOWN_SECONDS': {
        'value': 5,
        'type': 'int',
        'min': 1,
        'max': 60,
        'description': 'Minimum seconds between motion captures to avoid duplicate photos.',
        'category': 'Motion Detection'
    },
    'TIMELAPSE_BRIGHTNESS_THRESHOLD': {
        'value': 40,
        'type': 'int',
        'min': 0,
        'max': 255,
        'description': 'Minimum brightness (0-255) required for timelapse capture. Skips dark images.',
        'category': 'Timelapse'
    },
    'SCHEDULER_INTERVAL_MINUTES': {
        'value': 30,
        'type': 'int',
        'min': 1,
        'max': 1440,
        'description': 'Minutes between scheduled timelapse captures.',
        'category': 'Timelapse'
    },
    'MIN_FREE_GB': {
        'value': 10.0,
        'type': 'float',
        'min': 0.5,
        'max': 100.0,
        'description': 'Minimum free disk space in GB. Old files are deleted when space is low.',
        'category': 'Storage'
    },
    'WEBSERVER_PORT': {
        'value': 5000,
        'type': 'int',
        'min': 1024,
        'max': 65535,
        'description': 'Port number for the web interface.',
        'category': 'Web Server'
    },
    'WEBSERVER_DEBUG': {
        'value': False,
        'type': 'bool',
        'description': 'Enable debug mode for the web server (NOT recommended - causes camera conflicts).',
        'category': 'Web Server'
    }
}

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database with settings table and default values"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                data_type TEXT NOT NULL,
                min_value REAL,
                max_value REAL,
                description TEXT,
                category TEXT
            )
        ''')
        
        # Check if table is empty
        cursor.execute('SELECT COUNT(*) FROM settings')
        count = cursor.fetchone()[0]
        
        # Populate with defaults if empty
        if count == 0:
            for key, meta in SETTINGS_METADATA.items():
                cursor.execute('''
                    INSERT INTO settings (key, value, data_type, min_value, max_value, description, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    str(meta['value']),
                    meta['type'],
                    meta.get('min'),
                    meta.get('max'),
                    meta.get('description', ''),
                    meta.get('category', 'General')
                ))
            conn.commit()
            print("Database initialized with default settings")

def get_setting(key, default=None):
    """Get a setting value by key, with type conversion"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value, data_type FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row is None:
            return default
        
        value_str, data_type = row
        
        # Convert to appropriate type
        if data_type == 'int':
            return int(value_str)
        elif data_type == 'float':
            return float(value_str)
        elif data_type == 'bool':
            return value_str.lower() in ('true', '1', 'yes')
        else:
            return value_str

def set_setting(key, value):
    """Set a setting value with validation"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get metadata for validation
        cursor.execute('SELECT data_type, min_value, max_value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row is None:
            raise ValueError(f"Unknown setting: {key}")
        
        data_type, min_val, max_val = row
        
        # Validate and convert type
        if data_type == 'int':
            value = int(value)
            if min_val is not None and value < min_val:
                raise ValueError(f"{key} must be at least {min_val}")
            if max_val is not None and value > max_val:
                raise ValueError(f"{key} must be at most {max_val}")
        elif data_type == 'float':
            value = float(value)
            if min_val is not None and value < min_val:
                raise ValueError(f"{key} must be at least {min_val}")
            if max_val is not None and value > max_val:
                raise ValueError(f"{key} must be at most {max_val}")
        elif data_type == 'bool':
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes')
            else:
                value = bool(value)
        
        # Special validation for BLUR_KERNEL (must be odd)
        if key == 'BLUR_KERNEL' and value % 2 == 0:
            raise ValueError("BLUR_KERNEL must be an odd number")
        
        # Update database
        cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (str(value), key))
        conn.commit()

def get_all_settings():
    """Get all settings with metadata"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings ORDER BY category, key')
        rows = cursor.fetchall()
        
        settings = {}
        for row in rows:
            settings[row['key']] = {
                'value': row['value'],
                'data_type': row['data_type'],
                'min_value': row['min_value'],
                'max_value': row['max_value'],
                'description': row['description'],
                'category': row['category']
            }
        return settings

def get_settings_by_category():
    """Get settings organized by category"""
    all_settings = get_all_settings()
    by_category = {}
    
    for key, data in all_settings.items():
        category = data['category']
        if category not in by_category:
            by_category[category] = {}
        by_category[category][key] = data
    
    return by_category

def reset_to_defaults():
    """Reset all settings to default values"""
    with get_db() as conn:
        cursor = conn.cursor()
        for key, meta in SETTINGS_METADATA.items():
            cursor.execute('UPDATE settings SET value = ? WHERE key = ?', (str(meta['value']), key))
        conn.commit()

# Initialize database on module import
init_db()
