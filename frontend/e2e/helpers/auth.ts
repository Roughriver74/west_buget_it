import { Page } from '@playwright/test';

/**
 * Тестовые учетные данные
 */
export const TEST_CREDENTIALS = {
  admin: {
    username: 'admin',
    password: 'admin',
  },
  // Можно добавить больше пользователей для разных ролей
};

/**
 * Логин пользователя через UI
 */
export async function login(page: Page, username: string, password: string) {
  await page.goto('/login');

  await page.fill('input[name="username"], input[id="username"]', username);
  await page.fill('input[name="password"], input[id="password"]', password);

  await page.click('button[type="submit"]');

  // Ждем редиректа на главную страницу
  await page.waitForURL('/');
}

/**
 * Логин админа
 */
export async function loginAsAdmin(page: Page) {
  await login(page, TEST_CREDENTIALS.admin.username, TEST_CREDENTIALS.admin.password);
}

/**
 * Проверка, что пользователь залогинен
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  try {
    // Проверяем наличие элемента, который виден только залогиненным пользователям
    const userMenu = page.locator('[data-testid="user-menu"], .user-menu, .ant-dropdown-trigger').first();
    await userMenu.waitFor({ timeout: 2000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Логаут
 */
export async function logout(page: Page) {
  // Клик по меню пользователя
  await page.click('[data-testid="user-menu"], .user-menu, .ant-dropdown-trigger');

  // Ждем появления меню
  await page.waitForSelector('.ant-dropdown-menu', { state: 'visible' });

  // Клик по кнопке выхода
  await page.click('text=Выход, text=Выйти, text=Logout');

  // Ждем редиректа на страницу логина
  await page.waitForURL('/login');
}
