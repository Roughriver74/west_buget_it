# Детальный план реализации системы упаковки и лицензирования

## 1. Архитектура системы

### 1.1 Компоненты
```
┌─────────────────────────────────────────┐
│   Портал лицензирования (облако)        │
│   - API для проверки лицензий           │
│   - База данных клиентов                │
│   - Генератор ключей                    │
└─────────────────────────────────────────┘
              ↓ API запросы
┌─────────────────────────────────────────┐
│   Сервер клиента                        │
│   ├── Installer (веб-интерфейс)         │
│   ├── Core Application (защищенный)     │
│   ├── License Module                    │
│   └── Docker контейнеры                 │
└─────────────────────────────────────────┘
```

## 2. Портал лицензирования

### 2.1 Технологии
- **Backend**: FastAPI (Python) / Node.js
- **База данных**: PostgreSQL
- **API**: REST API с JWT авторизацией
- **Хостинг**: VPS/облако (отдельный сервер)

### 2.2 Структура БД

```sql
-- Таблица клиентов
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    company_name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP,
    status VARCHAR(50) -- active/suspended/expired
);

-- Таблица лицензий
CREATE TABLE licenses (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    license_key VARCHAR(255) UNIQUE,
    license_type VARCHAR(50), -- base/module
    module_name VARCHAR(100), -- NULL для базовой
    issued_at TIMESTAMP,
    expires_at TIMESTAMP,
    activations_count INT DEFAULT 0,
    max_activations INT DEFAULT 1,
    status VARCHAR(50) -- active/suspended/expired
);

-- Таблица активаций
CREATE TABLE activations (
    id UUID PRIMARY KEY,
    license_id UUID REFERENCES licenses(id),
    server_fingerprint VARCHAR(255), -- уникальный ID сервера
    activated_at TIMESTAMP,
    last_check TIMESTAMP,
    ip_address VARCHAR(45),
    status VARCHAR(50) -- active/revoked
);

-- Таблица модулей
CREATE TABLE modules (
    id UUID PRIMARY KEY,
    module_code VARCHAR(50) UNIQUE,
    module_name VARCHAR(255),
    description TEXT,
    price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true
);
```

### 2.3 API эндпоинты

```python
# Проверка базовой лицензии
POST /api/v1/license/validate
{
    "license_key": "BASE-XXXX-XXXX-XXXX",
    "server_fingerprint": "hash_сервера"
}

# Активация лицензии
POST /api/v1/license/activate
{
    "license_key": "BASE-XXXX-XXXX-XXXX",
    "server_fingerprint": "hash_сервера",
    "server_info": {
        "hostname": "...",
        "ip": "..."
    }
}

# Проверка модуля
POST /api/v1/module/validate
{
    "license_key": "MOD-XXXX-XXXX-XXXX",
    "module_code": "analytics",
    "server_fingerprint": "hash_сервера"
}

# Heartbeat (периодическая проверка)
POST /api/v1/license/heartbeat
{
    "server_fingerprint": "hash_сервера",
    "timestamp": "2025-11-21T10:00:00Z"
}
```

### 2.4 Генерация лицензионных ключей

```python
import hashlib
import secrets
from datetime import datetime, timedelta

class LicenseGenerator:
    def __init__(self, secret_key):
        self.secret_key = secret_key
    
    def generate_license_key(self, client_id, license_type, module_code=None):
        """
        Формат: TYPE-XXXX-XXXX-XXXX-CHECKSUM
        TYPE: BASE (базовая) или MOD (модуль)
        """
        # Генерируем случайные сегменты
        segment1 = secrets.token_hex(2).upper()
        segment2 = secrets.token_hex(2).upper()
        segment3 = secrets.token_hex(2).upper()
        
        # Создаем данные для подписи
        data = f"{client_id}-{license_type}-{module_code}-{segment1}{segment2}{segment3}"
        
        # Генерируем контрольную сумму
        checksum = hashlib.sha256(
            f"{data}-{self.secret_key}".encode()
        ).hexdigest()[:4].upper()
        
        prefix = "BASE" if license_type == "base" else "MOD"
        
        return f"{prefix}-{segment1}-{segment2}-{segment3}-{checksum}"
    
    def validate_license_key(self, license_key, client_id, license_type, module_code=None):
        """Проверка валидности ключа"""
        parts = license_key.split('-')
        if len(parts) != 5:
            return False
        
        prefix, seg1, seg2, seg3, checksum = parts
        
        # Пересчитываем контрольную сумму
        data = f"{client_id}-{license_type}-{module_code}-{seg1}{seg2}{seg3}"
        expected_checksum = hashlib.sha256(
            f"{data}-{self.secret_key}".encode()
        ).hexdigest()[:4].upper()
        
        return checksum == expected_checksum
```

### 2.5 Админ-панель портала

```
Функции:
- Управление клиентами
- Генерация лицензий
- Просмотр активаций
- Управление модулями
- Статистика и аналитика
- Блокировка/разблокировка лицензий
```

## 3. Installer (Установщик)

### 3.1 Технологии
- **Frontend**: React/Next.js
- **Backend**: FastAPI (Python)
- **Контейнеризация**: Docker + Docker Compose

### 3.2 Структура проекта

```
project-installer/
├── docker-compose.yml
├── install.sh                    # Скрипт запуска установки
├── installer/                    # Веб-установщик
│   ├── frontend/                # React приложение
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── Step1_Welcome.jsx
│   │   │   │   ├── Step2_License.jsx
│   │   │   │   ├── Step3_Database.jsx
│   │   │   │   ├── Step4_Admin.jsx
│   │   │   │   ├── Step5_Modules.jsx
│   │   │   │   └── Step6_Complete.jsx
│   │   │   ├── App.jsx
│   │   │   └── api.js
│   │   └── Dockerfile
│   └── backend/                 # API установщика
│       ├── main.py
│       ├── installer.py
│       ├── license_checker.py
│       └── requirements.txt
├── app/                          # Основное приложение
│   ├── src/                     # Исходный код (защищенный)
│   ├── modules/                 # Модули
│   └── Dockerfile
└── config/
    └── nginx.conf
```

### 3.3 Скрипт установки (install.sh)

```bash
#!/bin/bash

echo "=================================="
echo "  Установщик IT Budget Manager"
echo "=================================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Генерация server fingerprint
SERVER_FINGERPRINT=$(cat /etc/machine-id /sys/class/dmi/id/product_uuid 2>/dev/null | md5sum | cut -d' ' -f1)
export SERVER_FINGERPRINT

echo "Server Fingerprint: $SERVER_FINGERPRINT"
echo ""

# Запуск установщика
echo "Запуск установщика..."
docker-compose -f docker-compose.installer.yml up -d

# Получение IP
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=================================="
echo "Установщик запущен!"
echo "Откройте в браузере: http://$IP:8080"
echo "=================================="
```

### 3.4 Docker Compose для установщика

```yaml
# docker-compose.installer.yml
version: '3.8'

services:
  installer-frontend:
    build: ./installer/frontend
    ports:
      - "8080:80"
    depends_on:
      - installer-backend
    environment:
      - API_URL=http://localhost:8081

  installer-backend:
    build: ./installer/backend
    ports:
      - "8081:8000"
    volumes:
      - ./config:/config
      - ./app:/app
      - /var/run/docker.sock:/var/run/docker.sock  # Для управления Docker
    environment:
      - SERVER_FINGERPRINT=${SERVER_FINGERPRINT}
      - LICENSE_API_URL=https://license.yourdomain.com/api/v1
```

### 3.5 Backend установщика (installer/backend/main.py)

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import subprocess
import yaml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LICENSE_API_URL = os.getenv("LICENSE_API_URL")
SERVER_FINGERPRINT = os.getenv("SERVER_FINGERPRINT")

class LicenseValidation(BaseModel):
    license_key: str

class DatabaseConfig(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str

class AdminConfig(BaseModel):
    admin_email: str
    admin_password: str
    company_name: str

class ModuleActivation(BaseModel):
    module_code: str
    license_key: str

# Шаг 2: Проверка базовой лицензии
@app.post("/api/validate-license")
async def validate_license(data: LicenseValidation):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LICENSE_API_URL}/license/activate",
                json={
                    "license_key": data.license_key,
                    "server_fingerprint": SERVER_FINGERPRINT
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # Сохраняем лицензию в конфиг
                save_license_config(data.license_key, result)
                return {"status": "success", "data": result}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Лицензия недействительна или уже активирована"
                )
        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="Не удалось связаться с сервером лицензий"
            )

# Шаг 3: Настройка БД
@app.post("/api/configure-database")
async def configure_database(config: DatabaseConfig):
    # Проверка подключения к БД
    try:
        # Тестовое подключение
        import psycopg2
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password
        )
        conn.close()
        
        # Сохранение конфига
        save_db_config(config)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Шаг 4: Создание администратора
@app.post("/api/create-admin")
async def create_admin(config: AdminConfig):
    save_admin_config(config)
    return {"status": "success"}

# Шаг 5: Активация модулей
@app.post("/api/activate-module")
async def activate_module(data: ModuleActivation):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LICENSE_API_URL}/module/validate",
                json={
                    "license_key": data.license_key,
                    "module_code": data.module_code,
                    "server_fingerprint": SERVER_FINGERPRINT
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                save_module_license(data.module_code, data.license_key)
                return {"status": "success", "data": result}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Лицензия модуля недействительна"
                )
        except httpx.RequestError:
            raise HTTPException(
                status_code=500,
                detail="Не удалось связаться с сервером лицензий"
            )

@app.get("/api/available-modules")
async def get_available_modules():
    """Получить список доступных модулей"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{LICENSE_API_URL}/modules/list",
                timeout=10.0
            )
            return response.json()
        except:
            # Возвращаем дефолтный список
            return [
                {"code": "analytics", "name": "Аналитика и отчеты", "price": 50000},
                {"code": "forecasting", "name": "Прогнозирование бюджета", "price": 75000},
                {"code": "integration_1c", "name": "Интеграция с 1С", "price": 100000},
                {"code": "api_access", "name": "API доступ", "price": 30000}
            ]

# Шаг 6: Финальная установка
@app.post("/api/install")
async def install_application():
    """Запуск основного приложения"""
    try:
        # Генерируем финальный docker-compose.yml
        generate_production_compose()
        
        # Останавливаем установщик
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.installer.yml", "down"],
            check=True
        )
        
        # Запускаем продакшн
        subprocess.run(
            ["docker-compose", "-f", "docker-compose.yml", "up", "-d"],
            check=True
        )
        
        return {
            "status": "success",
            "message": "Установка завершена!",
            "url": f"http://{get_server_ip()}:80"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_license_config(license_key, license_data):
    """Сохранение конфигурации лицензии"""
    config = {
        "license_key": license_key,
        "server_fingerprint": SERVER_FINGERPRINT,
        "activated_at": license_data.get("activated_at"),
        "expires_at": license_data.get("expires_at")
    }
    with open("/config/license.yml", "w") as f:
        yaml.dump(config, f)

def save_db_config(config: DatabaseConfig):
    """Сохранение конфигурации БД"""
    db_config = {
        "host": config.host,
        "port": config.port,
        "database": config.database,
        "username": config.username,
        "password": config.password
    }
    with open("/config/database.yml", "w") as f:
        yaml.dump(db_config, f)

def save_admin_config(config: AdminConfig):
    """Сохранение конфигурации администратора"""
    admin_config = {
        "email": config.admin_email,
        "password": config.admin_password,  # В реальности - хэш
        "company_name": config.company_name
    }
    with open("/config/admin.yml", "w") as f:
        yaml.dump(admin_config, f)

def save_module_license(module_code, license_key):
    """Сохранение лицензии модуля"""
    try:
        with open("/config/modules.yml", "r") as f:
            modules = yaml.safe_load(f) or {}
    except:
        modules = {}
    
    modules[module_code] = {
        "license_key": license_key,
        "enabled": True
    }
    
    with open("/config/modules.yml", "w") as f:
        yaml.dump(modules, f)

def generate_production_compose():
    """Генерация production docker-compose.yml"""
    # Читаем конфиги
    with open("/config/database.yml", "r") as f:
        db_config = yaml.safe_load(f)
    
    compose = {
        "version": "3.8",
        "services": {
            "app": {
                "build": "./app",
                "ports": ["80:8000"],
                "environment": [
                    f"DB_HOST={db_config['host']}",
                    f"DB_PORT={db_config['port']}",
                    f"DB_NAME={db_config['database']}",
                    f"DB_USER={db_config['username']}",
                    f"DB_PASSWORD={db_config['password']}",
                    f"SERVER_FINGERPRINT={SERVER_FINGERPRINT}"
                ],
                "volumes": [
                    "./config:/app/config:ro",
                    "./data:/app/data"
                ],
                "restart": "always"
            }
        }
    }
    
    with open("/docker-compose.yml", "w") as f:
        yaml.dump(compose, f)

def get_server_ip():
    """Получить IP сервера"""
    import socket
    return socket.gethostbyname(socket.gethostname())
```

### 3.6 Frontend установщика (пример Step2_License.jsx)

```jsx
import React, { useState } from 'react';
import { validateLicense } from '../api';

export const Step2License = ({ onNext, onError }) => {
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);

  const handleValidate = async () => {
    if (!licenseKey) {
      onError('Введите лицензионный ключ');
      return;
    }

    setLoading(true);
    try {
      const result = await validateLicense(licenseKey);
      
      if (result.status === 'success') {
        onNext({
          licenseKey,
          expiresAt: result.data.expires_at
        });
      }
    } catch (error) {
      onError(error.response?.data?.detail || 'Ошибка проверки лицензии');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-container">
      <h2>Активация лицензии</h2>
      <p>Введите базовый лицензионный ключ для активации системы</p>
      
      <div className="form-group">
        <label>Лицензионный ключ:</label>
        <input
          type="text"
          value={licenseKey}
          onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
          placeholder="BASE-XXXX-XXXX-XXXX-XXXX"
          maxLength={24}
          className="license-input"
        />
      </div>

      <div className="info-box">
        <p>Формат ключа: BASE-XXXX-XXXX-XXXX-XXXX</p>
        <p>Лицензионный ключ можно получить на портале: <a href="https://license.yourdomain.com" target="_blank">license.yourdomain.com</a></p>
      </div>

      <button
        onClick={handleValidate}
        disabled={loading || !licenseKey}
        className="btn-primary"
      >
        {loading ? 'Проверка...' : 'Проверить и продолжить'}
      </button>
    </div>
  );
};
```

## 4. Защита кода приложения

### 4.1 Обфускация Python кода

```python
# Использование PyArmor для защиты кода
pip install pyarmor

# Обфускация всего проекта
pyarmor gen --recursive --output dist/ src/

# С привязкой к лицензии
pyarmor gen --bind-data "license_key:BASE-XXXX" src/
```

### 4.2 Компиляция в binary (альтернатива)

```bash
# Использование PyInstaller
pip install pyinstaller

pyinstaller --onefile \
            --hidden-import=fastapi \
            --hidden-import=uvicorn \
            --add-data "config:config" \
            main.py
```

### 4.3 Docker слои для защиты

```dockerfile
# app/Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем обфусцированный код
COPY dist/ ./src/

# Production image
FROM python:3.11-slim

WORKDIR /app

# Копируем только необходимое из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/src /app/src

# Копируем конфигурацию
COPY config/ /app/config/

# Запрет на запись в директорию с кодом
RUN chmod -R 555 /app/src

# Пользователь без прав root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app/data
USER appuser

CMD ["python", "src/main.py"]
```

### 4.4 License Checker в приложении

```python
# app/src/core/license_checker.py
import httpx
import hashlib
import time
from datetime import datetime
import yaml

class LicenseChecker:
    def __init__(self, config_path="/app/config/license.yml"):
        self.config_path = config_path
        self.license_api_url = "https://license.yourdomain.com/api/v1"
        self.last_check = None
        self.check_interval = 3600  # 1 час
        
    def get_server_fingerprint(self):
        """Получить fingerprint сервера"""
        try:
            with open("/etc/machine-id", "r") as f:
                machine_id = f.read().strip()
            with open("/sys/class/dmi/id/product_uuid", "r") as f:
                product_uuid = f.read().strip()
            
            combined = f"{machine_id}{product_uuid}"
            return hashlib.md5(combined.encode()).hexdigest()
        except:
            # Fallback для Docker
            import socket
            hostname = socket.gethostname()
            return hashlib.md5(hostname.encode()).hexdigest()
    
    def load_license_config(self):
        """Загрузить конфигурацию лицензии"""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except:
            return None
    
    async def verify_license(self):
        """Проверить лицензию"""
        config = self.load_license_config()
        
        if not config:
            raise Exception("Лицензия не найдена. Требуется переустановка.")
        
        # Проверяем не чаще раза в час
        if self.last_check and (time.time() - self.last_check < self.check_interval):
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.license_api_url}/license/heartbeat",
                    json={
                        "server_fingerprint": self.get_server_fingerprint(),
                        "license_key": config["license_key"],
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.last_check = time.time()
                    return True
                else:
                    raise Exception("Лицензия недействительна")
        except httpx.RequestError:
            # Если сервер недоступен, проверяем срок действия локально
            expires_at = datetime.fromisoformat(config["expires_at"])
            if datetime.utcnow() < expires_at:
                return True
            raise Exception("Срок действия лицензии истек")
    
    async def verify_module(self, module_code):
        """Проверить лицензию модуля"""
        try:
            with open("/app/config/modules.yml", "r") as f:
                modules = yaml.safe_load(f) or {}
        except:
            return False
        
        if module_code not in modules or not modules[module_code].get("enabled"):
            return False
        
        # Проверяем лицензию модуля на сервере
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.license_api_url}/module/validate",
                    json={
                        "license_key": modules[module_code]["license_key"],
                        "module_code": module_code,
                        "server_fingerprint": self.get_server_fingerprint()
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except:
            # В случае недоступности сервера разрешаем работу
            return True

# Middleware для проверки лицензии
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class LicenseMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, license_checker):
        super().__init__(app)
        self.license_checker = license_checker
    
    async def dispatch(self, request: Request, call_next):
        # Пропускаем статические файлы и health check
        if request.url.path.startswith("/static") or request.url.path == "/health":
            return await call_next(request)
        
        # Проверяем лицензию
        try:
            await self.license_checker.verify_license()
        except Exception as e:
            raise HTTPException(
                status_code=403,
                detail=f"Ошибка лицензии: {str(e)}"
            )
        
        return await call_next(request)
```

### 4.5 Интеграция в приложение

```python
# app/src/main.py
from fastapi import FastAPI
from core.license_checker import LicenseChecker, LicenseMiddleware

app = FastAPI()

# Инициализация проверки лицензии
license_checker = LicenseChecker()
app.add_middleware(LicenseMiddleware, license_checker=license_checker)

# Декоратор для проверки модулей
def require_module(module_code: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not await license_checker.verify_module(module_code):
                raise HTTPException(
                    status_code=403,
                    detail=f"Модуль '{module_code}' не активирован"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Пример использования
@app.get("/api/analytics/report")
@require_module("analytics")
async def get_analytics_report():
    return {"data": "..."}
```

## 5. Управление обновлениями

### 5.1 Git workflow для обновлений

```bash
# На сервере клиента создается специальный remote
cd /app
git remote add developer git@your-git-server.com:client-123/project.git

# Разработчик пушит обновления
git push developer main

# На сервере клиента - автоматический pull и перезапуск
# через Git hooks или CI/CD
```

### 5.2 Webhook для автообновления

```python
# update_webhook.py на сервере клиента
from fastapi import FastAPI, HTTPException, Header
import hmac
import hashlib
import subprocess

app = FastAPI()

SECRET_KEY = "your-webhook-secret"

@app.post("/webhook/update")
async def handle_update(
    payload: dict,
    x_hub_signature: str = Header(None)
):
    # Проверяем подпись
    if not verify_signature(payload, x_hub_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Выполняем обновление
    try:
        # Pull изменений
        subprocess.run(["git", "pull", "developer", "main"], check=True)
        
        # Пересборка и перезапуск
        subprocess.run(["docker-compose", "build"], check=True)
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def verify_signature(payload, signature):
    """Проверка HMAC подписи"""
    expected = hmac.new(
        SECRET_KEY.encode(),
        str(payload).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 5.3 Защищенный доступ разработчика

```yaml
# docker-compose.yml с SSH доступом для разработчика
services:
  app:
    # ... основной сервис
    
  dev-access:
    image: linuxserver/openssh-server
    environment:
      - PUBLIC_KEY=ssh-rsa AAAA... developer@company.com
      - USER_NAME=developer
    volumes:
      - ./:/workspace:ro  # Read-only доступ
    ports:
      - "2222:2222"
    # Запускается только по требованию
    profiles:
      - dev-access
```

## 6. Production docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: budget-manager-app
    ports:
      - "80:8000"
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - SERVER_FINGERPRINT=${SERVER_FINGERPRINT}
      - LICENSE_API_URL=https://license.yourdomain.com/api/v1
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: budget-manager-nginx
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## 7. Roadmap внедрения

### Этап 1: Портал лицензирования (2-3 недели)
- Разработка API
- База данных
- Админ-панель
- Тестирование

### Этап 2: Установщик (2-3 недели)
- Backend API установщика
- Frontend веб-интерфейс
- Docker конфигурации
- Тестирование на чистом сервере

### Этап 3: Защита кода (1-2 недели)
- Обфускация/компиляция
- License checker middleware
- Тестирование защиты

### Этап 4: Интеграция (1 неделя)
- Подключение к порталу лицензий
- Тестирование полного цикла
- Документация

### Этап 5: Пилот (2 недели)
- Установка на тестовом клиенте
- Сбор обратной связи
- Исправление ошибок

Хочешь, чтобы я детализировал какой-то конкретный компонент еще глубже?r