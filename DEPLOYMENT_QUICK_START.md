# 🚀 Quick Start: Deployment Guide

## Current Status

✅ **Server Ready**: 31.129.107.178
- Docker, Docker Compose, Nginx installed
- Database (PostgreSQL) and Redis running
- Application directory: `/opt/budget-app`

✅ **Code Ready**:
- Production Docker configurations created
- CI/CD workflow configured (GitHub Actions)
- All changes committed and pushed to GitHub

## ⚡ Next Steps (5 minutes)

### 1. Configure GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions → New repository secret**

Add these 3 secrets:

```
Name: PROD_HOST
Value: 31.129.107.178

Name: PROD_USERNAME  
Value: root

Name: PROD_SSH_KEY
Value: (paste your private SSH key - see below)
```

**Get your SSH private key**:
```bash
cat ~/.ssh/id_rsa
```
Copy the entire output including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`.

### 2. Enable GitHub Packages

Go to: **Settings → Actions → General → Workflow permissions**

Select: **"Read and write permissions"**

Click **Save**

### 3. Trigger Deployment

**Option A - Automatic** (recommended):
```bash
git commit --allow-empty -m "trigger first deployment"
git push origin main
```

**Option B - Manual**:
- Go to **Actions** tab in GitHub
- Click on "Deploy to Production" workflow
- Click "Run workflow" button

### 4. Monitor Deployment

- Go to **Actions** tab
- Watch the "Deploy to Production" workflow
- Deployment takes ~5-10 minutes
- Green checkmark = Success! ✅

### 5. Verify Deployment

Check that application is running:

```bash
# Via IP (works immediately)
curl http://31.129.107.178/health

# Check services status
ssh root@31.129.107.178 "cd /opt/budget-app && docker compose -f docker-compose.prod.yml ps"
```

Expected output: `{"status":"healthy"}`

### 6. Configure DNS (After Deployment Works)

Update DNS A record:
```
Type: A
Name: budget-west.shknv.ru
Value: 31.129.107.178
TTL: 300 (or default)
```

Wait 5-15 minutes for DNS propagation, then test:
```bash
curl http://budget-west.shknv.ru/health
```

### 7. Setup SSL Certificate

After DNS is configured and working:

```bash
ssh root@31.129.107.178

# Install SSL certificate
certbot --nginx -d budget-west.shknv.ru

# Follow the prompts:
# - Enter your email
# - Agree to Terms of Service
# - Choose "Yes" for HTTPS redirect
```

## 🎉 Done!

Your application is now deployed and accessible at:
- **HTTP**: http://budget-west.shknv.ru
- **HTTPS**: https://budget-west.shknv.ru (after SSL setup)

## 📋 Quick Commands

```bash
# SSH to server
ssh root@31.129.107.178

# Check status
cd /opt/budget-app && docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml down

# Start services
docker compose -f docker-compose.prod.yml up -d
```

## 🆘 Troubleshooting

### Deployment fails at "Build and push Backend image"

**Cause**: Workflow permissions not set

**Fix**: Go to Settings → Actions → General → Enable "Read and write permissions"

### Can't connect to server via SSH

**Cause**: SSH key not accepted by GitHub Actions

**Fix**: Make sure you copied the ENTIRE private key including headers:
```
-----BEGIN OPENSSH PRIVATE KEY-----
... your key content ...
-----END OPENSSH PRIVATE KEY-----
```

### Health check shows 502 Bad Gateway

**Cause**: Containers not running yet

**Fix**: Wait 2-3 minutes after deployment, containers need time to start

### DNS not working

**Cause**: DNS propagation takes time

**Fix**: 
- Check if record is configured correctly
- Wait 15-30 minutes
- Test with: `nslookup budget-west.shknv.ru`
- Meanwhile use: http://31.129.107.178

## 📚 More Information

- Full documentation: `docs/PRODUCTION_DEPLOYMENT.md`
- Server details: See deploy.yml workflow
- Issues: Check GitHub Actions logs

---

**Need help?** Check logs: `docker compose -f /opt/budget-app/docker-compose.prod.yml logs -f`
