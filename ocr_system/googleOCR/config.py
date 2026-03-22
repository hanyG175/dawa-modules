"""
Configuration settings for Google OCR Tool
"""

import os
from pathlib import Path

# Get the googleOCR directory path
GOOGLEOCR_DIR = Path(__file__).parent

# Google API Configuration
SCOPES = 'https://www.googleapis.com/auth/drive'
APPLICATION_NAME = 'Google OCR Tool'
CREDENTIAL_FILE = os.path.join(GOOGLEOCR_DIR, 'drive-python-quickstart.json')

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'
}

# File encoding
DEFAULT_ENCODING = 'utf-8'

# Output settings
OUTPUT_EXTENSION = '.txt'

# Logging
LOG_DIR = os.path.join(GOOGLEOCR_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Temporary files
TEMP_DIR = os.path.join(GOOGLEOCR_DIR, 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
