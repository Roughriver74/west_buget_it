# Техническая спецификация системы лицензирования

## 1. Формат лицензионного ключа

### 1.1 Структура ключа

```
{LICENSE_TYPE}-{ORG_HASH}-{TIMESTAMP}-{MODULE_FLAGS}-{CHECKSUM}

Пример:
ENT-A1B2C3D4-20251120-FFFFFFFFFFFFFF-E5F6G7H8

Расшифровка:
- ENT: Enterprise license
- A1B2C3D4: Hash организации (первые 8 символов SHA-256)
- 20251120: Дата создания (YYYYMMDD)
- FFFFFFFFFFFFFF: 14 hex символов (7 байт = 56 бит) для флагов модулей
- E5F6G7H8: Checksum (первые 8 символов HMAC-SHA256)
```

### 1.2 License Types

```python
class LicenseTypeEnum(str, enum.Enum):
    BASE = "BASE"           # Базовая лицензия
    PROFESSIONAL = "PRO"    # Профессиональная
    ENTERPRISE = "ENT"      # Корпоративная
    TRIAL = "TRL"          # Триальная (30 дней)
    DEVELOPER = "DEV"      # Разработчик
```

### 1.3 Module Flags (bit field)

```
Бит 0: BUDGET_CORE (всегда 1)
Бит 1: AI_FORECAST
Бит 2: CREDIT_PORTFOLIO
Бит 3: REVENUE_BUDGET
Бит 4: PAYROLL_KPI
Бит 5: INTEGRATIONS_1C
Бит 6: FOUNDER_DASHBOARD
Бит 7: ADVANCED_ANALYTICS
Бит 8: MULTI_DEPARTMENT
Биты 9-55: Резерв для будущих модулей

Пример: 0x000000000001FF = все 9 модулей включены
```

### 1.4 Алгоритм генерации

```python
def generate_license_key(
    license_type: LicenseTypeEnum,
    organization_name: str,
    modules: List[str],
    secret_key: str
) -> str:
    # 1. Organization hash
    org_hash = hashlib.sha256(organization_name.encode()).hexdigest()[:8].upper()

    # 2. Timestamp
    timestamp = datetime.now().strftime("%Y%m%d")

    # 3. Module flags
    module_bits = 0
    for module in modules:
        bit_position = MODULE_BIT_POSITIONS[module]
        module_bits |= (1 << bit_position)

    module_flags = f"{module_bits:014X}"

    # 4. Checksum
    data = f"{license_type.value}-{org_hash}-{timestamp}-{module_flags}"
    checksum = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:8].upper()

    # 5. Combine
    return f"{license_type.value}-{org_hash}-{timestamp}-{module_flags}-{checksum}"
```

## 2. Hardware Fingerprint

### 2.1 Компоненты fingerprint

```python
def generate_hardware_signature() -> str:
    """
    Создает уникальный отпечаток сервера

    Компоненты:
    1. CPU ID (если доступен)
    2. Primary MAC address
    3. Root disk serial number
    4. Hostname
    5. OS installation UUID (Linux: /etc/machine-id)
    """
    components = []

    # CPU ID
    try:
        cpu_id = get_cpu_id()
        components.append(cpu_id)
    except:
        pass

    # MAC Address (первый активный интерфейс)
    mac = get_primary_mac_address()
    if mac:
        components.append(mac)

    # Disk serial
    disk_serial = get_root_disk_serial()
    if disk_serial:
        components.append(disk_serial)

    # Hostname
    hostname = socket.gethostname()
    components.append(hostname)

    # Machine ID (Linux)
    try:
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
            components.append(machine_id)
    except:
        pass

    # Combine and hash
    combined = "|".join(components)
    signature = hashlib.sha256(combined.encode()).hexdigest()

    return signature
```

### 2.2 Проверка соответствия

```python
def verify_hardware_signature(stored_signature: str, tolerance: int = 1) -> bool:
    """
    Проверить соответствие текущего hardware signature сохраненному

    tolerance: количество компонентов, которые могут отличаться
               (для учета замены сетевой карты, смены hostname и т.д.)
    """
    current_signature = generate_hardware_signature()

    if stored_signature == current_signature:
        return True

    # Если не совпадает, проверяем по компонентам
    stored_components = get_signature_components(stored_signature)
    current_components = get_signature_components(current_signature)

    differences = sum(
        1 for s, c in zip(stored_components, current_components)
        if s != c
    )

    return differences <= tolerance
```

## 3. License Validation Flow

### 3.1 При установке

```
┌─────────────────────────────────────────────────┐
│  1. Ввод лицензионного ключа                    │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  2. Парсинг ключа                                │
│     - Извлечь type, org_hash, timestamp, flags  │
│     - Проверить формат                           │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  3. Проверка checksum                            │
│     - Вычислить checksum с secret_key           │
│     - Сравнить с ключом                          │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  4. Проверка в БД лицензий                       │
│     - Ключ уже активирован?                      │
│     - На каком сервере?                          │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  5. Генерация hardware signature                │
│     - Создать отпечаток сервера                  │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  6. Активация                                    │
│     - Сохранить в БД                             │
│     - Привязать к hardware signature             │
│     - Создать InstallationInfo                   │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  7. Инициализация модулей                        │
│     - Распарсить module flags                    │
│     - Создать OrganizationModule записи          │
└─────────────────────────────────────────────────┘
```

### 3.2 Runtime проверка (middleware)

```
┌─────────────────────────────────────────────────┐
│  Request → LicenseMiddleware                     │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  Skip public endpoints?                          │
│     - /health, /login, /docs                     │
└─────────────────────────────────────────────────┘
                     ↓ No
┌─────────────────────────────────────────────────┐
│  Get installation_info from DB                   │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  Check license validity                          │
│     - Exists?                                    │
│     - Active?                                    │
│     - Not expired?                               │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  Verify hardware signature (1x per hour)         │
│     - Cache result in Redis                      │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  Add license info to request.state               │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  Continue to endpoint                            │
└─────────────────────────────────────────────────┘
```

## 4. Database Schema

### 4.1 Таблицы

```sql
-- licenses
CREATE TABLE licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key VARCHAR(64) UNIQUE NOT NULL,
    license_type VARCHAR(50) NOT NULL,
    organization_name VARCHAR(255) NOT NULL,

    -- Validity
    issued_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,  -- NULL = permanent
    is_active BOOLEAN DEFAULT TRUE,

    -- Limits
    max_users INTEGER,
    max_departments INTEGER,
    max_transactions_per_month INTEGER,

    -- Hardware binding
    hardware_signature VARCHAR(128),
    server_id UUID,

    -- Module flags
    module_flags BIGINT NOT NULL,  -- Bit field

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    INDEX idx_license_key (license_key),
    INDEX idx_license_type (license_type),
    INDEX idx_hardware_sig (hardware_signature)
);

-- installation_info
CREATE TABLE installation_info (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID UNIQUE NOT NULL,

    -- Hardware
    hardware_signature VARCHAR(128) NOT NULL,
    hostname VARCHAR(255),
    os_info JSONB,

    -- Installation
    installation_date TIMESTAMP NOT NULL,
    version VARCHAR(20) NOT NULL,

    -- License binding
    license_id UUID REFERENCES licenses(id),

    -- Health checks
    last_check_at TIMESTAMP,
    last_signature_verified_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_server_id (server_id),
    INDEX idx_license_id (license_id)
);

-- license_audit_logs
CREATE TABLE license_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID REFERENCES licenses(id),

    event_type VARCHAR(50) NOT NULL,  -- ACTIVATION, VALIDATION_SUCCESS, VALIDATION_FAILED, etc.
    event_data JSONB,
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_license_id (license_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);

-- license_modules (связь лицензии с модулями)
CREATE TABLE license_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID REFERENCES licenses(id),
    module_code VARCHAR(50) NOT NULL,

    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,  -- Для временных модулей

    -- Module-specific limits
    limits JSONB,  -- {"max_contracts": 100, "max_invoices_per_month": 500}

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE (license_id, module_code),
    INDEX idx_license_id (license_id),
    INDEX idx_module_code (module_code)
);
```

### 4.2 Связь с существующими таблицами

```sql
-- organizations: Добавить license_id
ALTER TABLE organizations
ADD COLUMN license_id UUID REFERENCES licenses(id);

-- organization_modules: Уже существует, но нужна проверка лицензии
-- При включении модуля проверяем:
-- 1. Есть ли module_code в license.module_flags
-- 2. Не истек ли license_modules.expires_at
```

## 5. API Endpoints

### 5.1 License Management API

```python
# POST /api/v1/licenses/activate
@router.post("/activate")
async def activate_license(
    license_key: str = Body(...),
    db: Session = Depends(get_db)
):
    """
    Активировать лицензию при установке

    Body:
    {
        "license_key": "ENT-A1B2C3D4-20251120-FFFFFFFFFFFFFF-E5F6G7H8"
    }

    Response:
    {
        "success": true,
        "license": {
            "license_type": "ENTERPRISE",
            "organization_name": "ООО Компания",
            "expires_at": null,
            "available_modules": ["AI_FORECAST", "CREDIT_PORTFOLIO", ...]
        },
        "server_id": "uuid"
    }
    """
    pass

# GET /api/v1/licenses/status
@router.get("/status")
async def get_license_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить статус лицензии (для UI)

    Response:
    {
        "license_type": "ENTERPRISE",
        "organization_name": "ООО Компания",
        "is_active": true,
        "expires_at": null,
        "days_until_expiration": null,
        "available_modules": [...],
        "limits": {
            "max_users": 100,
            "current_users": 45,
            "max_departments": 10,
            "current_departments": 3
        }
    }
    """
    pass

# POST /api/v1/licenses/modules/add
@router.post("/modules/add")
async def add_module_to_license(
    module_code: str = Body(...),
    module_license_key: str = Body(...),  # Отдельный ключ для модуля
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Добавить модуль к существующей лицензии

    Body:
    {
        "module_code": "AI_FORECAST",
        "module_license_key": "MOD-AI-FORECAST-12345678"
    }

    Response:
    {
        "success": true,
        "module": {
            "code": "AI_FORECAST",
            "name": "AI прогнозирование",
            "is_active": true,
            "expires_at": "2026-12-31T23:59:59Z"
        }
    }
    """
    pass

# GET /api/v1/licenses/modules/available
@router.get("/modules/available")
async def get_available_modules(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить список доступных модулей

    Response:
    {
        "modules": [
            {
                "code": "AI_FORECAST",
                "name": "AI прогнозирование",
                "is_active": true,
                "is_available_in_license": true,
                "is_enabled_for_organization": true,
                "expires_at": null
            },
            ...
        ]
    }
    """
    pass

# POST /api/v1/licenses/validate
@router.post("/validate")
async def validate_license_key(
    license_key: str = Body(...)
):
    """
    Проверить валидность ключа (без активации)

    Body:
    {
        "license_key": "ENT-A1B2C3D4-20251120-FFFFFFFFFFFFFF-E5F6G7H8"
    }

    Response:
    {
        "valid": true,
        "license_type": "ENTERPRISE",
        "modules_count": 9,
        "already_activated": false
    }
    """
    pass
```

### 5.2 Installation API (внутренний)

```python
# POST /api/v1/installation/init
@router.post("/init")
async def initialize_installation(
    license_key: str = Body(...),
    admin_username: str = Body(...),
    admin_password: str = Body(...),
    admin_email: str = Body(...),
    db: Session = Depends(get_db)
):
    """
    Инициализация установки (вызывается из install.sh)

    1. Проверить и активировать лицензию
    2. Создать первую организацию
    3. Создать admin пользователя
    4. Инициализировать модули
    5. Загрузить базовые справочники
    """
    pass
```

## 6. Frontend Components

### 6.1 License Badge Component

```typescript
// components/license/LicenseBadge.tsx
export const LicenseBadge: React.FC = () => {
  const { license } = useLicense()

  const getBadgeColor = () => {
    if (!license?.isActive) return 'red'
    if (license.daysUntilExpiration && license.daysUntilExpiration < 30) {
      return 'orange'
    }
    return 'green'
  }

  return (
    <Badge
      count={license?.licenseType}
      style={{
        backgroundColor: getBadgeColor(),
        marginLeft: 16
      }}
    />
  )
}
```

### 6.2 Module Activation Modal

```typescript
// components/license/AddModuleModal.tsx
export const AddModuleModal: React.FC<Props> = ({ visible, onClose }) => {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      await api.addModuleToLicense(values)
      message.success('Module activated successfully')
      onClose()
    } catch (error) {
      message.error('Failed to activate module')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="Add Module to License"
      visible={visible}
      onCancel={onClose}
      footer={null}
    >
      <Form form={form} onFinish={handleSubmit}>
        <Form.Item
          name="module_code"
          label="Module"
          rules={[{ required: true }]}
        >
          <Select>
            <Option value="AI_FORECAST">AI прогнозирование</Option>
            <Option value="CREDIT_PORTFOLIO">Кредитный портфель</Option>
            {/* ... */}
          </Select>
        </Form.Item>

        <Form.Item
          name="module_license_key"
          label="License Key"
          rules={[{ required: true }]}
        >
          <Input.Password placeholder="MOD-..." />
        </Form.Item>

        <Button type="primary" htmlType="submit" loading={loading}>
          Activate Module
        </Button>
      </Form>
    </Modal>
  )
}
```

## 7. Docker Configuration

### 7.1 Production Dockerfile

```dockerfile
# backend/Dockerfile.production
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application
WORKDIR /app
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini .
COPY backend/scripts ./scripts

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Volumes for writable data
VOLUME ["/app/storage", "/app/logs"]

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Production docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: it-budget-backend:${VERSION:-latest}
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      SECRET_KEY: ${SECRET_KEY}
      LICENSE_KEY: ${LICENSE_KEY}
    volumes:
      - storage:/app/storage:rw
      - logs:/app/logs:rw
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: it-budget-frontend:${VERSION:-latest}
    restart: always
    depends_on:
      - backend
    ports:
      - "${PORT:-80}:80"
    read_only: true
    tmpfs:
      - /var/cache/nginx
      - /var/run
    security_opt:
      - no-new-privileges:true

volumes:
  postgres_data:
  storage:
  logs:
```

## 8. Security Considerations

### 8.1 Защита лицензионного ключа

1. **Secret Key хранение**:
   ```python
   # НЕ хардкодить в коде
   SECRET_KEY = os.getenv("LICENSE_SECRET_KEY")

   # Использовать разные ключи для разных окружений
   # Dev: один ключ
   # Production: другой ключ
   ```

2. **Шифрование в БД**:
   ```python
   # Хранить hardware_signature в зашифрованном виде
   from cryptography.fernet import Fernet

   def encrypt_signature(signature: str, key: bytes) -> str:
       f = Fernet(key)
       return f.encrypt(signature.encode()).decode()
   ```

3. **Rate limiting на validation API**:
   ```python
   # Ограничить попытки валидации
   @limiter.limit("10 per hour")
   @router.post("/licenses/validate")
   async def validate_license_key(...):
       pass
   ```

### 8.2 Защита от reverse engineering

1. **Obfuscation критичного кода** (опционально):
   ```bash
   # Использовать pyarmor для обфускации
   pyarmor obfuscate backend/app/services/license_validator.py
   ```

2. **Code signing**:
   ```bash
   # Подписать Docker образы
   docker trust sign it-budget-backend:1.0.0
   ```

3. **Integrity check**:
   ```python
   # Проверка целостности критичных файлов при старте
   def verify_file_integrity():
       checksums = {
           "app/services/license_validator.py": "abc123...",
           "app/core/license_middleware.py": "def456..."
       }

       for file_path, expected_checksum in checksums.items():
           actual_checksum = calculate_file_checksum(file_path)
           if actual_checksum != expected_checksum:
               raise SecurityError("File integrity violation")
   ```

## 9. Monitoring & Alerting

### 9.1 Метрики

```python
# Prometheus metrics
from prometheus_client import Counter, Gauge

license_validation_attempts = Counter(
    'license_validation_attempts_total',
    'Total license validation attempts',
    ['status']  # success, failed, expired
)

license_expiration_days = Gauge(
    'license_expiration_days',
    'Days until license expiration'
)

active_modules = Gauge(
    'active_modules_count',
    'Number of active modules'
)
```

### 9.2 Alerts

```yaml
# Prometheus alerts
groups:
  - name: license_alerts
    rules:
      - alert: LicenseExpiringSoon
        expr: license_expiration_days < 30
        for: 1h
        annotations:
          summary: "License expiring in {{ $value }} days"

      - alert: LicenseExpired
        expr: license_expiration_days <= 0
        annotations:
          summary: "License has expired"
          severity: critical

      - alert: TooManyValidationFailures
        expr: rate(license_validation_attempts{status="failed"}[5m]) > 10
        annotations:
          summary: "Possible license bypass attempt"
          severity: warning
```

## 10. Backup & Recovery

### 10.1 License Backup

```python
# Экспорт лицензии для backup
def export_license_data(license_id: UUID) -> dict:
    """
    Экспортировать данные лицензии для backup

    Включает:
    - License info
    - Module activations
    - Installation info
    - Audit logs (last 30 days)
    """
    pass

# Восстановление лицензии
def import_license_data(license_data: dict):
    """
    Восстановить лицензию из backup
    """
    pass
```

### 10.2 Disaster Recovery

```bash
# scripts/recover_license.sh
#!/bin/bash

# В случае потери лицензии из-за сбоя сервера:
# 1. Получить hardware signature нового сервера
# 2. Связаться с support
# 3. Получить новый ключ для нового hardware signature
# 4. Активировать
```

## Заключение

Эта техническая спецификация покрывает все аспекты системы лицензирования. Следующие шаги:

1. Review спецификации
2. Начать реализацию с Backend (Phase 1)
3. Параллельно работать над Docker packaging (Phase 2)
4. Интегрировать с Frontend (Phase 3)
5. Тестирование и deployment (Phase 4)
