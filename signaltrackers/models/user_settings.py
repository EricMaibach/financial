"""
User Settings Model

Stores user preferences and encrypted API keys for AI services.
"""

import os
from datetime import datetime

from flask import current_app

from extensions import db

# Optional import - only needed when encrypting/decrypting
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None


class UserSettings(db.Model):
    """User settings including encrypted API keys."""

    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )

    # AI Provider preference
    ai_provider = db.Column(db.String(20), default='openai')  # 'openai' or 'anthropic'

    # Encrypted API keys
    openai_api_key_encrypted = db.Column(db.LargeBinary, nullable=True)
    anthropic_api_key_encrypted = db.Column(db.LargeBinary, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def _get_cipher():
        """Get Fernet cipher for encryption/decryption."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography package not installed")

        key = current_app.config.get('ENCRYPTION_KEY') or os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY not configured. Generate one with: "
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        # Key should be bytes
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)

    def set_openai_key(self, key):
        """Encrypt and store OpenAI API key."""
        if key:
            cipher = self._get_cipher()
            self.openai_api_key_encrypted = cipher.encrypt(key.encode())
        else:
            self.openai_api_key_encrypted = None

    def get_openai_key(self):
        """Decrypt and return OpenAI API key."""
        if self.openai_api_key_encrypted:
            cipher = self._get_cipher()
            return cipher.decrypt(self.openai_api_key_encrypted).decode()
        return None

    def set_anthropic_key(self, key):
        """Encrypt and store Anthropic API key."""
        if key:
            cipher = self._get_cipher()
            self.anthropic_api_key_encrypted = cipher.encrypt(key.encode())
        else:
            self.anthropic_api_key_encrypted = None

    def get_anthropic_key(self):
        """Decrypt and return Anthropic API key."""
        if self.anthropic_api_key_encrypted:
            cipher = self._get_cipher()
            return cipher.decrypt(self.anthropic_api_key_encrypted).decode()
        return None

    @property
    def has_openai_key(self):
        """Check if OpenAI key is configured."""
        return self.openai_api_key_encrypted is not None

    @property
    def has_anthropic_key(self):
        """Check if Anthropic key is configured."""
        return self.anthropic_api_key_encrypted is not None

    @property
    def has_active_key(self):
        """Check if the selected provider has a configured key."""
        if self.ai_provider == 'anthropic':
            return self.has_anthropic_key
        return self.has_openai_key

    def __repr__(self):
        return f'<UserSettings user_id={self.user_id} provider={self.ai_provider}>'
