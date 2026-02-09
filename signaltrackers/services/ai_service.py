"""
AI Service Layer

Handles AI client management for both system-level (scheduled tasks)
and user-level (chatbot, portfolio analysis) API key usage.

System API Key: Used for scheduled briefings, paid by system owner.
User API Key: Used for on-demand features (chat, portfolio analysis), paid by user.
"""

import os
from typing import Tuple, Optional, Any

from flask import current_app
from flask_login import current_user


class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


# AI Provider constants
OPENAI_MODEL = "gpt-5.2"
ANTHROPIC_MODEL = "claude-opus-4-6"


def get_user_ai_client() -> Tuple[Any, str]:
    """
    Get AI client using current user's API key.

    For chatbot and portfolio analysis - user provides and pays.

    Returns:
        tuple: (client, provider_name)

    Raises:
        AIServiceError: If user not authenticated or key not configured
    """
    if not current_user.is_authenticated:
        raise AIServiceError("Authentication required to use AI features.")

    settings = current_user.settings
    if not settings:
        raise AIServiceError(
            "User settings not configured. Please visit Settings to configure your API keys."
        )

    provider = settings.ai_provider or 'openai'

    if provider == 'anthropic':
        try:
            key = settings.get_anthropic_key()
        except Exception as e:
            raise AIServiceError(f"Error accessing API key: {e}")

        if not key:
            raise AIServiceError(
                "Anthropic API key not configured. "
                "Please add your API key in Settings to use the chatbot and portfolio analysis."
            )

        try:
            import anthropic
            return anthropic.Anthropic(api_key=key), 'anthropic'
        except ImportError:
            raise AIServiceError("Anthropic package not installed on server.")

    else:  # OpenAI (default)
        try:
            key = settings.get_openai_key()
        except Exception as e:
            raise AIServiceError(f"Error accessing API key: {e}")

        if not key:
            raise AIServiceError(
                "OpenAI API key not configured. "
                "Please add your API key in Settings to use the chatbot and portfolio analysis."
            )

        try:
            from openai import OpenAI
            return OpenAI(api_key=key), 'openai'
        except ImportError:
            raise AIServiceError("OpenAI package not installed on server.")


def get_system_ai_client() -> Tuple[Optional[Any], Optional[str]]:
    """
    Get AI client using system API key from environment/config.

    For scheduled briefings - system owner pays.

    Returns:
        tuple: (client, provider_name) or (None, error_message)
    """
    provider = current_app.config.get('SYSTEM_AI_PROVIDER', 'openai').lower()

    if provider == 'anthropic':
        key = current_app.config.get('SYSTEM_ANTHROPIC_KEY')
        if not key:
            return None, "System Anthropic key not configured"

        try:
            import anthropic
            return anthropic.Anthropic(api_key=key), 'anthropic'
        except ImportError:
            return None, "Anthropic package not installed"

    else:  # OpenAI (default)
        key = current_app.config.get('SYSTEM_OPENAI_KEY')
        if not key:
            return None, "System OpenAI key not configured"

        try:
            from openai import OpenAI
            return OpenAI(api_key=key), 'openai'
        except ImportError:
            return None, "OpenAI package not installed"


def get_user_ai_model() -> str:
    """
    Get the appropriate model name for the user's configured provider.

    Returns:
        str: Model name (e.g., 'gpt-5.2' or 'claude-opus-4-6')
    """
    if not current_user.is_authenticated:
        return OPENAI_MODEL

    settings = current_user.settings
    if settings and settings.ai_provider == 'anthropic':
        return ANTHROPIC_MODEL

    return OPENAI_MODEL


def get_system_ai_model() -> str:
    """
    Get the appropriate model name for the system's configured provider.

    Returns:
        str: Model name
    """
    provider = current_app.config.get('SYSTEM_AI_PROVIDER', 'openai').lower()
    if provider == 'anthropic':
        return ANTHROPIC_MODEL
    return OPENAI_MODEL


def check_user_ai_configured() -> dict:
    """
    Check if current user has AI properly configured.

    Returns:
        dict: {
            'configured': bool,
            'provider': str or None,
            'message': str
        }
    """
    if not current_user.is_authenticated:
        return {
            'configured': False,
            'provider': None,
            'message': 'Please log in to use AI features.'
        }

    settings = current_user.settings
    if not settings:
        return {
            'configured': False,
            'provider': None,
            'message': 'Please configure your settings.'
        }

    provider = settings.ai_provider or 'openai'

    if provider == 'anthropic':
        if settings.has_anthropic_key:
            return {
                'configured': True,
                'provider': 'anthropic',
                'message': 'Anthropic API key configured.'
            }
        return {
            'configured': False,
            'provider': 'anthropic',
            'message': 'Please add your Anthropic API key in Settings.'
        }

    # OpenAI
    if settings.has_openai_key:
        return {
            'configured': True,
            'provider': 'openai',
            'message': 'OpenAI API key configured.'
        }
    return {
        'configured': False,
        'provider': 'openai',
        'message': 'Please add your OpenAI API key in Settings.'
    }
