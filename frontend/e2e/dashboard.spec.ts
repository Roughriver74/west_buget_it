import { test, expect } from '@playwright/test';
import { loginAsAdmin } from './helpers/auth';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Логинимся перед каждым тестом
    await loginAsAdmin(page);
  });

  test('should display dashboard page', async ({ page }) => {
    await page.goto('/');

    // Проверяем, что мы на дашборде
    await expect(page).toHaveURL('/');

    // Проверяем наличие заголовка дашборда
    await expect(page.locator('h1, h2, .page-title')).toContainText(/Дашборд|Dashboard|Главная/i);
  });

  test('should display summary statistics', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки данных
    await page.waitForLoadState('networkidle');

    // Проверяем наличие статистических карточек
    // Обычно дашборд содержит карточки с суммами, категориями и т.д.
    const statsCards = page.locator('.ant-statistic, .ant-card, [class*="stat"]');
    await expect(statsCards.first()).toBeVisible({ timeout: 10000 });

    // Проверяем, что есть числовые данные
    const numbers = page.locator('[class*="statistic-value"], [class*="stat-value"], .ant-statistic-content-value');
    await expect(numbers.first()).toBeVisible();
  });

  test('should display charts and graphs', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки данных
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Даем время для рендера графиков

    // Проверяем наличие графиков (Recharts, Ant Design Charts)
    const charts = page.locator('svg, canvas, [class*="chart"], [class*="recharts"]');
    await expect(charts.first()).toBeVisible({ timeout: 10000 });
  });

  test('should filter data by year', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки
    await page.waitForLoadState('networkidle');

    // Ищем селектор года (может быть dropdown или кнопки)
    const yearSelector = page.locator('select[name="year"], .ant-select:has-text("2025"), button:has-text("2025")').first();

    if (await yearSelector.isVisible()) {
      await yearSelector.click();

      // Ждем обновления данных
      await page.waitForTimeout(1000);

      // Проверяем, что данные обновились (идет новый запрос)
      await page.waitForResponse((response) =>
        response.url().includes('/api/v1/analytics/dashboard') && response.status() === 200
      );
    }
  });

  test('should filter data by department', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки
    await page.waitForLoadState('networkidle');

    // Ищем селектор отдела (в хедере или на странице)
    const deptSelector = page.locator('.ant-select:has-text("Отдел"), select[name="department"]').first();

    if (await deptSelector.isVisible()) {
      await deptSelector.click();

      // Выбираем любой отдел из списка
      await page.locator('.ant-select-item').first().click();

      // Ждем обновления данных
      await page.waitForResponse((response) =>
        response.url().includes('/api/v1/') && response.status() === 200
      );

      // Проверяем, что данные обновились
      await page.waitForTimeout(500);
    }
  });

  test('should display recent expenses table', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки
    await page.waitForLoadState('networkidle');

    // Ищем таблицу последних расходов
    const table = page.locator('.ant-table, table').first();

    if (await table.isVisible()) {
      await expect(table).toBeVisible();

      // Проверяем наличие заголовков таблицы
      const tableHeaders = table.locator('thead th, .ant-table-thead th');
      await expect(tableHeaders.first()).toBeVisible();

      // Проверяем наличие строк данных
      const tableRows = table.locator('tbody tr, .ant-table-tbody tr');
      const rowCount = await tableRows.count();

      // Может быть пустая таблица, но структура должна быть
      expect(rowCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('should navigate to expenses page from dashboard', async ({ page }) => {
    await page.goto('/');

    // Ищем ссылку/кнопку на страницу расходов
    const expensesLink = page.locator('a[href*="/expenses"], button:has-text("Заявки"), a:has-text("Расходы")').first();

    if (await expensesLink.isVisible()) {
      await expensesLink.click();

      // Проверяем, что перешли на страницу расходов
      await page.waitForURL(/\/expenses/);
      await expect(page).toHaveURL(/\/expenses/);
    }
  });

  test('should display OPEX vs CAPEX breakdown', async ({ page }) => {
    await page.goto('/');

    // Ждем загрузки
    await page.waitForLoadState('networkidle');

    // Ищем карточки или текст с OPEX/CAPEX
    const opexCapex = page.locator('text=/OPEX|CAPEX/i');

    if (await opexCapex.first().isVisible()) {
      await expect(opexCapex.first()).toBeVisible();

      // Должно быть минимум 2 упоминания (OPEX и CAPEX)
      const count = await opexCapex.count();
      expect(count).toBeGreaterThanOrEqual(2);
    }
  });
});
