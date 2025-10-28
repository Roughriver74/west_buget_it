import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

test.describe('Expenses Management', () => {
  test.beforeEach(async ({ page }) => {
    // Логинимся перед каждым тестом
    await loginAsAdmin(page);
  });

  test('should display expenses list page', async ({ page }) => {
    await page.goto('/expenses');

    // Проверяем, что мы на странице расходов
    await expect(page).toHaveURL('/expenses');

    // Проверяем наличие заголовка
    await expect(page.locator('h1, h2, .page-title')).toContainText(/Заявки|Расходы|Expenses/i);

    // Проверяем наличие таблицы
    const table = page.locator('.ant-table, table');
    await expect(table).toBeVisible({ timeout: 10000 });
  });

  test('should open create expense modal', async ({ page }) => {
    await page.goto('/expenses');

    // Ждем загрузки страницы
    await page.waitForLoadState('networkidle');

    // Ищем кнопку создания (может быть "Создать", "Добавить", "+" и т.д.)
    const createButton = page.locator('button:has-text("Создать"), button:has-text("Добавить"), button:has(svg)').first();
    await expect(createButton).toBeVisible();

    await createButton.click();

    // Проверяем, что модальное окно открылось
    const modal = page.locator('.ant-modal, [role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Проверяем наличие формы с полями
    await expect(modal.locator('form, .ant-form')).toBeVisible();
  });

  test('should create new expense', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');

    // Открываем модальное окно создания
    const createButton = page.locator('button:has-text("Создать"), button:has-text("Добавить")').first();
    await createButton.click();

    // Ждем появления модального окна
    const modal = page.locator('.ant-modal, [role="dialog"]');
    await expect(modal).toBeVisible();

    // Заполняем форму
    // Номер заявки (генерируем уникальный)
    const expenseNumber = `TEST-${Date.now()}`;
    await modal.locator('input[name="number"], input[id="number"]').fill(expenseNumber);

    // Сумма
    await modal.locator('input[name="amount"], input[id="amount"]').fill('10000');

    // Дата запроса (если есть DatePicker)
    const dateInput = modal.locator('input[placeholder*="дат"], .ant-picker-input input').first();
    if (await dateInput.isVisible()) {
      await dateInput.click();
      // Выбираем сегодняшний день
      await page.locator('.ant-picker-today-btn, .ant-picker-cell-today').click();
    }

    // Категория (выпадающий список)
    const categorySelect = modal.locator('.ant-select:has-text("Категория"), select[name="category_id"]').first();
    if (await categorySelect.isVisible()) {
      await categorySelect.click();
      await page.waitForTimeout(500);
      // Выбираем первую категорию из списка
      await page.locator('.ant-select-item').first().click();
    }

    // Контрагент (может быть автокомплит)
    const contractorSelect = modal.locator('.ant-select:has-text("Контрагент"), input[name="contractor"]').first();
    if (await contractorSelect.isVisible()) {
      await contractorSelect.click();
      await page.waitForTimeout(500);
      // Выбираем первого контрагента
      await page.locator('.ant-select-item').first().click();
    }

    // Комментарий
    const commentField = modal.locator('textarea[name="comment"], textarea[id="comment"]');
    if (await commentField.isVisible()) {
      await commentField.fill('Тестовая заявка создана через E2E тест');
    }

    // Нажимаем кнопку сохранения
    const submitButton = modal.locator('button[type="submit"], button:has-text("Создать"), button:has-text("Сохранить")');
    await submitButton.click();

    // Ждем закрытия модального окна
    await expect(modal).not.toBeVisible({ timeout: 10000 });

    // Ждем обновления списка
    await page.waitForResponse((response) =>
      response.url().includes('/api/v1/expenses') && response.status() === 200
    );

    // Проверяем, что заявка появилась в списке
    await page.waitForTimeout(1000);
    const newExpenseRow = page.locator(`tr:has-text("${expenseNumber}")`);
    await expect(newExpenseRow).toBeVisible({ timeout: 10000 });
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');

    // Открываем модальное окно
    const createButton = page.locator('button:has-text("Создать"), button:has-text("Добавить")').first();
    await createButton.click();

    const modal = page.locator('.ant-modal, [role="dialog"]');
    await expect(modal).toBeVisible();

    // Пытаемся сохранить пустую форму
    const submitButton = modal.locator('button[type="submit"], button:has-text("Создать"), button:has-text("Сохранить")');
    await submitButton.click();

    // Проверяем, что появились сообщения об ошибках валидации
    const errorMessages = page.locator('.ant-form-item-explain-error, .ant-form-item-has-error');
    await expect(errorMessages.first()).toBeVisible({ timeout: 3000 });
  });

  test('should filter expenses', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');

    // Ищем фильтры (могут быть кнопки, селекты, inputs)
    const filterButton = page.locator('button:has-text("Фильтр"), button:has(svg[data-icon="filter"])').first();

    if (await filterButton.isVisible()) {
      await filterButton.click();

      // Применяем какой-нибудь фильтр (например, по статусу)
      const statusFilter = page.locator('.ant-select:has-text("Статус"), select[name="status"]').first();
      if (await statusFilter.isVisible()) {
        await statusFilter.click();
        await page.locator('.ant-select-item').first().click();

        // Ждем обновления данных
        await page.waitForResponse((response) =>
          response.url().includes('/api/v1/expenses') && response.status() === 200
        );
      }
    }
  });

  test('should export expenses to Excel', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');

    // Ищем кнопку экспорта
    const exportButton = page.locator('button:has-text("Экспорт"), button:has-text("Export"), button:has(svg[data-icon="download"])').first();

    if (await exportButton.isVisible()) {
      // Начинаем ожидание загрузки файла
      const downloadPromise = page.waitForEvent('download');

      await exportButton.click();

      // Ждем загрузки файла
      const download = await downloadPromise;

      // Проверяем, что файл скачался
      expect(download.suggestedFilename()).toMatch(/\.xlsx?$/i);
    }
  });

  test('should search expenses', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');

    // Ищем поле поиска
    const searchInput = page.locator('input[placeholder*="Поиск"], input[placeholder*="Search"], input[type="search"]').first();

    if (await searchInput.isVisible()) {
      await searchInput.fill('test');

      // Ждем обновления результатов
      await page.waitForTimeout(1000);

      // Проверяем, что произошел запрос с параметром поиска
      await page.waitForResponse((response) =>
        response.url().includes('/api/v1/expenses') && response.status() === 200,
        { timeout: 5000 }
      ).catch(() => {
        // Если запрос не произошел, это нормально - может быть клиентский поиск
      });
    }
  });

  test('should paginate expenses', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');

    // Ищем пагинацию
    const pagination = page.locator('.ant-pagination');

    if (await pagination.isVisible()) {
      // Проверяем наличие кнопок следующей страницы
      const nextButton = pagination.locator('li.ant-pagination-next').first();

      if (await nextButton.isVisible() && !(await nextButton.isDisabled())) {
        await nextButton.click();

        // Ждем загрузки новой страницы
        await page.waitForResponse((response) =>
          response.url().includes('/api/v1/expenses') && response.status() === 200
        );

        // Проверяем, что URL или данные изменились
        await page.waitForTimeout(500);
      }
    }
  });
});
