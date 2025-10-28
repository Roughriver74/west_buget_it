# E2E Tests с Playwright

Набор end-to-end тестов для IT Budget Manager, покрывающих основные user flows.

## 📋 Тестовые сценарии

### 1. Authentication (`auth.spec.ts`)
- ✅ Отображение страницы логина
- ✅ Успешная авторизация с валидными данными
- ✅ Отображение ошибки при невалидных данных
- ✅ Выход из системы
- ✅ Редирект на /login для защищенных страниц
- ✅ Сохранение сессии после перезагрузки страницы
- ✅ Очистка сессии при выходе

### 2. Dashboard (`dashboard.spec.ts`)
- ✅ Отображение дашборда
- ✅ Отображение статистических карточек
- ✅ Отображение графиков и диаграмм
- ✅ Фильтрация по году
- ✅ Фильтрация по отделу
- ✅ Таблица последних расходов
- ✅ Навигация на страницу расходов
- ✅ Разбивка OPEX vs CAPEX

### 3. Expenses Management (`expenses.spec.ts`)
- ✅ Отображение списка расходов
- ✅ Открытие модального окна создания
- ✅ Создание новой заявки
- ✅ Валидация обязательных полей
- ✅ Фильтрация расходов
- ✅ Экспорт в Excel
- ✅ Поиск
- ✅ Пагинация

### 4. Budget Planning (`budget.spec.ts`)
- ✅ Отображение страницы планирования
- ✅ Таблица планирования бюджета
- ✅ Редактирование ячеек плана
- ✅ Переключение между годами
- ✅ Отображение итоговых сумм
- ✅ Копирование из предыдущего года
- ✅ Сохранение плана
- ✅ Разбивка OPEX/CAPEX
- ✅ Экспорт в Excel
- ✅ Навигация к обзору бюджета

## 🚀 Запуск тестов

### Установка зависимостей

```bash
cd frontend
npm install
npx playwright install  # Установка браузеров
```

### Запуск всех тестов

```bash
npm run test:e2e
```

### Запуск в UI mode (интерактивный режим)

```bash
npm run test:e2e:ui
```

### Запуск с видимым браузером

```bash
npm run test:e2e:headed
```

### Запуск в режиме отладки

```bash
npm run test:e2e:debug
```

### Запуск конкретного теста

```bash
npx playwright test auth.spec.ts
```

### Просмотр отчета о тестировании

```bash
npm run test:e2e:report
```

## 📝 Тестовые данные

### Учетные данные по умолчанию:
- **Username**: admin
- **Password**: admin

Данные определены в `helpers/auth.ts` и могут быть расширены для тестирования разных ролей.

## ⚙️ Конфигурация

Конфигурация тестов находится в `playwright.config.ts`:

- **Base URL**: http://localhost:5173
- **Browsers**: Chromium, Firefox, WebKit
- **Retries**: 2 на CI, 0 локально
- **Parallel**: Да
- **Screenshots**: Только при ошибках
- **Video**: Сохраняется при ошибках
- **Traces**: Записываются при первом retry

## 🔧 Структура проекта

```
e2e/
├── README.md                 # Эта документация
├── helpers/
│   └── auth.ts              # Хелперы для авторизации
├── auth.spec.ts             # Тесты авторизации
├── dashboard.spec.ts        # Тесты дашборда
├── expenses.spec.ts         # Тесты управления расходами
└── budget.spec.ts           # Тесты планирования бюджета
```

## 🐛 Troubleshooting

### Браузеры не установлены
```bash
npx playwright install
```

### Тайм-ауты на CI
Увеличьте timeout в `playwright.config.ts`:
```typescript
use: {
  actionTimeout: 10000, // 10 секунд
  navigationTimeout: 30000, // 30 секунд
}
```

### Тесты падают локально
1. Убедитесь, что приложение запущено на `http://localhost:5173`
2. Проверьте, что база данных заполнена тестовыми данными
3. Убедитесь, что пользователь `admin:admin` существует

### Скриншоты и видео
Все артефакты сохраняются в директорию `test-results/`:
- Screenshots: `test-results/**/*.png`
- Videos: `test-results/**/*.webm`
- Traces: `test-results/**/*.zip`

## 📊 CI/CD Integration

Тесты интегрированы в GitHub Actions pipeline (`.github/workflows/ci.yml`).

Запускаются автоматически:
- При каждом push в main/develop
- При создании Pull Request
- Можно запустить вручную

## 💡 Best Practices

1. **Используйте data-testid**: Добавляйте `data-testid` атрибуты к ключевым элементам UI
2. **Изолированные тесты**: Каждый тест должен быть независимым
3. **Очистка данных**: Используйте `beforeEach` для подготовки тестовой среды
4. **Ожидание готовности**: Используйте `waitForLoadState`, `waitForResponse` для синхронизации
5. **Читаемые селекторы**: Предпочитайте текстовые селекторы и роли

## 📚 Дополнительные ресурсы

- [Playwright Documentation](https://playwright.dev/)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [Selectors](https://playwright.dev/docs/selectors)
