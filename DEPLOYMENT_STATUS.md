# 🚀 Deployment Status

**Last Updated**: 2025-11-13
**Server**: 31.129.107.178
**Domain**: budget-west.shknv.ru (not configured yet)

## ✅ Current Status: DEPLOYED & WORKING

### HTTP Access (Working Now)

- ✅ **Frontend**: http://31.129.107.178/
- ✅ **Backend API**: http://31.129.107.178/api/v1/health
- ✅ **Health Check**: http://31.129.107.178/health
- ✅ **API Docs**: http://31.129.107.178/docs

### HTTPS Access (Pending DNS Setup)

- ❌ **HTTPS**: Not working yet (DNS not configured)
- 📋 **Action Required**: Follow [DNS_SSL_SETUP.md](docs/DNS_SSL_SETUP.md)

## 🎯 Completed Setup

### Server Infrastructure
- [x] Ubuntu 24.04 LTS server ready
- [x] Docker & Docker Compose installed
- [x] Nginx reverse proxy configured
- [x] PostgreSQL database running
- [x] Redis cache running
- [x] All services healthy

### Application Deployment
- [x] Backend Docker image built and deployed
- [x] Frontend Docker image built and deployed
- [x] Database migrations applied
- [x] Environment variables configured
- [x] CORS configured correctly

### CI/CD Pipeline
- [x] GitHub Actions workflow configured
- [x] Automatic image building on push to main
- [x] Automatic deployment to server
- [x] Automatic database migrations
- [x] Health checks and verification
- [x] .env symlink auto-creation

### Security
- [x] Rate limiting enabled (10 req/s API, 5 req/min login)
- [x] Security headers configured
- [x] Non-root user in containers
- [x] Proper CORS configuration
- [ ] SSL certificate (pending DNS setup)

## 📊 Service Status

```
Service          Status      Port    Health
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend          ✅ Healthy   8888    ✅ OK
Frontend         ✅ Running   8080    ✅ OK
PostgreSQL       ✅ Healthy   5432    ✅ OK
Redis            ✅ Healthy   6379    ✅ OK
Nginx            ✅ Running   80      ✅ OK
```

## 🔄 Deployment Workflow

Every `git push` to `main` branch automatically:

1. ✅ Builds Docker images
2. ✅ Pushes to GitHub Container Registry
3. ✅ SSH to production server
4. ✅ Creates .env symlink if needed
5. ✅ Pulls latest images
6. ✅ Restarts services with zero downtime
7. ✅ Runs database migrations
8. ✅ Verifies deployment health
9. ✅ Cleans up old images

**Average deployment time**: 3-5 minutes

## 📝 Next Steps

### 1. Configure DNS (Required for HTTPS)

Add A record in your DNS provider:
```
Type: A
Name: budget-west.shknv.ru
Value: 31.129.107.178
TTL: 300
```

**Guide**: [DNS_SSL_SETUP.md](docs/DNS_SSL_SETUP.md)

### 2. Install SSL Certificate (After DNS)

```bash
ssh root@31.129.107.178
certbot --nginx -d budget-west.shknv.ru
```

### 3. Change Default Passwords (Recommended)

Current passwords are defaults and should be changed for production:

```bash
ssh root@31.129.107.178
cd /opt/budget-app

# Edit .env.prod
nano .env.prod

# Change:
# - POSTGRES_PASSWORD (currently: budget_pass)
# - SECRET_KEY (currently: needs strong random value)

# Restart services
docker compose -f docker-compose.prod.yml restart
```

## 🛠️ Maintenance Commands

### Check Status

```bash
# SSH to server
ssh root@31.129.107.178

# Check all services
cd /opt/budget-app
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Check health
curl http://localhost:8888/health
```

### Manual Deployment

If you need to deploy without pushing to Git:

```bash
ssh root@31.129.107.178
cd /opt/budget-app

# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Restart services
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Restart Services

```bash
ssh root@31.129.107.178
cd /opt/budget-app

# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

## 📚 Documentation

- [DEPLOYMENT_QUICK_START.md](DEPLOYMENT_QUICK_START.md) - Quick start guide
- [DNS_SSL_SETUP.md](docs/DNS_SSL_SETUP.md) - DNS and SSL certificate setup
- [SERVER_FIXES.md](docs/SERVER_FIXES.md) - Fixes applied during deployment
- [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) - Full deployment guide

## 🔍 Troubleshooting

### Application Not Accessible

```bash
# Check if containers are running
docker compose -f /opt/budget-app/docker-compose.prod.yml ps

# Check Nginx status
systemctl status nginx

# Test backend directly
curl http://localhost:8888/health

# Test frontend directly
curl http://localhost:8080/
```

### Deployment Failed

1. Check GitHub Actions logs: https://github.com/Roughriver74/west_buget_it/actions
2. Check if secrets are configured correctly
3. Verify SSH access to server
4. Check server logs

### Database Issues

```bash
# Check database logs
docker compose -f /opt/budget-app/docker-compose.prod.yml logs db

# Access database
docker compose -f /opt/budget-app/docker-compose.prod.yml exec db psql -U budget_user -d it_budget_db

# Run migrations manually
docker compose -f /opt/budget-app/docker-compose.prod.yml exec backend alembic upgrade head
```

## 🎉 Success Criteria

All checks passed:
- ✅ Application accessible via HTTP
- ✅ Backend API responding
- ✅ Frontend loading
- ✅ Database connected
- ✅ Redis working
- ✅ CI/CD pipeline working
- ✅ Health checks passing
- ⏳ SSL certificate (pending DNS setup)

## 📞 Support

For issues:
1. Check logs first
2. Review documentation
3. Check GitHub Actions for deployment errors
4. Verify server resources: `htop`, `df -h`

## 🔐 Security Checklist

Before going live:
- [ ] Change POSTGRES_PASSWORD
- [ ] Update SECRET_KEY
- [ ] Review CORS_ORIGINS
- [ ] Install SSL certificate
- [ ] Enable firewall (ufw)
- [ ] Setup backup strategy
- [ ] Configure monitoring
- [ ] Review Nginx rate limits

---

**Server Access**: `ssh root@31.129.107.178`
**Application Directory**: `/opt/budget-app`
**Nginx Config**: `/etc/nginx/sites-available/budget-west`
