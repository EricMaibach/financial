#!/usr/bin/env python3
"""
Direct SMTP Test

Tests SMTP connection directly without Flask-Mail to diagnose authentication issues.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp():
    """Test SMTP connection directly."""

    # Get credentials from environment
    smtp_server = os.environ.get('MAIL_SERVER', 'smtp-relay.brevo.com')
    smtp_port = int(os.environ.get('MAIL_PORT', 587))
    username = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    sender = os.environ.get('MAIL_DEFAULT_SENDER', username)

    print(f"Testing SMTP connection...")
    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"Username: {username}")
    print(f"Password length: {len(password) if password else 0}")
    print(f"Sender: {sender}")
    print()

    if not username or not password:
        print("ERROR: MAIL_USERNAME or MAIL_PASSWORD not set!")
        return False

    try:
        # Create SMTP connection
        print("Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.set_debuglevel(1)  # Show all SMTP communication

        print("\nStarting TLS...")
        server.starttls()

        print("\nAuthenticating...")
        server.login(username, password)

        print("\n✓ Authentication successful!")

        # Try to send a test email
        recipient = input("\nEnter recipient email (or press Enter to skip sending): ").strip()

        if recipient:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'Direct SMTP Test'
            msg['From'] = sender
            msg['To'] = recipient

            text = "This is a test email sent directly via SMTP (bypassing Flask-Mail)."
            html = "<html><body><p>This is a test email sent directly via SMTP (bypassing Flask-Mail).</p></body></html>"

            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))

            print(f"\nSending test email to {recipient}...")
            server.sendmail(sender, [recipient], msg.as_string())
            print("✓ Email sent successfully!")

        server.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n✗ Authentication failed: {e}")
        print("\nPossible causes:")
        print("1. Incorrect SMTP key")
        print("2. Incorrect username (should be the email you signed up with)")
        print("3. Sender email not verified in Brevo")
        print("4. Account restrictions in Brevo")
        return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == '__main__':
    test_smtp()
