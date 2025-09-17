"""
Configuration Management - Handles both local and production environments
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration that works for both local and production"""
    
    # Determine environment
    ENV = os.getenv('ENV', 'development')
    IS_PRODUCTION = ENV == 'production'
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / 'data'
    STATIC_DIR = BASE_DIR / 'static'
    
    # Database - SQLite for local, can switch to PostgreSQL for production
    if IS_PRODUCTION and os.getenv('DATABASE_URL'):
        DATABASE_URL = os.getenv('DATABASE_URL')
        DATABASE_TYPE = 'postgresql'
    else:
        DATABASE_PATH = BASE_DIR / 'nonprofits.db'
        DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
        DATABASE_TYPE = 'sqlite'
    
    # Application settings
    APP_NAME = os.getenv('APP_NAME', 'Nonprofit Intelligence Platform')
    APP_URL = os.getenv('APP_URL', 'http://localhost:8000')
    
    # API settings
    API_PREFIX = '/api'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
    
    # IRS Data URLs
    IRS_BASE_URL = 'https://www.irs.gov/pub/irs-soi'
    IRS_REGIONS = ['eo1', 'eo2', 'eo3', 'eo4', 'eo_other']
    
    # Performance settings
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    
    # Search settings
    SEARCH_MIN_LENGTH = 2
    SEARCH_MAX_RESULTS = 500
    DEFAULT_PAGE_SIZE = 50
    
    # Cache settings (for future Redis implementation)
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    
    # Security (for production)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    @classmethod
    def get_database_url(cls):
        """Get database URL based on environment"""
        return cls.DATABASE_URL
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all necessary directories exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.STATIC_DIR.mkdir(exist_ok=True)
        
        # Create subdirectories
        (cls.DATA_DIR / 'raw').mkdir(exist_ok=True)
        (cls.DATA_DIR / 'processed').mkdir(exist_ok=True)
        (cls.DATA_DIR / 'temp').mkdir(exist_ok=True)

config = Config()
