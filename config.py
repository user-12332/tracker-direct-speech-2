"""
Configuration for officials tracker
"""
import os
from pathlib import Path

# Base paths
# For local development
BASE_PATH = Path(__file__).parent.resolve()

# For Google Drive (uncomment and modify when deploying)
# BASE_PATH = Path.home() / 'Google Drive' / 'officials_tracker'
# Or on Windows: Path('G:/My Drive/officials_tracker')

# Storage type
STORAGE_TYPE = 'local'  # Options: 'local', 'google_drive'

# User info (for tracking who made changes)
CURRENT_USER = os.environ.get('USER', 'default_user')

# UI Settings
PAGE_TITLE = 'Officials Tracker'
PAGE_ICON = '📄'  # Simple document icon for browser tab

# Date format
DATE_FORMAT = '%Y-%m-%d'
