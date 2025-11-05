# External API - Integration Guide

## Overview

IT Budget Manager provides a token-based External API for integration with external systems. This API allows authorized applications to upload and download data programmatically.

## Features

✅ **Token-based authentication** - Secure API tokens with granular permissions
✅ **Department isolation** - Tokens can be scoped to specific departments
✅ **Multiple data formats** - JSON and CSV export support
✅ **Bulk operations** - Import/export large datasets efficiently
✅ **Usage tracking** - Monitor token usage and last access time
✅ **Expiration support** - Set token expiration dates for security

## Authentication

### API Token Structure

```
itb_<64_hex_characters>
```

Example: `itb_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

### Token Scopes

- **READ** - Read-only access to data
- **WRITE** - Create and update operations
- **DELETE** - Delete operations
- **ADMIN** - Full access (includes all scopes)

### Authentication Header

```bash
Authorization: Bearer itb_<your_token_here>
```

## Managing API Tokens

### Create API Token (Admin Only)

**Endpoint:** `POST /api/v1/api-tokens`

**Authentication:** JWT (Admin role required)

**Request Body:**
```json
{
  "name": "External Integration System",
  "description": "Token for ERP integration",
  "scopes": ["READ", "WRITE"],
  "department_id": 1,  // null for system-wide token
  "expires_at": "2026-12-31T23:59:59"  // null for no expiration
}
```

**Response:**
```json
{
  "id": 1,
  "name": "External Integration System",
  "token_key": "itb_a1b2c3d4e5f6...",  // ⚠️ SAVE THIS - shown only once!
  "scopes": ["READ", "WRITE"],
  "status": "ACTIVE",
  "department_id": 1,
  "created_at": "2025-11-04T21:13:00",
  "expires_at": "2026-12-31T23:59:59",
  "request_count": 0
}
```

⚠️ **Important:** The `token_key` is returned only during creation. Save it securely!

### List API Tokens

**Endpoint:** `GET /api/v1/api-tokens`

**Authentication:** JWT (Admin role required)

**Query Parameters:**
- `skip` (optional) - Pagination offset
- `limit` (optional) - Max results (default: 100)
- `status_filter` (optional) - Filter by status: ACTIVE, REVOKED, EXPIRED
- `department_id` (optional) - Filter by department

### Revoke API Token

**Endpoint:** `POST /api/v1/api-tokens/{token_id}/revoke`

**Authentication:** JWT (Admin role required)

**Request Body (optional):**
```json
{
  "reason": "Security breach - rotating keys"
}
```

## External API Endpoints

Base URL: `/api/v1/external`

### Health Check

**Endpoint:** `GET /api/v1/external/health`

**Authentication:** None (public endpoint)

```bash
curl -X GET "http://localhost:8000/api/v1/external/health"
```

### Export Data

#### Export Expenses

**Endpoint:** `GET /api/v1/external/export/expenses`

**Authentication:** API Token (READ scope required)

**Query Parameters:**
- `year` (optional) - Filter by year
- `month` (optional) - Filter by month
- `format` (optional) - Output format: `json` (default) or `csv`

**Example (JSON):**
```bash
curl -X GET \
  "http://localhost:8000/api/v1/external/export/expenses?year=2025&format=json" \
  -H "Authorization: Bearer itb_your_token_here"
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "amount": 10000.00,
      "category_id": 1,
      "contractor_id": 1,
      "description": "Server purchase",
      "request_date": "2025-01-15",
      "status": "PAID",
      "department_id": 1
    }
  ],
  "count": 1
}
```

**Example (CSV):**
```bash
curl -X GET \
  "http://localhost:8000/api/v1/external/export/expenses?year=2025&format=csv" \
  -H "Authorization: Bearer itb_your_token_here" \
  -o expenses_2025.csv
```

#### Export Revenue Actuals

**Endpoint:** `GET /api/v1/external/export/revenue-actuals`

**Parameters:** Same as expenses

#### Export Budget Plans

**Endpoint:** `GET /api/v1/external/export/budget-plans`

**Parameters:** `year`, `format`

#### Export Employees

**Endpoint:** `GET /api/v1/external/export/employees`

**Parameters:** `format`

### Import Data

#### Import Revenue Actuals

**Endpoint:** `POST /api/v1/external/import/revenue-actuals`

**Authentication:** API Token (WRITE scope required)

**Request Body:**
```json
{
  "data": [
    {
      "year": 2025,
      "month": 1,
      "revenue_stream_id": 1,
      "revenue_category_id": 1,
      "actual_amount": 100000.00,
      "planned_amount": 95000.00
    },
    {
      "year": 2025,
      "month": 2,
      "revenue_stream_id": 1,
      "revenue_category_id": 1,
      "actual_amount": 105000.00,
      "planned_amount": 95000.00
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "created_count": 2,
  "error_count": 0,
  "errors": []
}
```

**Example:**
```bash
curl -X POST \
  "http://localhost:8000/api/v1/external/import/revenue-actuals" \
  -H "Authorization: Bearer itb_your_token_here" \
  -H "Content-Type: application/json" \
  -d @revenue_data.json
```

#### Import Expenses

**Endpoint:** `POST /api/v1/external/import/expenses`

**Authentication:** API Token (WRITE scope required)

**Request Body:**
```json
{
  "data": [
    {
      "amount": 10000.00,
      "category_id": 1,
      "contractor_id": 1,
      "organization_id": 1,
      "description": "Equipment purchase",
      "request_date": "2025-01-15",
      "status": "DRAFT"
    }
  ]
}
```

### Reference Data

#### Get Categories

**Endpoint:** `GET /api/v1/external/reference/categories`

**Authentication:** API Token (READ scope)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Оборудование",
      "category_type": "CAPEX",
      "department_id": 1
    }
  ]
}
```

#### Get Contractors

**Endpoint:** `GET /api/v1/external/reference/contractors`

#### Get Revenue Streams

**Endpoint:** `GET /api/v1/external/reference/revenue-streams`

## Error Handling

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Token lacks required scope
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "detail": "Token requires WRITE scope"
}
```

## Security Best Practices

1. **Store tokens securely** - Never commit tokens to version control
2. **Use environment variables** - Store tokens in env vars or secrets manager
3. **Rotate tokens regularly** - Create new tokens and revoke old ones periodically
4. **Use minimal scopes** - Grant only required permissions
5. **Set expiration dates** - Use token expiration for temporary access
6. **Monitor usage** - Check `request_count` and `last_used_at` regularly
7. **Department isolation** - Use department-scoped tokens when possible

## Example Integration Scripts

### Python Example

```python
import requests
import os

# Load token from environment
API_TOKEN = os.getenv("IT_BUDGET_API_TOKEN")
BASE_URL = "http://localhost:8000/api/v1/external"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Export expenses
response = requests.get(
    f"{BASE_URL}/export/expenses",
    params={"year": 2025, "format": "json"},
    headers=headers
)
expenses = response.json()
print(f"Exported {expenses['count']} expenses")

# Import revenue actuals
data = {
    "data": [
        {
            "year": 2025,
            "month": 1,
            "revenue_stream_id": 1,
            "revenue_category_id": 1,
            "actual_amount": 100000.00,
            "planned_amount": 95000.00
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/import/revenue-actuals",
    json=data,
    headers=headers
)
result = response.json()
print(f"Imported {result['created_count']} records")
```

### curl Example

```bash
#!/bin/bash

# Load token from environment
API_TOKEN="${IT_BUDGET_API_TOKEN}"
BASE_URL="http://localhost:8000/api/v1/external"

# Export expenses to CSV
curl -X GET \
  "${BASE_URL}/export/expenses?year=2025&format=csv" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -o expenses_$(date +%Y%m%d).csv

# Import revenue actuals from JSON file
curl -X POST \
  "${BASE_URL}/import/revenue-actuals" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @revenue_data.json
```

### Node.js Example

```javascript
const axios = require('axios');

const API_TOKEN = process.env.IT_BUDGET_API_TOKEN;
const BASE_URL = 'http://localhost:8000/api/v1/external';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_TOKEN}`,
    'Content-Type': 'application/json'
  }
});

// Export expenses
async function exportExpenses() {
  const response = await client.get('/export/expenses', {
    params: { year: 2025, format: 'json' }
  });
  console.log(`Exported ${response.data.count} expenses`);
  return response.data;
}

// Import revenue actuals
async function importRevenueActuals(data) {
  const response = await client.post('/import/revenue-actuals', { data });
  console.log(`Imported ${response.data.created_count} records`);
  return response.data;
}
```

## Rate Limiting

- **500 requests per minute** per IP address
- **5000 requests per hour** per IP address

Exceed these limits and you'll receive a `429 Too Many Requests` response.

## Support

For issues or questions about the External API:
- Check API documentation: `/docs`
- Review application logs for detailed error messages
- Contact your system administrator

## Changelog

### v1.0.0 (2025-11-04)
- Initial release
- Token-based authentication
- Export: expenses, revenue actuals, budget plans, employees
- Import: expenses, revenue actuals
- Reference data endpoints
- CSV and JSON format support
