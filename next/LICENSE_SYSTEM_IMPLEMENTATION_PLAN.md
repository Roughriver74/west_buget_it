# План реализации системы лицензирования и упаковки проекта

## Обзор задачи

Создать систему для:
1. **Упаковки проекта** в standalone дистрибутив
2. **Лицензирования** с базовой лицензией + дополнительные модули
3. **Установки на чистый сервер** через Docker-based installer
4. **Защиты от несанкционированного редактирования**
5. **Git-based deployment** для разработчика

## Архитектура решения

```
┌─────────────────────────────────────────────────────────────┐
│                    УПАКОВКА ПРОЕКТА                         │
│                                                               │
│  1. Docker Images (backend, frontend, db)                   │
│  2. Installer Script (install.sh)                           │
│  3. License Validator Service                               │
│  4. Configuration Wizard                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 ПРОЦЕСС УСТАНОВКИ                            │
│                                                               │
│  Step 1: License Key Validation                             │
│  Step 2: Basic Configuration (domain, DB, etc)              │
│  Step 3: Docker Compose Setup                               │
│  Step 4: Database Initialization                            │
│  Step 5: Admin User Creation                                │
│  Step 6: Module Activation (based on license)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               RUNTIME PROTECTION                             │
│                                                               │
│  1. License Check на каждый запрос (middleware)             │
│  2. Module Access Control (уже есть)                        │
│  3. Read-only File System для клиента                       │
│  4. Git Remote для разработчика                             │
└─────────────────────────────────────────────────────────────┘
```

## Фаза 1: Система лицензирования (Backend)

### 1.1 Модель данных лицензий

**Новые таблицы:**

```sql
-- licenses: Главная таблица лицензий
CREATE TABLE licenses (
    id UUID PRIMARY KEY,
    license_key VARCHAR(64) UNIQUE NOT NULL,
    license_type VARCHAR(50) NOT NULL,  -- BASE, PROFESSIONAL, ENTERPRISE
    organization_name VARCHAR(255) NOT NULL,
    issued_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    max_users INTEGER,
    max_departments INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    hardware_signature VARCHAR(128),  -- Привязка к серверу
    created_at TIMESTAMP DEFAULT NOW()
);

-- license_modules: Связь лицензии с модулями
CREATE TABLE license_modules (
    id UUID PRIMARY KEY,
    license_id UUID REFERENCES licenses(id),
    module_code VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    limits JSONB,  -- Дополнительные ограничения
    created_at TIMESTAMP DEFAULT NOW()
);

-- license_audit_logs: Аудит использования лицензий
CREATE TABLE license_audit_logs (
    id UUID PRIMARY KEY,
    license_id UUID REFERENCES licenses(id),
    event_type VARCHAR(50) NOT NULL,  -- ACTIVATION, VALIDATION, EXPIRATION_WARNING
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- installation_info: Информация об установке
CREATE TABLE installation_info (
    id UUID PRIMARY KEY,
    server_id UUID UNIQUE NOT NULL,  -- Уникальный ID сервера
    hardware_signature VARCHAR(128) NOT NULL,
    installation_date TIMESTAMP NOT NULL,
    version VARCHAR(20) NOT NULL,
    license_id UUID REFERENCES licenses(id),
    last_check_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.2 Backend сервисы

**Файлы для создания:**

```
backend/app/services/
├── license_service.py          # Главный сервис лицензирования
├── license_validator.py        # Валидация ключей
├── license_generator.py        # Генерация ключей (для разработчика)
├── hardware_fingerprint.py     # Создание hardware signature
└── license_checker.py          # Runtime проверки

backend/app/core/
└── license_middleware.py       # Middleware для проверки лицензии

backend/app/api/v1/
└── licenses.py                 # API endpoints для лицензий
```

**1.2.1 LicenseService (`license_service.py`)**

```python
class LicenseService:
    """Главный сервис управления лицензиями"""

    def validate_license(self, license_key: str, hardware_sig: str) -> LicenseValidationResult:
        """Проверить лицензию при установке"""
        pass

    def activate_license(self, license_key: str, server_id: UUID) -> License:
        """Активировать лицензию на сервере"""
        pass

    def check_license_status(self, license_id: UUID) -> LicenseStatus:
        """Проверить статус лицензии (expiration, limits)"""
        pass

    def get_available_modules(self, license_id: UUID) -> List[str]:
        """Получить доступные модули для лицензии"""
        pass

    def add_module_to_license(self, license_id: UUID, module_code: str, expires_at: datetime):
        """Добавить модуль к лицензии"""
        pass
```

**1.2.2 LicenseGenerator (`license_generator.py`)**

```python
class LicenseGenerator:
    """Генерация лицензионных ключей (только для разработчика)"""

    def generate_license_key(
        self,
        license_type: str,
        organization_name: str,
        expires_at: Optional[datetime],
        modules: List[str]
    ) -> str:
        """
        Генерация лицензионного ключа

        Формат: {type}-{org_hash}-{timestamp}-{checksum}
        Пример: BASE-A1B2C3D4-20251120-E5F6G7H8
        """
        pass

    def create_license(self, license_data: LicenseCreate) -> License:
        """Создать запись лицензии в БД"""
        pass
```

**1.2.3 HardwareFingerprint (`hardware_fingerprint.py`)**

```python
class HardwareFingerprint:
    """Создание уникального отпечатка сервера"""

    def generate_signature(self) -> str:
        """
        Создать hardware signature на основе:
        - CPU info
        - MAC address
        - Disk serial
        - Hostname

        Returns: SHA-256 hash
        """
        pass

    def verify_signature(self, stored_sig: str) -> bool:
        """Проверить соответствие текущему серверу"""
        pass
```

**1.2.4 LicenseMiddleware (`license_middleware.py`)**

```python
class LicenseMiddleware:
    """Middleware для проверки лицензии на каждый запрос"""

    async def __call__(self, request: Request, call_next):
        # Skip для public endpoints
        if request.url.path in ["/health", "/api/v1/auth/login"]:
            return await call_next(request)

        # Проверить лицензию
        license_status = await self.check_license()

        if not license_status.is_valid:
            return JSONResponse(
                status_code=403,
                content={"detail": "License expired or invalid"}
            )

        # Добавить информацию о лицензии в request.state
        request.state.license = license_status

        return await call_next(request)
```

### 1.3 API endpoints для лицензий

```python
# GET /api/v1/licenses/status
def get_license_status():
    """Получить текущий статус лицензии (ADMIN only)"""
    pass

# POST /api/v1/licenses/activate
def activate_license(license_key: str):
    """Активировать лицензию (при установке)"""
    pass

# POST /api/v1/licenses/modules/add
def add_module(module_code: str, license_key: str):
    """Добавить модуль к лицензии (ADMIN only)"""
    pass

# GET /api/v1/licenses/modules/available
def get_available_modules():
    """Получить доступные модули"""
    pass

# GET /api/v1/licenses/info
def get_license_info():
    """Информация о лицензии (для UI)"""
    pass
```

## Фаза 2: Упаковка проекта

### 2.1 Docker Multi-stage Build

**Создать оптимизированные образы:**

```dockerfile
# backend/Dockerfile.production
FROM python:3.11-slim as builder

# Build dependencies
RUN pip install --no-cache-dir poetry
COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry export -f requirements.txt > requirements.txt

FROM python:3.11-slim

# Install runtime dependencies only
COPY --from=builder /requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/app /app/app
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/

WORKDIR /app

# Read-only filesystem (security)
USER nobody
VOLUME ["/app/storage"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile.production
FROM node:18-alpine as builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Read-only
USER nginx

EXPOSE 80
```

### 2.2 Packaging Script

**Создать `scripts/package.sh`:**

```bash
#!/bin/bash
# Упаковка проекта для дистрибуции

set -e

VERSION=${1:-"1.0.0"}
OUTPUT_DIR="dist/it-budget-manager-${VERSION}"

echo "📦 Packaging IT Budget Manager v${VERSION}..."

# 1. Create directory structure
mkdir -p "${OUTPUT_DIR}"/{docker,installer,docs}

# 2. Build Docker images
docker build -f backend/Dockerfile.production -t it-budget-backend:${VERSION} .
docker build -f frontend/Dockerfile.production -t it-budget-frontend:${VERSION} .

# 3. Save images to tar
docker save it-budget-backend:${VERSION} | gzip > "${OUTPUT_DIR}/docker/backend.tar.gz"
docker save it-budget-frontend:${VERSION} | gzip > "${OUTPUT_DIR}/docker/frontend.tar.gz"
docker pull postgres:15 && docker save postgres:15 | gzip > "${OUTPUT_DIR}/docker/postgres.tar.gz"

# 4. Copy installer
cp installer/install.sh "${OUTPUT_DIR}/installer/"
cp installer/config.template.env "${OUTPUT_DIR}/installer/"
cp docker-compose.production.yml "${OUTPUT_DIR}/docker-compose.yml"

# 5. Copy documentation
cp docs/INSTALLATION_GUIDE.md "${OUTPUT_DIR}/docs/"
cp LICENSE "${OUTPUT_DIR}/"
cp README.md "${OUTPUT_DIR}/"

# 6. Create archive
tar -czf "it-budget-manager-${VERSION}.tar.gz" -C dist "it-budget-manager-${VERSION}"

echo "✅ Package created: it-budget-manager-${VERSION}.tar.gz"
```

## Фаза 3: Installer Script

### 3.1 Интерактивный установщик

**Создать `installer/install.sh`:**

```bash
#!/bin/bash
# IT Budget Manager - Interactive Installer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/it-budget-manager"

echo "╔════════════════════════════════════════════════════╗"
echo "║   IT Budget Manager - Installation Wizard         ║"
echo "║   Version 1.0.0                                    ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Step 1: License Validation
echo "📋 Step 1/6: License Activation"
echo "─────────────────────────────────────────────────"
read -p "Enter your license key: " LICENSE_KEY

# Validate license (call validation API or local check)
if ! validate_license "$LICENSE_KEY"; then
    echo "❌ Invalid license key. Installation aborted."
    exit 1
fi

echo "✅ License validated successfully"
echo ""

# Step 2: Domain Configuration
echo "🌐 Step 2/6: Domain Configuration"
echo "─────────────────────────────────────────────────"
read -p "Enter domain name (e.g., budget.company.com): " DOMAIN_NAME
read -p "Enable HTTPS? (y/n): " ENABLE_HTTPS

echo ""

# Step 3: Database Configuration
echo "💾 Step 3/6: Database Configuration"
echo "─────────────────────────────────────────────────"
read -p "Database name [it_budget_db]: " DB_NAME
DB_NAME=${DB_NAME:-it_budget_db}

read -p "Database user [budget_user]: " DB_USER
DB_USER=${DB_USER:-budget_user}

read -s -p "Database password: " DB_PASSWORD
echo ""

# Generate random secret key
SECRET_KEY=$(openssl rand -hex 32)

echo ""

# Step 4: Admin User
echo "👤 Step 4/6: Create Admin User"
echo "─────────────────────────────────────────────────"
read -p "Admin username [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "Admin password: " ADMIN_PASSWORD
echo ""

read -p "Admin email: " ADMIN_EMAIL
echo ""

# Step 5: Installation
echo "📦 Step 5/6: Installing..."
echo "─────────────────────────────────────────────────"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Copy files
cp -r "$SCRIPT_DIR/../docker" .
cp "$SCRIPT_DIR/../docker-compose.yml" .

# Generate .env file
cat > .env <<EOF
# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DOMAIN_NAME=${DOMAIN_NAME}
ENABLE_HTTPS=${ENABLE_HTTPS}

# License
LICENSE_KEY=${LICENSE_KEY}

# Admin
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
ADMIN_EMAIL=${ADMIN_EMAIL}
EOF

# Load Docker images
echo "Loading Docker images..."
docker load < docker/backend.tar.gz
docker load < docker/frontend.tar.gz
docker load < docker/postgres.tar.gz

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for database
echo "Waiting for database to be ready..."
sleep 10

# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py

# Activate license
docker-compose exec backend python scripts/activate_license.py "$LICENSE_KEY"

echo ""

# Step 6: Complete
echo "✅ Step 6/6: Installation Complete!"
echo "─────────────────────────────────────────────────"
echo ""
echo "📊 IT Budget Manager is now running at:"
if [ "$ENABLE_HTTPS" == "y" ]; then
    echo "   https://${DOMAIN_NAME}"
else
    echo "   http://${DOMAIN_NAME}"
fi
echo ""
echo "🔐 Admin credentials:"
echo "   Username: ${ADMIN_USERNAME}"
echo "   Password: ${ADMIN_PASSWORD}"
echo ""
echo "📖 Documentation: ${INSTALL_DIR}/docs/INSTALLATION_GUIDE.md"
echo ""
echo "🚀 To manage the application:"
echo "   cd ${INSTALL_DIR}"
echo "   docker-compose logs -f           # View logs"
echo "   docker-compose restart           # Restart services"
echo "   docker-compose down              # Stop services"
echo ""
```

## Фаза 4: Frontend интеграция лицензий

### 4.1 License Context

**Создать `frontend/src/contexts/LicenseContext.tsx`:**

```typescript
interface LicenseInfo {
  licenseKey: string
  licenseType: 'BASE' | 'PROFESSIONAL' | 'ENTERPRISE'
  organizationName: string
  expiresAt: string | null
  isActive: boolean
  availableModules: string[]
  limits: {
    maxUsers: number
    maxDepartments: number
  }
}

export const LicenseContext = createContext<{
  license: LicenseInfo | null
  isLoading: boolean
  hasModule: (moduleCode: string) => boolean
  refreshLicense: () => Promise<void>
}>()

export const LicenseProvider = ({ children }) => {
  const [license, setLicense] = useState<LicenseInfo | null>(null)

  useEffect(() => {
    fetchLicenseInfo()
  }, [])

  const hasModule = (moduleCode: string) => {
    return license?.availableModules.includes(moduleCode) ?? false
  }

  return (
    <LicenseContext.Provider value={{ license, hasModule }}>
      {children}
    </LicenseContext.Provider>
  )
}
```

### 4.2 License Management Page

**Создать `frontend/src/pages/LicenseManagementPage.tsx`:**

```typescript
const LicenseManagementPage = () => {
  const { license } = useLicense()
  const [addingModule, setAddingModule] = useState(false)

  return (
    <div>
      <Card title="License Information">
        <Descriptions>
          <Item label="License Type">{license.licenseType}</Item>
          <Item label="Organization">{license.organizationName}</Item>
          <Item label="Expires At">{license.expiresAt || 'Never'}</Item>
          <Item label="Status">
            <Badge
              status={license.isActive ? 'success' : 'error'}
              text={license.isActive ? 'Active' : 'Inactive'}
            />
          </Item>
        </Descriptions>
      </Card>

      <Card title="Active Modules" style={{ marginTop: 24 }}>
        <List
          dataSource={license.availableModules}
          renderItem={(module) => (
            <List.Item>
              <CheckCircleOutlined style={{ color: 'green' }} />
              {module}
            </List.Item>
          )}
        />

        <Button
          type="primary"
          onClick={() => setAddingModule(true)}
          style={{ marginTop: 16 }}
        >
          Add Module
        </Button>
      </Card>

      <AddModuleModal
        visible={addingModule}
        onClose={() => setAddingModule(false)}
      />
    </div>
  )
}
```

## Фаза 5: Защита от редактирования

### 5.1 Read-only File System

**В `docker-compose.production.yml`:**

```yaml
services:
  backend:
    image: it-budget-backend:latest
    read_only: true  # Файловая система только для чтения
    volumes:
      - storage:/app/storage:rw  # Только storage writable
      - logs:/app/logs:rw
    tmpfs:
      - /tmp
    user: "1000:1000"  # Non-root user

  frontend:
    image: it-budget-frontend:latest
    read_only: true
    tmpfs:
      - /var/cache/nginx
      - /var/run
```

### 5.2 Git-based Deployment для разработчика

**Создать `scripts/developer_deploy.sh`:**

```bash
#!/bin/bash
# Deployment script for developers

# Требования:
# 1. SSH ключ к серверу
# 2. Git remote configured
# 3. Developer license key

REMOTE_HOST="production-server"
REMOTE_PATH="/opt/it-budget-manager"

echo "🔐 Developer Deployment"
read -s -p "Enter developer license key: " DEV_LICENSE
echo ""

# Verify developer license
if ! verify_developer_license "$DEV_LICENSE"; then
    echo "❌ Invalid developer license"
    exit 1
fi

# SSH to server and pull updates
ssh "$REMOTE_HOST" <<EOF
    cd "$REMOTE_PATH"

    # Backup current version
    docker-compose exec backend pg_dump -U budget_user it_budget_db > backup.sql

    # Pull updates from git
    git pull origin main

    # Rebuild and restart
    docker-compose build
    docker-compose up -d

    # Run migrations
    docker-compose exec backend alembic upgrade head
EOF

echo "✅ Deployment complete"
```

## Фаза 6: Интеграция с существующей системой модулей

### 6.1 Связь Licenses ↔ Modules

**Обновить `backend/app/services/module_service.py`:**

```python
class ModuleService:
    def __init__(self, db: Session, license_service: LicenseService):
        self.db = db
        self.license_service = license_service

    def get_available_modules(self, organization_id: int) -> List[Module]:
        """
        Получить доступные модули с учетом лицензии
        """
        # 1. Получить модули из лицензии
        license = self.license_service.get_organization_license(organization_id)
        licensed_modules = license.available_modules

        # 2. Получить активированные модули организации
        org_modules = self.db.query(OrganizationModule).filter(
            OrganizationModule.organization_id == organization_id,
            OrganizationModule.is_active == True
        ).all()

        # 3. Фильтровать по лицензии
        return [
            mod for mod in org_modules
            if mod.module.code in licensed_modules
        ]
```

### 6.2 Module Gate с License Check

**Обновить `backend/app/core/module_guard.py`:**

```python
def require_module(module_code: str):
    def decorator(
        current_user: User = Depends(get_current_active_user),
        license_status: LicenseStatus = Depends(get_license_status),
        db: Session = Depends(get_db)
    ):
        # 1. Check license
        if module_code not in license_status.available_modules:
            raise HTTPException(
                status_code=403,
                detail=f"Module {module_code} not available in your license"
            )

        # 2. Check organization module activation
        org_module = db.query(OrganizationModule).filter(
            OrganizationModule.organization_id == current_user.organization_id,
            OrganizationModule.module.code == module_code,
            OrganizationModule.is_active == True
        ).first()

        if not org_module:
            raise HTTPException(
                status_code=403,
                detail=f"Module {module_code} not activated"
            )

        return org_module

    return Depends(decorator)
```

## Фаза 7: Тестирование и документация

### 7.1 Тестовые сценарии

1. **Установка на чистый сервер**
   - Создать VM с Ubuntu 22.04
   - Распаковать дистрибутив
   - Запустить installer
   - Проверить работу приложения

2. **Активация модулей**
   - Войти как admin
   - Добавить лицензионный ключ для модуля
   - Проверить доступность функционала

3. **Попытка редактирования**
   - Попытаться изменить файлы в контейнере
   - Должна быть ошибка "Read-only file system"

4. **Developer deployment**
   - Использовать developer license
   - Сделать изменения в коде
   - Задеплоить через Git

### 7.2 Документация

**Создать:**

1. `docs/INSTALLATION_GUIDE.md` - Руководство по установке
2. `docs/LICENSE_MANAGEMENT.md` - Управление лицензиями
3. `docs/DEVELOPER_DEPLOYMENT.md` - Deployment для разработчика
4. `docs/PACKAGING_GUIDE.md` - Инструкции по сборке дистрибутива

## График реализации

### Спринт 1 (5 дней): Backend лицензирование
- [ ] День 1: Модели данных + миграции
- [ ] День 2: LicenseService, LicenseValidator
- [ ] День 3: LicenseGenerator, HardwareFingerprint
- [ ] День 4: API endpoints
- [ ] День 5: Middleware + интеграция с модулями

### Спринт 2 (3 дня): Упаковка и installer
- [ ] День 1: Docker production builds
- [ ] День 2: Packaging script
- [ ] День 3: Interactive installer

### Спринт 3 (3 дня): Frontend + защита
- [ ] День 1: License Context + UI
- [ ] День 2: Read-only filesystem + security
- [ ] День 3: Developer deployment script

### Спринт 4 (2 дня): Тестирование + документация
- [ ] День 1: Тестирование на чистой VM
- [ ] День 2: Документация

**Итого: 13 дней**

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|------------|-----------|
| Обход лицензионной защиты | Средняя | Регулярная проверка лицензии + hardware binding |
| Проблемы с Docker на разных ОС | Низкая | Тестирование на Ubuntu/Debian/CentOS |
| Сложность установки для клиента | Средняя | Интерактивный wizard + подробная документация |
| Конфликты портов | Средняя | Автоопределение занятых портов |

## Следующие шаги

1. **Утвердить архитектуру** - Review этого плана
2. **Создать тикеты** - Разбить на задачи в issue tracker
3. **Начать с бэкенда** - Спринт 1
4. **Параллельная работа над упаковкой** - Можно начать Спринт 2 параллельно

## Вопросы для обсуждения

1. **Типы лицензий**: Какие тарифные планы? (BASE, PRO, ENTERPRISE)
2. **Ценообразование модулей**: Фиксированная цена или по подписке?
3. **Trial период**: Нужна ли демо-версия на 30 дней?
4. **Online activation**: Нужна ли проверка лицензий через онлайн API?
5. **Upgrade path**: Как обновлять систему без переустановки?
