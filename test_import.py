#!/usr/bin/env python3
"""Test employee import to see validation errors"""

import requests
import json

# Login
from urllib.parse import urlencode
login_data_form = urlencode({"username": "admin", "password": "admin"})
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data=login_data_form,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
print(f"Login status: {login_response.status_code}")
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

login_json = login_response.json()
print(f"Login successful!")
token = login_json["access_token"]

# Import
column_mapping = {
    "ФИО": "full_name",
    "Должность": "position",
    "Базовый оклад": "base_salary",
    "Месячная премия": "monthly_bonus_base",
    "Квартальная премия": "quarterly_bonus_base",
    "Годовая премия": "annual_bonus_base",
    "Дата приема": "hire_date",
    "Табельный номер": "employee_number"
}

files = {"file": open("xls/Пример_Импорт_Сотрудников.xlsx", "rb")}
data = {
    "entity_type": "employees",
    "column_mapping": json.dumps(column_mapping)
}
headers = {"Authorization": f"Bearer {token}"}

response = requests.post(
    "http://localhost:8000/api/v1/import/execute",
    files=files,
    data=data,
    headers=headers
)

print(f"Status code: {response.status_code}")
print(f"\nResponse:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
