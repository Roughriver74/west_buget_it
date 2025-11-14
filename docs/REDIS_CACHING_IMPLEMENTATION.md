# Redis Caching Implementation

## Overview

Redis caching has been successfully integrated into the credit portfolio analytics endpoints to improve performance and reduce database load.

## Implementation Details

### 1. Cache Service
- **Location**: `backend/app/services/cache.py`
- **Features**:
  - Redis support with in-memory fallback
  - Namespace-based cache organization
  - Configurable TTL (Time-To-Live)
  - JSON serialization for complex objects
  - Thread-safe in-memory cache fallback

### 2. Cached Endpoints

The following analytics endpoints now use Redis caching with 5-minute TTL:

1. **`GET /api/v1/credit-portfolio/summary`**
   - Overall portfolio statistics
   - Cache key: `summary|{department_id}|{date_from}|{date_to}`

2. **`GET /api/v1/credit-portfolio/monthly-stats`**
   - Monthly receipts vs expenses statistics
   - Cache key: `monthly_stats|{department_id}|{date_from}|{date_to}`

3. **`GET /api/v1/credit-portfolio/analytics/monthly-efficiency`**
   - Monthly payment efficiency (principal vs interest)
   - Cache key: `monthly_efficiency|{department_id}|{date_from}|{date_to}|{organization_id}|{bank_account_id}`

### 3. Cache Invalidation

Cache is automatically invalidated when:
- **FTP Import**: After successful import of credit portfolio data
- **Namespace**: All cached entries under `credit_portfolio` namespace are cleared

### 4. Configuration

**Environment Variables** (`.env`):
```bash
USE_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_TTL_SECONDS=300  # 5 minutes
```

**Docker Compose**:
- Redis 7 Alpine container added
- Persistent storage with `redis_data` volume
- Health checks enabled
- Backend depends on Redis

### 5. Performance Benefits

- **Reduced DB Load**: Analytics queries are cached for 5 minutes
- **Faster Response**: Cached responses are served instantly
- **Scalability**: Redis can be scaled independently
- **Fallback**: In-memory cache used when Redis unavailable

### 6. Code Changes

**File**: `backend/app/api/v1/credit_portfolio.py`

```python
# Import cache service
from app.services.cache import cache_service

# Cache namespace
CACHE_NAMESPACE = "credit_portfolio"

# Invalidation function
def invalidate_analytics_cache():
    """Invalidate all analytics cache when data changes"""
    cache_service.invalidate_namespace(CACHE_NAMESPACE)

# Example usage in endpoint
cache_key = cache_service.build_key("summary", department_id, date_from, date_to)
cached_result = cache_service.get(CACHE_NAMESPACE, cache_key)
if cached_result is not None:
    return cached_result

# ... compute result ...

cache_service.set(CACHE_NAMESPACE, cache_key, result.model_dump())
return result
```

## Usage

### Starting Redis

**With Docker Compose**:
```bash
docker-compose up -d redis
```

**Standalone**:
```bash
redis-server
```

### Monitoring Cache

```bash
# Connect to Redis CLI
docker exec -it it_budget_redis redis-cli

# View all credit portfolio cache keys
KEYS itbudget:cache:credit_portfolio:*

# Check specific key
GET "itbudget:cache:credit_portfolio:summary|8|None|None"

# Clear all cache
FLUSHDB

# Monitor cache operations
MONITOR
```

### Testing

1. **First Request** (cache miss):
   ```bash
   curl "http://localhost:8000/api/v1/credit-portfolio/summary?department_id=8" \
     -H "Authorization: Bearer $TOKEN"
   # Response time: ~500ms (database query)
   ```

2. **Second Request** (cache hit):
   ```bash
   curl "http://localhost:8000/api/v1/credit-portfolio/summary?department_id=8" \
     -H "Authorization: Bearer $TOKEN"
   # Response time: ~5ms (from cache)
   ```

3. **After Import** (cache invalidated):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/credit-portfolio/import/trigger" \
     -H "Authorization: Bearer $TOKEN"
   # Cache cleared, next request will be cache miss
   ```

## Next Steps

Future enhancements can include:

1. **More Cached Endpoints**:
   - `/analytics/org-efficiency`
   - `/analytics/cashflow-monthly`
   - `/analytics/yearly-comparison`
   - `/contract-stats`
   - `/organization-stats`

2. **Smart Invalidation**:
   - Invalidate only specific date ranges
   - Invalidate only specific departments
   - Invalidate only specific organizations

3. **Cache Warming**:
   - Pre-populate cache after import
   - Background refresh for popular queries

4. **Monitoring**:
   - Cache hit/miss ratio tracking
   - Prometheus metrics for cache performance
   - Alerts for Redis connection issues

## Troubleshooting

### Redis Not Available
- **Symptom**: Backend logs show "Falling back to in-memory cache"
- **Solution**: Verify Redis is running and accessible
  ```bash
  docker ps | grep redis
  docker logs it_budget_redis
  ```

### Cache Not Invalidating
- **Symptom**: Old data showing after import
- **Solution**: Check logs for invalidation calls
  ```bash
  docker logs it_budget_backend | grep "Invalidated analytics cache"
  ```

### Memory Issues
- **Symptom**: Redis consuming too much memory
- **Solution**: Configure maxmemory in Redis
  ```bash
  docker exec -it it_budget_redis redis-cli CONFIG SET maxmemory 256mb
  docker exec -it it_budget_redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
  ```

## Summary

Redis caching has been successfully implemented for credit portfolio analytics endpoints, providing:
- ✅ 5-minute TTL for all analytics queries
- ✅ Automatic cache invalidation on data import
- ✅ In-memory fallback when Redis unavailable
- ✅ Docker Compose integration
- ✅ Production-ready configuration

Expected performance improvement: **90-95% reduction** in response time for cached analytics queries.
