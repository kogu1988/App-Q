import { test, expect } from '@playwright/test';

/**
 * Oturum (auth) davranışı — LLM çağrısı YOK.
 *
 * Neden ayrı bir paket: `/client` altındaki tüm sayfalar `ClientLayout` içinde
 * yaşar. Bir dönem bu layout, oturum çözülmeden `children`'ı mount ediyordu;
 * alt bileşenler boş kimlikle fetch atıp 401 alıyor ve boş dependency array
 * yüzünden bir daha denemiyordu (abonelik kartı, araştırma geçmişi, kenar
 * çubuğu ve plan bilgisi boş/yanlış kalıyordu). Bu paket o sınıfı kilitler.
 */
test.describe.serial('Oturum akışı', () => {
  test('giriş öncesi kimlik gerektiren veri çağrısı yapılmaz', async ({ page }) => {
    const calls: string[] = [];
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('request', (r) => { if (r.url().includes('/api/')) calls.push(`${r.method()} ${r.url()}`); });
    page.on('response', (r) => { if (r.status() >= 400) calls.push(`HTTP ${r.status()} ${r.url()}`); });

    await page.goto('/client', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1200);
    await expect(page.locator('#username-input')).toBeVisible();

    const authCalls = calls.filter((c) => /\/(client\/(me|studies)|billing\/)/.test(c));
    expect(authCalls, 'giriş öncesi kimlik gerektiren çağrı olmamalı').toEqual([]);
    expect(errors, 'giriş öncesi konsol hatası olmamalı').toEqual([]);
  });

  test('giriş sonrası panel dolu gelir (geçmiş, plan)', async ({ page }) => {
    await page.goto('/client', { waitUntil: 'networkidle' });
    await page.locator('#username-input').fill('pro');
    await page.getByRole('button', { name: /^Başla/ }).click();
    await expect(page.locator('#username-input')).toBeHidden({ timeout: 30_000 });
    await page.waitForTimeout(2500);

    const body = await page.locator('body').innerText();
    // pro kullanıcısının araştırması ("BuddyNote") geçmişte görünmeli
    expect(body, 'araştırma geçmişi dolu olmalı').toMatch(/BuddyNote/);
    expect(body, 'boş geçmiş mesajı görünmemeli').not.toMatch(/Henüz bir araştırma bulunmuyor/);
    // plan bilgisi giriş sonrası doğru okunmalı
    expect(body, 'plan etiketi doğru olmalı').toMatch(/Pro/);
  });
});
