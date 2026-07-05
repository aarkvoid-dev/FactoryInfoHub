#!/usr/bin/env python3
import smtplib
import socket

# ---------- YOUR EXACT SETTINGS (hardcoded) ----------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "info@fashionchemistry.net"
EMAIL_HOST_PASSWORD = "xmbh jxdr iuam zwhs"   # <-- CHANGE THIS
DEFAULT_FROM_EMAIL = "info@fashionchemistry.net"

# Optional: send a test email to yourself
TEST_RECIPIENT = "motulshaikh@gmail.com"  # change to your real email

# ----------------------------------------------------

def test_smtp():
    print(f"Connecting to {EMAIL_HOST}:{EMAIL_PORT} (TLS={EMAIL_USE_TLS})...")

    # 1. Check that the host resolves
    try:
        socket.gethostbyname(EMAIL_HOST)
    except socket.gaierror:
        print(f"❌ Hostname '{EMAIL_HOST}' does not resolve.")
        return False

    try:
        # 2. Connect and start TLS
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.ehlo()
        if EMAIL_USE_TLS:
            server.starttls()
            server.ehlo()

        # 3. Login
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("✅ SMTP login successful – credentials are valid!")

        # 4. (Optional) send a test email
        if TEST_RECIPIENT:
            subject = "Test email from Django SMTP checker"
            body = "This is a test email to verify that the email configuration is working."
            msg = f"Subject: {subject}\n\n{body}"
            server.sendmail(DEFAULT_FROM_EMAIL, [TEST_RECIPIENT], msg)
            print(f"✅ Test email sent to {TEST_RECIPIENT}")

        server.quit()
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your password or use an App Password.")
        return False
    except (smtplib.SMTPException, socket.timeout, ConnectionRefusedError) as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_smtp()
    exit(0 if success else 1)