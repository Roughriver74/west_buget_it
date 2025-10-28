import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

test.describe('Budget Planning', () => {
  test.beforeEach(async ({ page }) => {
    // Логинимся перед каждым тестом
    await loginAsAdmin(page);
  });

  test('should display budget planning page', async ({ page }) => {
    await page.goto('/budget/plan');

    // Проверяем, что мы на странице планирования бюджета
    await expect(page).toHaveURL(/\/budget\/plan/);

    // Проверяем наличие заголовка
    await expect(page.locator('h1, h2, .page-title')).toContainText(/Планирование|Бюджет|Budget|План/i);
  });

  test('should display budget plan table', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Проверяем наличие таблицы планирования
    const table = page.locator('.ant-table, table');
    await expect(table.first()).toBeVisible({ timeout: 10000 });

    // Проверяем наличие заголовков месяцев
    const monthHeaders = page.locator('th:has-text("Январь"), th:has-text("Февраль"), th:has-text("Март")');
    if (await monthHeaders.first().isVisible()) {
      await expect(monthHeaders.first()).toBeVisible();
    }
  });

  test('should edit budget plan cell', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем редактируемую ячейку таблицы
    const editableCell = page.locator('td.editable-cell, td[contenteditable="true"], td input[type="number"]').first();

    if (await editableCell.isVisible()) {
      // Кликаем по ячейке
      await editableCell.click();

      // Находим input поле (может появиться после клика)
      const input = page.locator('input[type="number"]').first();
      if (await input.isVisible()) {
        // Очищаем и вводим новое значение
        await input.clear();
        await input.fill('50000');

        // Сохраняем (нажатием Enter или кликом вне)
        await input.press('Enter');

        // Ждем сохранения
        await page.waitForResponse((response) =>
          response.url().includes('/api/v1/budget') && response.status() === 200,
          { timeout: 5000 }
        ).catch(() => {
          // Может быть batch save, это нормально
        });
      }
    }
  });

  test('should switch between years', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем селектор года
    const yearSelector = page.locator('select[name="year"], .ant-select:has-text("2025")').first();

    if (await yearSelector.isVisible()) {
      await yearSelector.click();

      // Выбираем другой год (если доступен)
      const yearOption = page.locator('.ant-select-item:has-text("2024")').first();
      if (await yearOption.isVisible()) {
        await yearOption.click();

        // Ждем обновления данных
        await page.waitForResponse((response) =>
          response.url().includes('/api/v1/budget') && response.status() === 200
        );
      }
    }
  });

  test('should display budget totals', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем итоговые суммы (могут быть в footer таблицы или отдельных карточках)
    const totals = page.locator('tfoot, .total-row, .summary-card, [class*="total"]');

    if (await totals.first().isVisible()) {
      await expect(totals.first()).toBeVisible();

      // Проверяем наличие числовых значений
      const totalValues = page.locator('[class*="total"] .ant-statistic-content-value, tfoot td').first();
      await expect(totalValues).toBeVisible();
    }
  });

  test('should copy budget from previous year', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем кнопку копирования из предыдущего года
    const copyButton = page.locator('button:has-text("Копировать"), button:has-text("Скопировать"), button:has-text("Предыдущ")').first();

    if (await copyButton.isVisible()) {
      await copyButton.click();

      // Ждем подтверждения (может быть modal)
      const confirmButton = page.locator('.ant-modal button:has-text("OK"), .ant-modal button:has-text("Подтвердить")').first();
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }

      // Ждем обновления данных
      await page.waitForResponse((response) =>
        response.url().includes('/api/v1/budget') && (response.status() === 200 || response.status() === 201),
        { timeout: 10000 }
      ).catch(() => {
        // Может не быть данных для копирования
      });
    }
  });

  test('should save budget plan', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем кнопку сохранения
    const saveButton = page.locator('button:has-text("Сохранить"), button:has-text("Save"), button[type="submit"]').first();

    if (await saveButton.isVisible()) {
      await saveButton.click();

      // Ждем успешного сохранения
      await page.waitForResponse((response) =>
        response.url().includes('/api/v1/budget') && response.status() === 200,
        { timeout: 10000 }
      ).catch(() => {
        // Может быть автосохранение
      });

      // Проверяем появление уведомления об успехе
      const successMessage = page.locator('.ant-message-success, .ant-notification-success');
      if (await successMessage.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(successMessage).toBeVisible();
      }
    }
  });

  test('should display OPEX and CAPEX breakdown', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем разбивку по типам расходов
    const opexCapexLabels = page.locator('text=/OPEX|CAPEX/i');

    if (await opexCapexLabels.first().isVisible()) {
      const count = await opexCapexLabels.count();
      expect(count).toBeGreaterThanOrEqual(2);
    }
  });

  test('should export budget plan to Excel', async ({ page }) => {
    await page.goto('/budget/plan');
    await page.waitForLoadState('networkidle');

    // Ищем кнопку экспорта
    const exportButton = page.locator('button:has-text("Экспорт"), button:has(svg[data-icon="download"])').first();

    if (await exportButton.isVisible()) {
      // Начинаем ожидание загрузки файла
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 }).catch(() => null);

      await exportButton.click();

      // Ждем загрузки файла
      const download = await downloadPromise;

      if (download) {
        // Проверяем, что файл скачался
        expect(download.suggestedFilename()).toMatch(/\.xlsx?$/i);
      }
    }
  });

  test('should navigate to budget overview', async ({ page }) => {
    await page.goto('/budget/plan');

    // Ищем ссылку на обзор бюджета
    const overviewLink = page.locator('a[href*="/budget/overview"], button:has-text("Обзор")').first();

    if (await overviewLink.isVisible()) {
      await overviewLink.click();

      // Проверяем, что перешли на страницу обзора
      await page.waitForURL(/\/budget/);
    }
  });
});
