import os

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Database Configuration
DATA_DIR = 'data'
REPORTS_FILE = os.path.join(DATA_DIR, 'reports.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# Report Configuration
ALLOWED_REPORT_FORMATS = ['.pdf', '.doc', '.docx', '.txt']
MAX_REPORT_SIZE = 20 * 1024 * 1024  # 20MB

# Admin Configuration
ADMIN_IDS = [123456789]  # Replace with actual admin Telegram IDs
