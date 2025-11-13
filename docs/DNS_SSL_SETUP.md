# DNS and SSL Certificate Setup Guide

This guide covers DNS configuration and SSL certificate installation for the production server.

## Current Status

✅ **Application deployed and working**:
- HTTP: http://31.129.107.178 (working)
- Backend: http://31.129.107.178/health (working)
- Frontend: http://31.129.107.178/ (working)

❌ **HTTPS not configured yet**:
- DNS not pointing to new server
- SSL certificate not installed

## Step 1: Configure DNS

### DNS Records to Add

Add the following A record in your DNS provider:

```
Type: A
Name: budget-west.shknv.ru (or @ for root domain)
Value: 31.129.107.178
TTL: 300 (or default)
```

### DNS Providers

Common DNS providers and where to find settings:

- **Cloudflare**: DNS → Records → Add record
- **GoDaddy**: Domain Settings → DNS Management → Add
- **Namecheap**: Domain List → Manage → Advanced DNS
- **Reg.ru**: Domains → Your Domain → DNS servers and zone

### Verify DNS Propagation

After adding the A record, wait 5-30 minutes and verify:

```bash
# Check DNS resolution
nslookup budget-west.shknv.ru

# Should return:
# Name:    budget-west.shknv.ru
# Address: 31.129.107.178
```

Or use online tools:
- https://dnschecker.org
- https://whatsmydns.net

Test HTTP access via domain (before SSL):
```bash
curl http://budget-west.shknv.ru/health
# Should return: {"status":"healthy"}
```

## Step 2: Install SSL Certificate

**IMPORTANT**: Only proceed after DNS is working and `budget-west.shknv.ru` resolves to `31.129.107.178`!

### Install Certificate with Let's Encrypt

SSH to the server and run:

```bash
ssh root@31.129.107.178

# Install SSL certificate
certbot --nginx -d budget-west.shknv.ru
```

### Certbot Prompts

You'll be asked:

1. **Email address**: Enter your email for renewal notifications
2. **Terms of Service**: Type `A` to agree
3. **Share email**: Type `N` (optional)
4. **HTTPS redirect**: Type `2` to redirect all HTTP to HTTPS

### Expected Output

```
Congratulations! You have successfully enabled HTTPS on budget-west.shknv.ru
```

### Verify SSL Certificate

Test HTTPS access:

```bash
# From your computer
curl https://budget-west.shknv.ru/health
# Should return: {"status":"healthy"}

# Check certificate details
curl -v https://budget-west.shknv.ru/health 2>&1 | grep "SSL"
```

Open in browser:
- https://budget-west.shknv.ru

You should see a valid SSL certificate (green padlock in browser).

## Step 3: Update Configuration (if needed)

The Nginx configuration should already be correct from our deployment. Verify it includes both HTTP and HTTPS:

```bash
ssh root@31.129.107.178
cat /etc/nginx/sites-available/budget-west
```

It should have:
- HTTP server block (port 80) for Let's Encrypt verification and initial access
- HTTPS server block (port 443) added by Certbot

## Step 4: Update CORS Origins (Optional)

If you want to restrict CORS to HTTPS only, update `.env.prod` on the server:

```bash
ssh root@31.129.107.178
cd /opt/budget-app

# Edit .env.prod
nano .env.prod

# Update CORS_ORIGINS to:
CORS_ORIGINS=["https://budget-west.shknv.ru"]

# Restart backend
docker compose -f docker-compose.prod.yml restart backend
```

## Automatic Certificate Renewal

Certbot automatically sets up certificate renewal. Verify it:

```bash
ssh root@31.129.107.178

# Test renewal (dry run)
certbot renew --dry-run

# Should show: "Congratulations, all simulated renewals succeeded"
```

Certificates will auto-renew every 60 days via systemd timer.

Check renewal timer:
```bash
systemctl status certbot.timer
```

## Troubleshooting

### DNS Not Resolving

**Problem**: `nslookup` doesn't return the correct IP

**Solutions**:
- Wait longer (DNS propagation can take up to 24 hours)
- Check DNS record is correct in DNS provider
- Clear local DNS cache: `sudo killall -HUP mDNSResponder` (macOS)

### Certbot Fails with "Connection Refused"

**Problem**: Certbot can't verify domain ownership

**Causes**:
- DNS not propagated yet
- Nginx not running
- Port 80 blocked by firewall

**Solutions**:
```bash
# Check DNS first
nslookup budget-west.shknv.ru

# Check Nginx is running
systemctl status nginx

# Check port 80 is accessible
curl http://budget-west.shknv.ru/.well-known/acme-challenge/test
```

### Certificate Already Exists Error

**Problem**: Certbot says certificate already exists

**Solution**:
```bash
# Expand existing certificate
certbot --nginx -d budget-west.shknv.ru --expand

# Or force renewal
certbot --nginx -d budget-west.shknv.ru --force-renewal
```

### Mixed Content Warnings in Browser

**Problem**: Browser shows "mixed content" warnings

**Cause**: Frontend is trying to load resources over HTTP when page is HTTPS

**Solution**: All API calls should use relative URLs (already configured in frontend)

## Testing Checklist

After SSL installation, test:

- [ ] HTTPS health endpoint: `https://budget-west.shknv.ru/health`
- [ ] HTTPS frontend: `https://budget-west.shknv.ru`
- [ ] HTTP redirects to HTTPS: `http://budget-west.shknv.ru` → `https://...`
- [ ] Valid SSL certificate (green padlock in browser)
- [ ] Login works
- [ ] API calls work
- [ ] No mixed content warnings

## Security Headers

After SSL is installed, verify security headers:

```bash
curl -I https://budget-west.shknv.ru | grep -E "(Strict|X-Frame|X-Content)"
```

Should see:
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options`
- `X-Content-Type-Options`

## Final Notes

- **Certificate expires**: 90 days (auto-renews at 60 days)
- **Renewal logs**: `/var/log/letsencrypt/letsencrypt.log`
- **Certificate location**: `/etc/letsencrypt/live/budget-west.shknv.ru/`
- **Renewal hook**: None needed, Nginx auto-reloads

## Need Help?

If you encounter issues:

1. Check Nginx logs: `tail -f /var/log/nginx/error.log`
2. Check Certbot logs: `tail -f /var/log/letsencrypt/letsencrypt.log`
3. Verify DNS: `nslookup budget-west.shknv.ru`
4. Test HTTP first: `curl http://budget-west.shknv.ru/health`
