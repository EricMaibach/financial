"""
Flask Application Configuration

Environment-based configuration for the SignalTrackers dashboard.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR / "data" / "signaltrackers.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # System AI Keys (for scheduled briefings)
    SYSTEM_AI_PROVIDER = os.environ.get('AI_PROVIDER', 'openai').lower()
    SYSTEM_OPENAI_KEY = os.environ.get('OPENAI_API_KEY')
    SYSTEM_ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_EFFORT = os.environ.get('ANTHROPIC_EFFORT', 'medium').lower()

    # Encryption key for user API keys
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

    # Session
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate limiting
    RATELIMIT_STORAGE_URI = 'memory://'
    RATELIMIT_DEFAULT = '100 per minute'

    # Optional services
    FRED_API_KEY = os.environ.get('FRED_API_KEY')
    TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    # Require SECRET_KEY in production
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError('SECRET_KEY environment variable required in production')
        return key


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
