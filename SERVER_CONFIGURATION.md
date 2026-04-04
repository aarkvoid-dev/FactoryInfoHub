# Server Configuration - infoizharjk

This document contains the server-specific configuration details for the FactoryInfoHub deployment.

## Server Details

| Property | Value |
|----------|-------|
| **Server Name** | infoizharjk |
| **IP Address** | 68.178.172.223 |
| **Hostname** | 223.172.178.68.host.secureserver.net |
| **Operating System** | Ubuntu 24.04 |
| **Location** | Asia (Singapore) |
| **Provider** | GoDaddy |

## SMTP Configuration

The application uses GoDaddy's SMTP relay server for sending emails.

| Setting | Value |
|---------|-------|
| **SMTP Relay Server** | `sg2nlvphout-v01.shr.prod.sin2.secureserver.net` |
| **Port** | 587 |
| **TLS** | Enabled |
| **Authentication** | Not required (relay from localhost) |

### Important Notes

1. **SMTP Relay Server**: This is specific to your GoDaddy hosting account. If you migrate to a different server, you'll need to update this value from your new hosting panel.

2. **Email Sending**: The SMTP relay works from the server itself (localhost). No username/password is required when sending from the server.

3. **From Email**: Set `DEFAULT_FROM_EMAIL` to a valid domain email address to improve deliverability.

## Configuration Files Updated

The following files have been updated with the GoDaddy SMTP configuration:

1. **`.env`** - Production environment variables
2. **`FactoryInfoHub/settings.py`** - Default SMTP host fallback
3. **`.env.example`** - Example configuration for reference

## Deployment Checklist

- [x] SMTP relay server configured
- [x] Environment variables updated
- [x] Settings.py updated with GoDaddy defaults
- [ ] Domain DNS configured (update ALLOWED_HOSTS)
- [ ] SSL certificate installed (enable SECURE_SSL_REDIRECT)
- [ ] PostgreSQL database configured
- [ ] Redis cache configured
- [ ] Nginx configured
- [ ] Gunicorn configured
- [ ] Firewall rules configured

## Troubleshooting

### Email Not Sending

1. Check if the SMTP relay server is correct in your GoDaddy hosting panel
2. Verify port 587 is not blocked by firewall
3. Check Django logs: `/var/log/factoryinfohub/django.log`
4. Test email connectivity:
   ```bash
   telnet sg2nlvphout-v01.shr.prod.sin2.secureserver.net 587
   ```

### Finding Your SMTP Relay Server

1. Log in to your GoDaddy hosting account
2. Go to Dashboard > Monitoring > Your Server
3. Look for "SMTP relay server" in the Server section
4. Copy the value and update `.env` file

## Security Reminders

- Keep your `SECRET_KEY` secure and never commit it to version control
- Update `ALLOWED_HOSTS` with your actual domain name
- Enable SSL/HTTPS in production
- Set strong database passwords
- Regularly update Ubuntu packages: `sudo apt update && sudo apt upgrade`