"""
Billing Module — Stripe Integration

Provides Stripe client initialization and billing utilities.
All secrets are read from environment variables; the module degrades
gracefully when Stripe credentials are not configured.
"""

import os
import logging

import stripe

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stripe client configuration
# ---------------------------------------------------------------------------

_stripe_configured = False


def init_stripe(app=None):
    """Initialise the Stripe SDK from environment variables.

    Call once at application startup.  If ``STRIPE_SECRET_KEY`` is not set
    (or is empty), the module stays in an unconfigured state and all
    billing operations will be unavailable — but the rest of the
    application continues to work normally.
    """
    global _stripe_configured

    secret_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()

    if not secret_key:
        logger.info("Stripe not configured — STRIPE_SECRET_KEY is not set. "
                     "Billing features will be unavailable.")
        _stripe_configured = False
        return False

    stripe.api_key = secret_key
    _stripe_configured = True
    logger.info("Stripe SDK initialised successfully.")
    return True


def is_stripe_configured() -> bool:
    """Return *True* if Stripe has been initialised with a secret key."""
    return _stripe_configured


def get_publishable_key() -> str | None:
    """Return the Stripe publishable key for client-side use, or *None*."""
    key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "").strip()
    return key or None


def get_webhook_secret() -> str | None:
    """Return the webhook signing secret, or *None*."""
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()
    return secret or None


def get_price_id() -> str | None:
    """Return the configured Stripe Price ID, or *None*."""
    price_id = os.environ.get("STRIPE_PRICE_ID", "").strip()
    return price_id or None
