# Server Configuration Fixes

This document describes the fixes applied to the production server during initial deployment.

## Issues Fixed

### 1. Docker Image Registry Authentication

**Problem**: Server couldn't pull Docker images from GitHub Container Registry (403 Forbidden).

**Solution**: Authenticated server with GitHub Personal Access Token:
```bash
echo 'GITHUB_TOKEN' | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

**For Future**: Either:
- Make packages public on GitHub
- Or keep token refreshed on server

### 2. CORS Origins Format

**Problem**: Backend crashed with error parsing CORS_ORIGINS environment variable.

**Original (wrong)**:
```bash
CORS_ORIGINS=https://budget-west.shknv.ru,http://budget-west.shknv.ru
```

**Fixed (correct)**:
```bash
CORS_ORIGINS=["https://budget-west.shknv.ru","http://budget-west.shknv.ru","http://31.129.107.178"]
```

**Changes Made**:
1. Updated `.env.prod` with JSON array format
2. Changed `docker-compose.prod.yml` to use variable: `CORS_ORIGINS=${CORS_ORIGINS}`
3. Created symlink: `.env -> .env.prod` (Docker Compose requires `.env` for variable substitution)

### 3. Database Password Mismatch

**Problem**: Backend couldn't connect to database due to password mismatch.

**Cause**: Database was created with default password `budget_pass`, but `.env.prod` had a different password.

**Solution**: Updated `.env.prod` to use `budget_pass` to match existing database.

**For Production**: Change this password and recreate database!

### 4. Nginx Configuration for HTTP Access

**Problem**: Nginx returned 404 for all HTTP requests because certbot moved all locations to HTTPS block.

**Solution**: Created new Nginx configuration with proper HTTP server block:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name budget-west.shknv.ru 31.129.107.178;

    location /api/ {
        proxy_pass http://127.0.0.1:8888;
        # ... proxy headers
    }

    location /health {
        proxy_pass http://127.0.0.1:8888/health;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        # ... proxy headers
    }
}
```

**Note**: Added IP address `31.129.107.178` to `server_name` for direct IP access before DNS is configured.

## Server File Locations

- `/opt/budget-app/` - Application directory
- `/opt/budget-app/.env.prod` - Production environment variables
- `/opt/budget-app/.env` - Symlink to `.env.prod`
- `/opt/budget-app/docker-compose.prod.yml` - Docker Compose configuration
- `/etc/nginx/sites-available/budget-west` - Nginx configuration
- `/etc/nginx/sites-enabled/budget-west` - Symlink to above

## Required Server Configuration

### Environment Variables (.env.prod)

```bash
# Database
POSTGRES_DB=it_budget_db
POSTGRES_USER=budget_user
POSTGRES_PASSWORD=budget_pass  # CHANGE IN PRODUCTION!

# CORS (JSON array format)
CORS_ORIGINS=["https://budget-west.shknv.ru","http://budget-west.shknv.ru","http://31.129.107.178"]

# Backend
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=False

# Application
APP_NAME="IT Budget Manager"
API_PREFIX=/api/v1

# Redis
REDIS_URL=redis://redis:6379

# Docker Registry
DOCKER_REGISTRY=ghcr.io
DOCKER_USERNAME=roughriver74
VERSION=latest
```

### Docker Compose (.env symlink)

Docker Compose needs `.env` file (not `.env.prod`) for variable substitution:

```bash
cd /opt/budget-app
ln -sf .env.prod .env
```

## Verification Commands

Check services:
```bash
cd /opt/budget-app
docker compose -f docker-compose.prod.yml ps
```

Check health:
```bash
curl http://31.129.107.178/health
# Should return: {"status":"healthy"}
```

Check frontend:
```bash
curl -I http://31.129.107.178/
# Should return: 200 OK
```

Check backend logs:
```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

## Future Deployments

GitHub Actions workflow automatically:
1. Builds Docker images
2. Pushes to GitHub Container Registry
3. Pulls images on server
4. Restarts services
5. Runs database migrations

No manual intervention needed after initial setup!

## Security Notes

⚠️ **Before production use**:
1. Change `POSTGRES_PASSWORD` to a strong password
2. Update `SECRET_KEY` to a strong random value (min 32 chars)
3. Recreate database with new password
4. Consider making Docker packages private and using GitHub token auth

## Contact

For issues, check:
- GitHub Actions logs: https://github.com/Roughriver74/west_buget_it/actions
- Server logs: `docker compose -f /opt/budget-app/docker-compose.prod.yml logs`
- Nginx logs: `/var/log/nginx/error.log`
