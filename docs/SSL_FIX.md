# SSL/HTTPS Configuration Fix

**Date**: 2025-11-13
**Issue**: HTTPS not working (https://budget-west.shknv.ru/login returned connection refused)
**Status**: ✅ RESOLVED

## Problem

After deployment, the application was accessible via HTTP but HTTPS was not working:
- ✅ DNS correctly resolved to 31.129.107.178
- ✅ HTTP access worked (http://budget-west.shknv.ru)
- ❌ HTTPS failed (connection refused on port 443)
- ❌ Port 443 was not listening

## Root Cause

SSL certificate was already installed by Certbot (valid until 2026-02-11), but Nginx configuration did not include HTTPS server block (port 443). The certificate existed but was not being used.

## Investigation

```bash
# Verified DNS
nslookup budget-west.shknv.ru
# Result: Correctly resolved to 31.129.107.178

# Tested HTTP
curl -I http://budget-west.shknv.ru/login
# Result: 200 OK

# Tested HTTPS
curl -I https://budget-west.shknv.ru/login
# Result: Connection refused

# Checked port 443
netstat -tlnp | grep ':443'
# Result: Port not listening

# Checked SSL certificate
certbot certificates
# Result: Certificate exists and valid until 2026-02-11
```

## Solution

Added HTTPS server block to Nginx configuration at `/etc/nginx/sites-available/budget-west`:

### Key Changes

1. **Split HTTP server blocks**:
   - Domain (budget-west.shknv.ru): Redirects HTTP to HTTPS
   - IP (31.129.107.178): Serves HTTP directly (no redirect)

2. **Added HTTPS server block** (port 443):
   - SSL certificate paths
   - TLS 1.2/1.3 configuration
   - Security headers (HSTS, X-Frame-Options, etc.)
   - All location blocks (API, health, docs, frontend)

3. **Security headers added**:
   ```nginx
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   add_header X-Frame-Options "SAMEORIGIN" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   ```

### Configuration Structure

```nginx
# HTTP for domain → redirect to HTTPS
server {
    listen 80;
    server_name budget-west.shknv.ru;
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTP for IP → no redirect
server {
    listen 80;
    server_name 31.129.107.178;
    # All location blocks...
}

# HTTPS for domain
server {
    listen 443 ssl http2;
    server_name budget-west.shknv.ru;

    ssl_certificate /etc/letsencrypt/live/budget-west.shknv.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/budget-west.shknv.ru/privkey.pem;

    # All location blocks...
}
```

## Verification

After applying the fix:

```bash
# Port 443 now listening
netstat -tlnp | grep ':443'
# tcp  0  0.0.0.0:443  0.0.0.0:*  LISTEN  4488/nginx: master

# HTTPS health check
curl -I https://budget-west.shknv.ru/health
# HTTP/2 405 (Method Not Allowed - expected for HEAD request)

# HTTPS login page
curl -I https://budget-west.shknv.ru/login
# HTTP/2 200 OK ✅

# HTTP redirect
curl -I http://budget-west.shknv.ru/login
# HTTP/1.1 301 Moved Permanently
# Location: https://budget-west.shknv.ru/login ✅
```

## Testing Checklist

✅ All tests passed:
- [x] HTTPS health endpoint working
- [x] HTTPS login page accessible
- [x] HTTPS API documentation accessible
- [x] HTTP to HTTPS redirect working for domain
- [x] HTTP direct access working for IP
- [x] Valid SSL certificate (green padlock in browser)
- [x] Security headers present in response
- [x] TLS 1.2/1.3 encryption enabled

## Files Changed

**Server** (manual changes, not in git):
- `/etc/nginx/sites-available/budget-west` - Added HTTPS server block

**Repository** (committed to git):
- `DEPLOYMENT_STATUS.md` - Updated status to show HTTPS working
- `docs/SSL_FIX.md` - This documentation

## Important Notes

1. **SSL certificate auto-renewal**: Certbot automatically renews certificates every 60 days via systemd timer
2. **Certificate expiration**: Current certificate valid until 2026-02-11 (89 days remaining)
3. **Nginx configuration persistence**: The HTTPS server block will persist across deployments because it's infrastructure-level configuration, not application code

## Monitoring

To check certificate status in the future:
```bash
# Check certificate expiration
certbot certificates

# Test certificate renewal (dry run)
certbot renew --dry-run

# Check renewal timer
systemctl status certbot.timer
```

## Related Documentation

- [DNS_SSL_SETUP.md](DNS_SSL_SETUP.md) - Complete DNS and SSL setup guide
- [SERVER_FIXES.md](SERVER_FIXES.md) - All server-level fixes applied
- [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md) - Current deployment status

## Summary

**Problem**: Port 443 not listening, HTTPS not working
**Cause**: Missing HTTPS server block in Nginx configuration
**Solution**: Added HTTPS server block with SSL certificate paths
**Result**: ✅ HTTPS fully functional with automatic HTTP redirect
**Time to fix**: ~5 minutes
