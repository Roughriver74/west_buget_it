# Deployment Guide

## Quick Deploy

To deploy the application to production server:

```bash
./deploy-prod.sh
```

This script will:
1. ✅ Check connection to server
2. ✅ Backup current configuration
3. ✅ Upload updated files
4. ✅ Update CORS settings in .env
5. ✅ Rebuild and restart Docker services
6. ✅ Check service health
7. ✅ Show recent logs

## Manual Deploy

If you need to deploy manually:

```bash
# 1. Connect to server
ssh root@93.189.228.52

# 2. Navigate to project directory
cd /root/budget-app

# 3. Pull latest changes or update files
git pull  # if using git
# OR
# Upload files manually using scp

# 4. Update .env file with correct CORS settings
nano .env
# Set: CORS_ORIGINS='["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]'

# 5. Rebuild and restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 6. Check status
docker-compose -f docker-compose.prod.yml ps
docker logs it_budget_backend_prod

# 7. Test health endpoint
curl http://localhost:8000/health
```

## Environment Variables

Ensure these are set in `.env` on the server:

```bash
# CORS - CRITICAL for API access
CORS_ORIGINS='["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]'

# Database
DB_USER=budget_user
DB_PASSWORD=<strong-password>
DB_NAME=it_budget_db

# Security
SECRET_KEY=<32+ character random string>

# Application
DEBUG=False
```

## Troubleshooting

### 503 Service Unavailable

If you see 503 errors:

1. **Check backend is running:**
   ```bash
   docker ps | grep backend
   ```

2. **Check backend logs:**
   ```bash
   docker logs it_budget_backend_prod
   ```

3. **Check health endpoint:**
   ```bash
   docker exec it_budget_backend_prod curl http://localhost:8000/health
   ```

4. **Check Traefik logs:**
   ```bash
   docker logs <traefik-container-name>
   ```

### CORS Errors

If you see CORS preflight errors:

1. **Verify CORS_ORIGINS in .env:**
   ```bash
   grep CORS_ORIGINS .env
   ```
   Should include both frontend and API domains.

2. **Restart backend after changing .env:**
   ```bash
   docker-compose -f docker-compose.prod.yml restart backend
   ```

### Database Connection Issues

If backend can't connect to database:

1. **Check database is running:**
   ```bash
   docker ps | grep postgres
   ```

2. **Check database health:**
   ```bash
   docker exec it_budget_db_prod pg_isready -U budget_user
   ```

3. **Verify database credentials in .env**

## Post-Deployment Checklist

- [ ] Frontend loads at https://budget-west.shknv.ru
- [ ] API responds at https://api.budget-west.shknv.ru/health
- [ ] Login works (test with admin credentials)
- [ ] Can create/view expenses
- [ ] Department switching works
- [ ] No CORS errors in browser console

## Rollback

If deployment fails, restore from backup:

```bash
ssh root@93.189.228.52
cd /root/budget-app

# List backups
ls -lh backups/

# Restore latest backup
tar -xzf backups/backup-YYYYMMDD-HHMMSS.tar.gz

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

- **Logs:** `docker logs -f it_budget_backend_prod`
- **Metrics:** https://api.budget-west.shknv.ru/metrics (if Prometheus enabled)
- **Health:** https://api.budget-west.shknv.ru/health

## Support

If issues persist:
1. Check logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure Traefik is routing correctly
4. Check firewall rules allow traffic on ports 80/443
