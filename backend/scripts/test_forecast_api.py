"""Test forecast API endpoints"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("=== Testing Forecast API ===\n")
print("1. Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin", "password": "admin123"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✓ Logged in successfully\n")

# Test GET forecasts endpoint WITHOUT department_id
print("2. Testing GET /forecast/ WITHOUT department_id parameter...")
response = requests.get(
    f"{BASE_URL}/forecast/",
    headers=headers,
    params={"year": 2025, "month": 11}
)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}\n")
else:
    data = response.json()
    print(f"Success! Returned {len(data)} forecasts\n")

# Test GET forecasts endpoint WITH department_id
print("3. Testing GET /forecast/ WITH department_id=2...")
response = requests.get(
    f"{BASE_URL}/forecast/",
    headers=headers,
    params={"year": 2025, "month": 11, "department_id": 2}
)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}\n")
else:
    data = response.json()
    print(f"Success! Returned {len(data)} forecasts")
    if len(data) > 0:
        print(f"First forecast: ID={data[0]['id']}, Department={data[0].get('department_id', 'MISSING')}, Amount={data[0]['amount']}\n")

# Test GET forecasts endpoint WITH department_id=1 (should return different data)
print("4. Testing GET /forecast/ WITH department_id=1...")
response = requests.get(
    f"{BASE_URL}/forecast/",
    headers=headers,
    params={"year": 2025, "month": 11, "department_id": 1}
)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}\n")
else:
    data = response.json()
    print(f"Success! Returned {len(data)} forecasts (should be 0 or different from dept 2)\n")

print("=== Test Complete ===")
