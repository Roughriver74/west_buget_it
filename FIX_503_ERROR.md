# 🔧 Fixing 503 Service Unavailable Error

## Your Error
```
[Error] Preflight response is not successful. Status code: 503
[Error] Fetch API cannot load https://api.budget-west.shknv.ru/api/v1/auth/login
due to access control checks.
```

**What this means:** Backend API is **not accessible** through Traefik. The OPTIONS request (CORS preflight) gets 503 error.

---

## 🚀 Quick Fix Steps

### Step 1: Connect to Your Server

```bash
ssh root@93.189.228.52
cd /path/to/your/project  # Navigate to project directory
```

### Step 2: Run Diagnostic Script

```bash
# Make script executable (first time only)
chmod +x scripts/diagnose-503.sh

# Run diagnostics
./scripts/diagnose-503.sh
```

**Look for these key indicators:**

#### ✅ **Good Signs:**
- Backend container status: `Up (healthy)`
- Backend /health responds: `{"status":"healthy"}`
- OPTIONS request returns `200 OK` with CORS headers

#### ❌ **Bad Signs:**
- Backend container: `Up (unhealthy)` or `Exited`
- Backend /health: No response or error
- OPTIONS request returns `503` or `502`

---

## 🔍 Common Causes & Fixes

### Cause 1: Backend Container Not Running ❌

**Check:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

**If backend shows "Exited" or "unhealthy":**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend --tail=100

# Common issues in logs:
# - Database connection error → Check DB container
# - Import errors → Missing dependencies
# - Configuration errors → Check environment variables
```

**Fix:**
```bash
# Restart backend
docker-compose -f docker-compose.prod.yml restart backend

# Or rebuild if code changed
docker-compose -f docker-compose.prod.yml up -d --build backend

# Watch logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Wait 1-2 minutes for backend to fully start** (migrations take time).

---

### Cause 2: Backend Starting Up (Health Check Failed) ⏳

Backend might still be starting. The entrypoint script:
1. Waits for database (up to 30 attempts)
2. Runs migrations
3. Creates admin user
4. Starts Gunicorn

**This can take 1-2 minutes!**

**Check startup progress:**
```bash
docker-compose -f docker-compose.prod.yml logs -f backend

# Wait for these messages:
# ✅ Database is ready!
# ✅ Migrations completed successfully
# ✅ Starting Gunicorn application server
# ✅ Booting worker with pid: XXXX
```

**Once you see workers started, test API:**
```bash
curl http://localhost:8888/health
# Should return: {"status":"healthy"}
```

---

### Cause 3: Database Not Ready 🗄️

Backend can't start if database is not available.

**Check database:**
```bash
docker-compose -f docker-compose.prod.yml ps db

# Should show: Up (healthy)
```

**If database unhealthy or stopped:**
```bash
# Check DB logs
docker-compose -f docker-compose.prod.yml logs db --tail=50

# Restart database
docker-compose -f docker-compose.prod.yml restart db

# Wait for it to be healthy, then restart backend
sleep 10
docker-compose -f docker-compose.prod.yml restart backend
```

---

### Cause 4: Wrong Environment Variables 🔧

**Check CORS_ORIGINS:**
```bash
docker exec it_budget_backend_prod python -c "from app.core.config import settings; print('CORS:', settings.CORS_ORIGINS)"

# Should include: ['https://budget-west.shknv.ru']
```

**If CORS wrong or error:**
```bash
# Update environment variable in Coolify or .env file
# Then restart:
docker-compose -f docker-compose.prod.yml restart backend
```

---

### Cause 5: Port Conflict 🔌

**Check if port 8000 is bound inside container:**
```bash
docker exec it_budget_backend_prod netstat -tlnp | grep 8000
# Should show: 0.0.0.0:8000 ... LISTEN
```

**Check external port mapping:**
```bash
docker port it_budget_backend_prod
# Should show: 8000/tcp -> 0.0.0.0:8888
```

---

### Cause 6: Traefik Not Configured or Not Running 🚦

**Check if Traefik is running:**
```bash
docker ps | grep traefik
```

**Check Traefik logs:**
```bash
docker logs traefik --tail=50 2>&1 | grep -i error
```

**Verify Traefik labels are applied:**
```bash
docker inspect it_budget_backend_prod | grep traefik
```

**If Traefik not routing correctly:**
- Check that `BACKEND_DOMAIN` is set: `api.budget-west.shknv.ru`
- Verify DNS points to server: `nslookup api.budget-west.shknv.ru`
- Restart Traefik: `docker restart traefik`

---

## 🧪 Manual Testing Sequence

Once backend is running, test in this order:

### 1. Test Inside Container (Should Always Work)
```bash
docker exec it_budget_backend_prod curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### 2. Test From Host Machine
```bash
curl http://localhost:8888/health
# Expected: {"status":"healthy"}
```

### 3. Test Through Traefik (External)
```bash
curl https://api.budget-west.shknv.ru/health
# Expected: {"status":"healthy"}
```

### 4. Test OPTIONS Request (CORS Preflight)
```bash
curl -X OPTIONS https://api.budget-west.shknv.ru/api/v1/auth/login \
  -H "Origin: https://budget-west.shknv.ru" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected:
# HTTP/2 200
# access-control-allow-origin: https://budget-west.shknv.ru
# access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
```

**If any of these fail, that's where the problem is!**

---

## 🔄 Complete Restart Procedure

If nothing works, try complete restart:

```bash
# Stop everything
docker-compose -f docker-compose.prod.yml down

# Pull latest changes
git pull origin main  # or your branch name

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build

# Watch logs
docker-compose -f docker-compose.prod.yml logs -f

# Wait for:
# - Database: "database system is ready to accept connections"
# - Backend: "Booting worker with pid: XXXX"
# - Frontend: "Starting Nginx web server"

# Give it 2 minutes, then test
sleep 120
curl https://api.budget-west.shknv.ru/health
```

---

## 📋 Environment Variables Checklist

Make sure these are set (in Coolify or `.env` file):

```bash
# Domains (without https://)
FRONTEND_DOMAIN=budget-west.shknv.ru
BACKEND_DOMAIN=api.budget-west.shknv.ru

# API URL (with https://, without /api/v1)
VITE_API_URL=https://api.budget-west.shknv.ru

# CORS - MUST include frontend domain with https://
CORS_ORIGINS=["https://budget-west.shknv.ru"]

# Security (generate random 32+ chars)
SECRET_KEY=your-long-random-secret-key-here

# Database
DB_USER=budget_user
DB_PASSWORD=your-secure-password
DB_NAME=it_budget_db
```

---

## 🆘 Still Not Working?

Collect diagnostic information and send:

```bash
# Run full diagnostics
./scripts/diagnose-503.sh > diagnostic-output.txt 2>&1

# Collect logs
docker-compose -f docker-compose.prod.yml logs > all-logs.txt

# Check container status
docker-compose -f docker-compose.prod.yml ps > container-status.txt

# Compress and download
tar -czf diagnostic-data.tar.gz diagnostic-output.txt all-logs.txt container-status.txt
```

**Send me:**
1. `diagnostic-data.tar.gz`
2. Screenshot of error from browser console
3. Your environment variables (REMOVE passwords!)

---

## 💡 Prevention Tips

1. **Always wait 1-2 minutes** after starting containers before testing
2. **Check logs** after any restart: `docker-compose logs -f`
3. **Test internally first** (inside container) before testing externally
4. **Use diagnostic script** regularly to catch issues early
5. **Monitor health checks**: `docker-compose ps` should show all `(healthy)`

---

## 📚 Related Documentation

- [TROUBLESHOOTING_LOGIN.md](./TROUBLESHOOTING_LOGIN.md) - General login issues
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Full deployment guide
- `scripts/diagnose-503.sh` - Automated diagnostics
- `scripts/diagnose-production.sh` - Full production diagnostics
