# Quick Fix for 503 CORS Error

## Problem
- 503 error on login
- CORS preflight failures
- API not accessible from frontend

## Solution

### Step 1: Connect to Server
```bash
ssh root@93.189.228.52
cd /root/budget-app  # or your app directory
```

### Step 2: Update docker-compose.prod.yml

Edit the file and update the backend CORS labels (around line 105):

```bash
nano docker-compose.prod.yml
```

Find this section under backend -> labels:
```yaml
- "traefik.http.middlewares.backend-cors.headers.accesscontrolalloworiginlist=https://budget-west.shknv.ru"
```

Replace with:
```yaml
- "traefik.http.middlewares.backend-cors.headers.accesscontrolalloworiginlist=https://budget-west.shknv.ru,https://api.budget-west.shknv.ru"
```

Also find (around line 72):
```yaml
CORS_ORIGINS: ${CORS_ORIGINS:-'["https://yourdomain.com"]'}
```

Replace with:
```yaml
CORS_ORIGINS: ${CORS_ORIGINS:-'["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]'}
```

Save file (Ctrl+O, Enter, Ctrl+X)

### Step 3: Update .env File

```bash
nano .env
```

Find the line with `CORS_ORIGINS` and update it to:
```bash
CORS_ORIGINS='["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]'
```

If the line doesn't exist, add it.

Save file (Ctrl+O, Enter, Ctrl+X)

### Step 4: Rebuild and Restart

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start (about 40 seconds)
sleep 40

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 5: Verify

```bash
# Check backend health
docker exec it_budget_backend_prod curl http://localhost:8000/health

# Should return: {"status":"healthy"}

# Check logs for any errors
docker logs --tail 50 it_budget_backend_prod
```

### Step 6: Test in Browser

1. Open https://budget-west.shknv.ru
2. Try to login
3. Check browser console (F12) - should see no CORS errors
4. Login should work

## If Still Not Working

### Check Traefik Logs
```bash
# List all containers to find Traefik
docker ps | grep traefik

# View Traefik logs
docker logs <traefik-container-id>
```

### Check Backend Logs in Detail
```bash
docker logs -f it_budget_backend_prod
```

### Verify Environment Variables
```bash
docker exec it_budget_backend_prod env | grep CORS
```

Should show:
```
CORS_ORIGINS=["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]
```

## Alternative: Copy Updated Files from Local

If you have the updated files locally:

```bash
# From your local machine
scp docker-compose.prod.yml root@93.189.228.52:/root/budget-app/

# Then on server
ssh root@93.189.228.52
cd /root/budget-app
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Summary of Changes

**What was fixed:**
1. ✅ Added both domains to Traefik CORS headers
2. ✅ Added both domains to backend CORS_ORIGINS
3. ✅ Added Traefik health check configuration
4. ✅ Updated default CORS origins in docker-compose

**Why it failed:**
- Traefik CORS middleware only allowed `https://budget-west.shknv.ru`
- Backend API is at `https://api.budget-west.shknv.ru`
- Browser preflight OPTIONS requests were blocked
- 503 error because Traefik couldn't route to backend

**After fix:**
- Both domains allowed in CORS
- Preflight requests pass
- Login works
- API accessible
