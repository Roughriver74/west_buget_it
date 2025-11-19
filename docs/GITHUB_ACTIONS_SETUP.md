# GitHub Actions Setup для автоматического деплоя на тестовый сервер

## Обзор

Настроен автоматический деплой на тестовый сервер при каждом push в ветку `test`.

## Требуемые GitHub Secrets

Необходимо настроить следующие секреты в репозитории GitHub:

### 1. `TEST_SERVER_SSH_KEY`
**Описание**: Приватный SSH ключ для доступа к тестовому серверу

**Как получить**:
```bash
cat ~/.ssh/id_rsa
```

**Значение**: Скопируйте весь вывод команды, включая строки:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...содержимое ключа...
-----END OPENSSH PRIVATE KEY-----
```

### 2. `TEST_SERVER_IP`
**Описание**: IP адрес тестового сервера

**Значение**: `46.173.18.143`

### 3. `TEST_SERVER_USER`
**Описание**: Пользователь для SSH подключения

**Значение**: `root`

### 4. `TEST_SERVER_PROJECT_PATH`
**Описание**: Путь к проекту на тестовом сервере

**Значение**: `/root/west_budget_test`

## Как настроить GitHub Secrets

1. Перейдите в репозиторий на GitHub
2. Откройте **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**
4. Добавьте каждый из секретов выше
5. Нажмите **Add secret**

## Workflow файл

Файл workflow: `.github/workflows/deploy-test.yml`

### Триггеры:
- **Автоматический**: При push в ветку `test`
- **Ручной**: Через Actions → "Run workflow"

## Доступ к тестовому окружению

- **Frontend**: http://46.173.18.143:3002
- **Backend API**: http://46.173.18.143:8889
- **API Docs**: http://46.173.18.143:8889/docs

## Учетные данные администратора

- **Username**: `admin`
- **Email**: `admin@test.local`
- **Password**: `admin123test`
