import { test, expect } from '@playwright/test';
import { login, shot } from '../helpers';

/**
 * UI akışları — LLM çağrısı YOK, hızlı duman testi.
 */
test.describe.serial('UI akışları', () => {
  test('landing sayfası yüklenir', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Clarere/i);
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible();
    // Bilinen bir CTA / metin
    await expect(page.getByText(/Clarere|sentetik/i).first()).toBeVisible();
    await shot(page, '01-landing');
  });

  test('pro kullanıcısı giriş yapar, dashboard açılır', async ({ page }) => {
    await login(page, 'pro');
    await expect(page.getByRole('link', { name: /Yeni Araştırma/i }).first()).toBeVisible();
    await expect(page.getByText(/Yeni Araştırma Başlat/).first()).toBeVisible();
    await shot(page, '02-dashboard-pro');
  });

  test('yeni (Free) kullanıcı oluşturulur ve paywall görünür', async ({ page }) => {
    const uname = 'f' + String(Date.now()).slice(-8);
    console.log(`  [free-user] ${uname}`);
    await login(page, uname);
    await expect(page.getByRole('link', { name: /Yeni Araştırma/i }).first()).toBeVisible();
    await shot(page, '03-dashboard-free-new');

    await page.goto('/client/upgrade');
    await expect(page.getByText(/Pro|Starter|Yükselt/i).first()).toBeVisible({ timeout: 30_000 });
    await shot(page, '04-upgrade');
  });

  test('admin paneli açılır (dev: korumasız)', async ({ page }) => {
    await page.goto('/admin');
    await expect(page.getByText(/Müşteri|Yönetim|Admin|Kullanıcı/i).first()).toBeVisible({
      timeout: 30_000,
    });
    await shot(page, '05-admin');
  });

  test('admin sekmeleri geçiş yapar (R3 refaktörü)', async ({ page }) => {
    await page.goto('/admin');
    await expect(page.getByText(/Yönetici Paneli/i).first()).toBeVisible({ timeout: 30_000 });

    const tabs: Array<[string, RegExp]> = [
      ['Danışanlar', /Danışan|Kullanıcı|plan/i],
      ['Yapılandırma', /Model|Yapılandırma|Kaydet/i],
      ['Personalar', /Persona|havuz/i],
      ['Soru Koleksiyonu', /soru/i],
      ['Geri Bildirimler', /geri bildirim|Beğeni|Kayıt/i],
      ['Denetim Kayıtları', /Denetim|kayıt/i],
      ['Ajan Şablonları', /şablon|Soru|brief/i],
      ['Metrikler', /Metrik|Toplam|Panel/i],
      ['Maliyet', /Maliyet|token|USD|\$/i],
    ];

    for (const [tab, expected] of tabs) {
      await page.getByRole('tab', { name: new RegExp(tab) }).click();
      await expect(page.getByText(expected).first()).toBeVisible({ timeout: 30_000 });
    }
  });
});
