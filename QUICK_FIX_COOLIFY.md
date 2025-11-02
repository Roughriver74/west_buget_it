# 🚨 СРОЧНОЕ ИСПРАВЛЕНИЕ - Пошаговая инструкция

## Проблема
Frontend всё ещё обращается к `http://localhost:8888` вместо реального API.

## ✅ РЕШЕНИЕ (5 минут)

### Шаг 1: Откройте Coolify

Зайдите на https://west-it.ru (или http://93.189.228.52:8000)

### Шаг 2: Найдите Frontend приложение

В проекте "IT Budget Manager" откройте **Frontend** сервис

### Шаг 3: Измените переменную окружения

1. Перейдите в раздел **Environment Variables**
2. Найдите переменную `VITE_API_URL`
3. **ИЗМЕНИТЕ** значение:

```bash
# БЫЛО (неправильно):
VITE_API_URL=https://api.budget-west.shknv.ru

# ДОЛЖНО БЫТЬ (правильно):
VITE_API_URL=https://api.budget-west.shknv.ru/api/v1
```

⚠️ **ВАЖНО**: Обратите внимание на `/api/v1` в конце!

4. Нажмите **Save** или **Update**

### Шаг 4: Rebuild Frontend

⚠️ **КРИТИЧЕСКИ ВАЖНО**: НЕ нажимайте "Restart"!

1. Найдите кнопку **"Rebuild"** или **"Redeploy"**
2. Нажмите на неё
3. Подождите окончания сборки (3-5 минут)

**Почему Rebuild?**
- `VITE_API_URL` используется при **сборке** (build time)
- Restart только перезапускает контейнер со старой сборкой
- Rebuild пересоберёт с новыми переменными

### Шаг 5: Проверьте Backend переменные

Откройте **Backend** сервис в Coolify:

1. Перейдите в **Environment Variables**
2. Убедитесь что есть:

```bash
CORS_ORIGINS=["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]
```

⚠️ **Оба домена** должны быть в списке!

3. Если изменили - нажмите **Restart** (для backend достаточно restart)

### Шаг 6: Проверка после деплоя

#### 6.1. Проверьте API

Откройте в браузере или через curl:

```bash
curl https://api.budget-west.shknv.ru/api/v1/health
```

Должно вернуть:
```json
{"status":"ok"}
```

#### 6.2. Проверьте конфигурацию frontend

Откройте в браузере:
```
https://budget-west.shknv.ru/config-check
```

Должно показать:
```javascript
window.ENV_CONFIG = {
  VITE_API_URL: 'https://api.budget-west.shknv.ru/api/v1'
};
```

Если всё ещё показывает `http://localhost:8888` - значит rebuild не завершился или не применился.

#### 6.3. Проверьте работу сайта

1. Очистите кэш браузера: **Ctrl+Shift+Delete** или **Cmd+Shift+Delete**
2. Откройте https://budget-west.shknv.ru/login
3. Откройте DevTools (F12) → **Console** tab
4. Попробуйте залогиниться
5. В консоли НЕ должно быть ошибок про `localhost:8888`

#### 6.4. Проверьте Network tab

В DevTools → **Network** tab:
- Должны быть запросы к `https://api.budget-west.shknv.ru/api/v1/auth/login`
- НЕ должно быть запросов к `localhost:8888`

---

## 🔍 Если всё ещё не работает

### Проблема: env-config.js всё ещё показывает localhost

**Решение**: Проверьте логи frontend контейнера

```bash
ssh root@93.189.228.52
docker ps | grep frontend
docker logs <container_id> --tail 50
```

Ищите строку:
```
Generated env-config.js with VITE_API_URL: ...
```

### Проблема: CORS ошибки

В DevTools Console видите:
```
Access to fetch at 'https://api.budget-west.shknv.ru' from origin 'https://budget-west.shknv.ru' has been blocked by CORS
```

**Решение**:
1. Проверьте `CORS_ORIGINS` в Backend
2. Должно быть: `["https://budget-west.shknv.ru","https://api.budget-west.shknv.ru"]`
3. Restart Backend

### Проблема: 404 на CSS/JS файлы

```
Failed to load resource: the server responded with a status of 404 (index-XXX.css)
```

**Причина**: Старый кэш браузера

**Решение**:
1. Очистите кэш: Ctrl+Shift+Delete
2. Hard reload: Ctrl+Shift+R (или Cmd+Shift+R на Mac)
3. Закройте и откройте браузер

---

## 📋 Итоговый чеклист

- [ ] Изменил `VITE_API_URL` на `https://api.budget-west.shknv.ru/api/v1` в Frontend
- [ ] Нажал **Rebuild** (не Restart!) для Frontend
- [ ] Дождался окончания сборки
- [ ] Проверил `CORS_ORIGINS` в Backend
- [ ] Проверил `curl https://api.budget-west.shknv.ru/api/v1/health`
- [ ] Проверил `https://budget-west.shknv.ru/config-check`
- [ ] Очистил кэш браузера
- [ ] Открыл сайт и проверил DevTools Console
- [ ] Залогинился успешно

---

## 💡 Почему это работает?

### Vite build process:

```
1. Build time (Rebuild):
   VITE_API_URL → встраивается в JavaScript бандл

2. Runtime (Container start):
   docker-entrypoint.sh → создаёт env-config.js

3. Browser load:
   index.html → загружает env-config.js
   React app → читает window.ENV_CONFIG.VITE_API_URL
```

Без **Rebuild** старое значение остаётся в JavaScript бандле!

---

## 🆘 Критическая проблема?

Если ничего не помогает, попробуйте **полный редеплой**:

1. В Coolify для Frontend:
   - Stop service
   - Clear builds/cache (если есть опция)
   - Rebuild from scratch

2. Или через SSH:
```bash
ssh root@93.189.228.52
docker stop <frontend_container>
docker rm <frontend_container>
docker rmi <frontend_image>
# Затем в Coolify нажмите Deploy
```

---

## 📞 Если нужна помощь

Пришлите вывод команд:

```bash
# 1. Проверьте что показывает config-check
curl https://budget-west.shknv.ru/config-check

# 2. Проверьте API
curl https://api.budget-west.shknv.ru/api/v1/health

# 3. Логи frontend
ssh root@93.189.228.52
docker logs $(docker ps -q -f name=frontend) --tail 50

# 4. Логи backend
docker logs $(docker ps -q -f name=backend) --tail 50
```
