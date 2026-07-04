#!/usr/bin/env python3
import os
import smtplib
import socket
import sys

# Read settings from environment (same as your Django config)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'sg2nlvphout-v01.shr.prod.sin2.secureserver.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Optional: recipient for a test email
TEST_RECIPIENT = os.environ.get('TEST_RECIPIENT', '')  # e.g., your-email@example.com

def test_email():
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        print("❌ EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set in environment.")
        print("   Please set them and try again.")
        return False

    print(f"Testing SMTP connection to {EMAIL_HOST}:{EMAIL_PORT}...")
    try:
        # 1. Check that the hostname resolves
        socket.gethostbyname(EMAIL_HOST)
    except socket.gaierror:
        print(f"❌ Hostname '{EMAIL_HOST}' does not resolve.")
        return False

    try:
        # 2. Connect to SMTP server
        if EMAIL_PORT == 465:
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=10)
        else:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
            server.ehlo()
            if EMAIL_USE_TLS:
                server.starttls()
                server.ehlo()

        # 3. Attempt login
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("✅ SMTP login successful – credentials are valid!")

        # 4. Optionally send a test email
        if TEST_RECIPIENT:
            subject = "Test email from Django SMTP checker"
            body = "This is a test email to verify that the email configuration is working."
            msg = f"Subject: {subject}\n\n{body}"
            server.sendmail(EMAIL_HOST_USER, [TEST_RECIPIENT], msg)
            print(f"✅ Test email sent to {TEST_RECIPIENT}")

        server.quit()
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP authentication failed. Check your username/password.")
        print("   If you use 2FA, you may need an app-specific password.")
        return False
    except (smtplib.SMTPException, socket.timeout, ConnectionRefusedError) as e:
        print(f"❌ SMTP connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_email()
    sys.exit(0 if success else 1)