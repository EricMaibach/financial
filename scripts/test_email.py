#!/usr/bin/env python3
"""
Test Email Script

Sends a test email to verify email configuration is working correctly.
Requires email configuration to be set in environment variables.

Usage:
    python scripts/test_email.py your-email@example.com
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'signaltrackers'))

from flask import Flask
from config import get_config
from extensions import init_extensions
from services.email_service import send_test_email


def main():
    """Send a test email to verify configuration."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_email.py your-email@example.com")
        sys.exit(1)

    recipient = sys.argv[1]

    # Create minimal Flask app for email testing
    # Point to the signaltrackers directory for templates
    signaltrackers_dir = Path(__file__).parent.parent / 'signaltrackers'
    app = Flask(
        __name__,
        template_folder=str(signaltrackers_dir / 'templates')
    )
    app.config.from_object(get_config())

    # Verify email configuration
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        print("ERROR: Email not configured!")
        print("\nPlease set the following environment variables:")
        print("  MAIL_SERVER (default: smtp-relay.brevo.com)")
        print("  MAIL_PORT (default: 587)")
        print("  MAIL_USE_TLS (default: True)")
        print("  MAIL_USERNAME (your email address)")
        print("  MAIL_PASSWORD (your SMTP password/key)")
        print("  MAIL_DEFAULT_SENDER (default: SignalTrackers <briefings@signaltrackers.com>)")
        sys.exit(1)

    # Initialize extensions (including Flask-Mail)
    init_extensions(app)

    print(f"Sending test email to: {recipient}")
    print(f"Using SMTP server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
    print(f"From: {app.config['MAIL_DEFAULT_SENDER']}")
    print()

    # Send test email within app context
    with app.app_context():
        success = send_test_email(recipient)

        if success:
            print("✓ Test email sent successfully!")
            print("\nCheck your inbox (and spam folder) for the test email.")
            print("If you don't receive it, verify:")
            print("  1. SMTP credentials are correct")
            print("  2. Sender email is verified with your email provider")
            print("  3. Recipient email address is valid")
        else:
            print("✗ Failed to send test email.")
            print("\nCheck the error messages above for details.")
            sys.exit(1)


if __name__ == '__main__':
    main()
