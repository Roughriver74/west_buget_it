# Production Deployment Guide

## Server Information
- **Host**: 31.129.107.178
- **Domain**: budget-west.shknv.ru (update DNS to point to new server)
- **OS**: Ubuntu 24.04.3 LTS
- **Application Directory**: /opt/budget-app

## Prerequisites

### 1. GitHub Repository Secrets

Configure the following secrets in GitHub repository settings (`Settings > Secrets and variables > Actions`):

```
PROD_HOST=31.129.107.178
PROD_USERNAME=root
PROD_SSH_KEY=<your_private_ssh_key>
```

To get your SSH private key:
```bash
cat ~/.ssh/id_rsa
```

Copy the entire output including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`.

### 2. GitHub Container Registry Access

The GitHub Actions workflow automatically uses `GITHUB_TOKEN` to push images to GitHub Container Registry (ghcr.io).

Ensure your repository has Packages > Write permission:
- Go to `Settings > Actions > General`
- Under "Workflow permissions", select "Read and write permissions"

## Deployment Process

### Automatic Deployment (Recommended)

1. **Push to main branch**:
   ```bash
   git push origin main
   ```

2. **Monitor deployment**:
   - Go to `Actions` tab in GitHub repository
   - Watch the `Deploy to Production` workflow
   - Deployment takes ~5-10 minutes

### Manual Deployment

If you need to deploy manually:

```bash
# SSH into server
ssh root@31.129.107.178

# Navigate to app directory
cd /opt/budget-app

# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Start services
docker compose -f docker-compose.prod.yml up -d

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

## SSL Certificate Setup

After DNS is configured and pointing to new server:

```bash
# SSH into server
ssh root@31.129.107.178

# Install SSL certificate
certbot --nginx -d budget-west.shknv.ru

# Follow prompts to:
# 1. Enter email address
# 2. Agree to Terms of Service
# 3. Choose whether to share email with EFF
# 4. Choose redirect option (recommended: Yes)

# Certbot will automatically:
# - Obtain certificate from Let's Encrypt
# - Update Nginx configuration
# - Setup auto-renewal
```

## Verify Deployment

Check application health:

```bash
# Check backend API
curl https://budget-west.shknv.ru/health

# Check frontend
curl https://budget-west.shknv.ru/

# Check API docs
curl https://budget-west.shknv.ru/docs
```

## Configuration Files

### Production Environment Variables

Edit `/opt/budget-app/.env.prod` on the server:

```bash
ssh root@31.129.107.178
nano /opt/budget-app/.env.prod
```

Important settings:
- `SECRET_KEY`: Generate strong random key (32+ characters)
- `POSTGRES_PASSWORD`: Set strong database password
- `CORS_ORIGINS`: Set to your domain

### Docker Compose

Main configuration file: `/opt/budget-app/docker-compose.prod.yml`

Services:
- **db**: PostgreSQL 15
- **redis**: Redis 7 for caching
- **backend**: FastAPI application (port 8888)
- **frontend**: React + Nginx (port 8080)
- **watchtower**: Auto-update containers (checks every 5 minutes)

### Nginx Configuration

Main config: `/etc/nginx/sites-available/budget-west`

Features:
- Rate limiting (10 req/s for API, 5 req/min for login)
- Security headers
- Gzip compression
- Static asset caching
- Health check endpoints

## Monitoring

### View Logs

```bash
# All services
docker compose -f /opt/budget-app/docker-compose.prod.yml logs -f

# Specific service
docker compose -f /opt/budget-app/docker-compose.prod.yml logs -f backend
docker compose -f /opt/budget-app/docker-compose.prod.yml logs -f frontend

# Nginx logs
tail -f /var/log/nginx/budget-west-access.log
tail -f /var/log/nginx/budget-west-error.log
```

### Check Service Health

```bash
# Docker containers
docker ps

# Container health
docker inspect budget_backend_prod | grep -A 10 "Health"
docker inspect budget_frontend_prod | grep -A 10 "Health"

# Service endpoints
curl http://localhost:8888/health  # Backend
curl http://localhost:8080/         # Frontend
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it budget_db_prod psql -U budget_user -d it_budget_db

# Run migrations
docker compose -f /opt/budget-app/docker-compose.prod.yml exec backend alembic upgrade head

# Check migration status
docker compose -f /opt/budget-app/docker-compose.prod.yml exec backend alembic current
```

## Maintenance

### Update Application

Application updates happen automatically via GitHub Actions on push to main.

Manual update:
```bash
cd /opt/budget-app
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Backup Database

```bash
# Create backup
docker exec budget_db_prod pg_dump -U budget_user it_budget_db > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i budget_db_prod psql -U budget_user -d it_budget_db < backup_20250413.sql
```

### Clean Up Old Images

```bash
# Remove unused images
docker image prune -af

# Remove stopped containers
docker container prune -f

# Remove unused volumes
docker volume prune -f
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs budget_backend_prod
docker logs budget_frontend_prod

# Check configuration
docker inspect budget_backend_prod
```

### Database Connection Issues

```bash
# Check database is running
docker ps | grep budget_db_prod

# Test connection
docker exec budget_backend_prod pg_isready -h db -p 5432
```

### Nginx Issues

```bash
# Test configuration
nginx -t

# Restart nginx
systemctl restart nginx

# Check status
systemctl status nginx
```

### SSL Certificate Issues

```bash
# Test renewal
certbot renew --dry-run

# Force renewal
certbot renew --force-renewal

# Check certificate status
certbot certificates
```

## Rollback

If deployment fails:

```bash
# List available images
docker images | grep budget

# Use specific version
cd /opt/budget-app
export VERSION=<previous-sha>
docker compose -f docker-compose.prod.yml up -d
```

## Performance Tuning

### Backend Workers

Adjust worker count in `/opt/budget-app/docker-compose.prod.yml`:

```yaml
backend:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Recommended: `workers = (2 x CPU cores) + 1`

### Database Connections

Tune PostgreSQL settings in docker-compose.prod.yml:

```yaml
db:
  environment:
    POSTGRES_MAX_CONNECTIONS: 100
    POSTGRES_SHARED_BUFFERS: 256MB
```

## Security Checklist

- [ ] Strong SECRET_KEY configured
- [ ] Strong database password set
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] SSH key-based authentication enabled
- [ ] Regular backups scheduled
- [ ] Monitoring and alerts setup
- [ ] Application logs rotated

## Support

For issues or questions:
- Check logs first: `docker compose logs -f`
- Review documentation: `docs/`
- Check GitHub Actions logs for deployment failures
