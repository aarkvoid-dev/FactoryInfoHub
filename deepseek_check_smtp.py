import smtplib

email = "info@fashionchemistry.net"
password = "ztvi btmr wsiu kqws"
smtp_host = "smtp.fashionchemistry.net"   # <-- change to the actual host
smtp_port = 587                           # <-- change if needed

try:
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
    else:
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.ehlo()
        if smtp_port == 587:
            server.starttls()
            server.ehlo()
    server.login(email, password)
    server.quit()
    print("✅ Login successful – account is working!")
except smtplib.SMTPAuthenticationError:
    print("❌ Wrong password or user (check credentials/app‑password)")
except Exception as e:
    print(f"❌ Failed: {e}")