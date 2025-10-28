import { test, expect } from '@playwright/test';
import { TEST_CREDENTIALS, login, loginAsAdmin, logout, isLoggedIn } from './helpers/auth';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Очищаем localStorage перед каждым тестом
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should display login page', async ({ page }) => {
    await page.goto('/login');

    // Проверяем наличие формы логина
    await expect(page.locator('h1, h2, .login-title')).toContainText(/Вход|Авторизация|Login/i);
    await expect(page.locator('input[name="username"], input[id="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"], input[id="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await login(page, TEST_CREDENTIALS.admin.username, TEST_CREDENTIALS.admin.password);

    // Проверяем, что редирект произошел и мы на главной странице
    await expect(page).toHaveURL('/');

    // Проверяем, что пользователь залогинен (видно меню пользователя или дашборд)
    const loggedIn = await isLoggedIn(page);
    expect(loggedIn).toBe(true);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="username"], input[id="username"]', 'invaliduser');
    await page.fill('input[name="password"], input[id="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Ждем сообщения об ошибке (может быть в notification или alert)
    await expect(
      page.locator('.ant-message-error, .ant-notification-error, .error-message')
    ).toBeVisible({ timeout: 5000 });
  });

  test('should logout successfully', async ({ page }) => {
    // Сначала логинимся
    await loginAsAdmin(page);

    // Проверяем, что залогинены
    expect(await isLoggedIn(page)).toBe(true);

    // Выходим
    await logout(page);

    // Проверяем, что вышли и на странице логина
    await expect(page).toHaveURL('/login');
  });

  test('should redirect to login when accessing protected route', async ({ page }) => {
    // Пытаемся перейти на защищенную страницу без авторизации
    await page.goto('/expenses');

    // Должен произойти редирект на /login
    await page.waitForURL('/login', { timeout: 5000 });
    await expect(page).toHaveURL('/login');
  });

  test('should persist session after page reload', async ({ page }) => {
    // Логинимся
    await loginAsAdmin(page);

    // Проверяем, что залогинены
    expect(await isLoggedIn(page)).toBe(true);

    // Перезагружаем страницу
    await page.reload();

    // Проверяем, что все еще залогинены (токен в localStorage)
    expect(await isLoggedIn(page)).toBe(true);
    await expect(page).toHaveURL('/');
  });

  test('should clear session on logout', async ({ page }) => {
    // Логинимся
    await loginAsAdmin(page);

    // Выходим
    await logout(page);

    // Проверяем, что токен удален из localStorage
    const token = await page.evaluate(() => localStorage.getItem('token'));
    expect(token).toBeNull();
  });
});
