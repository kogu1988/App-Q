import { Page, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const ART = path.join(__dirname, 'artifacts', 'screens');

/** Ekran görüntüsü al ve yolunu logla. */
export async function shot(page: Page, name: string): Promise<void> {
  fs.mkdirSync(ART, { recursive: true });
  const file = path.join(ART, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`  [shot] artifacts/screens/${name}.png`);
}

/**
 * Kullanıcı adı modalından giriş yapar.
 * Dev modunda parola opsiyoneldir (X-Username header'ı).
 */
export async function login(page: Page, username: string): Promise<void> {
  await page.goto('/client');
  const input = page.locator('#username-input');
  await expect(input).toBeVisible({ timeout: 30_000 });
  await input.fill(username);
  // Modal'daki giriş butonu `type="button"` (form submit değil) → click gerekir.
  await page.getByRole('button', { name: /^Başla/ }).click();
  await expect(input).toBeHidden({ timeout: 30_000 });
}

/** Sohbet yanıtı tamamlanana kadar bekler (textarea tekrar aktif olur). */
export async function waitIntakeIdle(page: Page, timeout = 240_000): Promise<void> {
  const ta = page.getByPlaceholder(/Yanıtınızı yazın/);
  await expect(ta).toBeEnabled({ timeout });
}
