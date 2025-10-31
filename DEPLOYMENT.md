# 🚀 Production Deployment Guide

## ❗ Fix for 504 Gateway Timeout Error

If you're experiencing **504 Gateway Timeout** errors after deployment, it's because Traefik needs complete routing configuration.

### What Was Fixed

The `docker-compose.prod.yml` now includes **complete Traefik labels** with:

✅ **Router rules** - Define which domains route to which services
✅ **Entrypoints** - HTTP (port 80) and HTTPS (port 443)
✅ **TLS configuration** - Automatic HTTPS with Let's Encrypt
✅ **HTTP to HTTPS redirect** - Automatic upgrade to secure connection
✅ **CORS middleware** - Proper handling of cross-origin requests

### Required Environment Variables

Add these to your `.env` file (or Coolify environment variables):

```bash
# Traefik Domain Configuration
FRONTEND_DOMAIN=budget-west.shknv.ru
BACKEND_DOMAIN=api.budget-west.shknv.ru

# CORS Origins (must match frontend domain)
CORS_ORIGINS='["https://budget-west.shknv.ru"]'

# Frontend API URL (must match backend domain)
VITE_API_URL=https://api.budget-west.shknv.ru
```

## 📋 Deployment Steps

### 1. Prepare Environment File

```bash
# Copy example and edit
cp .env.prod.example .env

# Edit .env and set:
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - DB_PASSWORD
# - ADMIN_PASSWORD
# - FRONTEND_DOMAIN
# - BACKEND_DOMAIN
# - CORS_ORIGINS
# - VITE_API_URL
```

### 2. Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service health
docker-compose -f docker-compose.prod.yml ps
```

### 3. Verify Traefik Configuration

Traefik should automatically:
- Route `https://budget-west.shknv.ru` → Frontend (port 80)
- Route `https://api.budget-west.shknv.ru` → Backend (port 8000)
- Redirect HTTP → HTTPS
- Request SSL certificates from Let's Encrypt
- Apply CORS headers for API requests

### 4. DNS Configuration

Make sure your DNS records point to your server:

```
budget-west.shknv.ru     → A record → your-server-ip
api.budget-west.shknv.ru → A record → your-server-ip
```

## 🔧 Traefik Configuration Explained

### Backend Labels

```yaml
labels:
  # Enable Traefik
  - "traefik.enable=true"

  # Define service (backend running on port 8000)
  - "traefik.http.services.backend.loadbalancer.server.port=8000"

  # HTTPS Router (websecure = port 443)
  - "traefik.http.routers.backend.rule=Host(`api.budget-west.shknv.ru`)"
  - "traefik.http.routers.backend.entrypoints=websecure"
  - "traefik.http.routers.backend.tls=true"
  - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
  - "traefik.http.routers.backend.middlewares=backend-cors"

  # HTTP Router (web = port 80) → redirects to HTTPS
  - "traefik.http.routers.backend-http.rule=Host(`api.budget-west.shknv.ru`)"
  - "traefik.http.routers.backend-http.entrypoints=web"
  - "traefik.http.routers.backend-http.middlewares=redirect-to-https"

  # CORS Middleware
  - "traefik.http.middlewares.backend-cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS,PATCH"
  - "traefik.http.middlewares.backend-cors.headers.accesscontrolalloworiginlist=https://budget-west.shknv.ru"
```

### Frontend Labels

```yaml
labels:
  # Enable Traefik
  - "traefik.enable=true"

  # Define service (nginx running on port 80)
  - "traefik.http.services.frontend.loadbalancer.server.port=80"

  # HTTPS Router
  - "traefik.http.routers.frontend.rule=Host(`budget-west.shknv.ru`)"
  - "traefik.http.routers.frontend.entrypoints=websecure"
  - "traefik.http.routers.frontend.tls=true"
  - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"

  # HTTP Router → redirects to HTTPS
  - "traefik.http.routers.frontend-http.rule=Host(`budget-west.shknv.ru`)"
  - "traefik.http.routers.frontend-http.entrypoints=web"
  - "traefik.http.routers.frontend-http.middlewares=redirect-to-https"
```

## 🐛 Troubleshooting

### Still Getting 504 Error?

1. **Check container health:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```
   All services should show `healthy` status.

2. **Check backend logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   ```
   Look for migration errors or startup issues.

3. **Check Traefik logs:**
   ```bash
   docker logs traefik  # or whatever your Traefik container name is
   ```

4. **Verify environment variables:**
   ```bash
   docker-compose -f docker-compose.prod.yml config | grep -A5 labels
   ```
   Make sure domains are correctly substituted.

5. **Test health endpoints:**
   ```bash
   # Inside backend container
   docker exec it_budget_backend_prod curl http://localhost:8000/health

   # Inside frontend container
   docker exec it_budget_frontend_prod curl http://localhost:80/
   ```

### Database Connection Issues

If backend fails to start:

```bash
# Check database is ready
docker exec it_budget_db_prod pg_isready -U budget_user

# Check backend can connect
docker exec it_budget_backend_prod python -c "
from app.db.session import engine
print('Database connection:', engine.connect())
"
```

### CORS Errors in Browser

If you see CORS errors in browser console:

1. Make sure `CORS_ORIGINS` in `.env` matches your frontend domain exactly
2. Restart backend after changing CORS settings:
   ```bash
   docker-compose -f docker-compose.prod.yml restart backend
   ```

## 📚 Additional Resources

- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **Coolify Documentation**: https://coolify.io/docs
- **Project README**: [README.md](./README.md)
- **Development Guide**: [CLAUDE.md](./CLAUDE.md)

## 🔒 Security Checklist

Before going live:

- [ ] Changed `SECRET_KEY` to secure random value
- [ ] Changed `DB_PASSWORD` to strong password
- [ ] Changed `ADMIN_PASSWORD` from default
- [ ] Set `DEBUG=False`
- [ ] Updated `CORS_ORIGINS` to production domains only
- [ ] Configured SSL certificates (automatic with Let's Encrypt)
- [ ] Setup database backups
- [ ] Configured Sentry for error tracking (optional)
- [ ] Reviewed firewall rules
- [ ] Enabled rate limiting (Redis)

## 📞 Support

For issues or questions:
- Create issue on GitHub
- Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Review [CLAUDE.md](./CLAUDE.md) for architecture details
