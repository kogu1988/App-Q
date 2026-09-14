import { test, expect } from '@playwright/test';
import { login, shot } from '../helpers';

/**
 * Çalışma detayı etkileşimleri — mevcut (en son) çalışma üzerinde.
 * Amaç: yeni intake/araştırma maliyeti olmadan sentez + sekmeleri doğrulamak.
 * NOT: Bu test `02-research-flow` sonrası çalıştırılmalı (bir çalışma olmalı).
 */
test.describe.serial('Çalışma detayı (pro, mevcut çalışma)', () => {
  test('sekmeler + transkript + sentez raporu', async ({ page }) => {
    test.setTimeout(600_000);

    await login(page, 'pro');

    const res = await page.request.get('/api/client/studies', {
      headers: { 'X-Username': 'pro' },
    });
    expect(res.ok()).toBeTruthy();
    const studies = await res.json();
    expect(studies.length, 'pro kullanıcısının çalışması yok — önce 02 çalıştırın').toBeGreaterThan(0);

    const study = studies[0];
    console.log(`  [study] ${study.id} — ${study.title} (has_report=${study.has_report})`);

    await page.goto(`/client/studies/${study.id}`);
    const personasTab = page.getByRole('button', { name: /^Personalar \(\d+\)/ });
    await expect(personasTab).toBeVisible({ timeout: 60_000 });
    await shot(page, '30-overview');

    // Personalar (Big Five / SES / stance)
    await personasTab.click();
    await page.waitForTimeout(2000);
    await expect(page.getByText(/Sentetik Kitle Paneli/)).toBeVisible({ timeout: 30_000 });
    await shot(page, '31-personas');

    // Mülakat kayıtları + transkript dialog
    const tTab = page.getByRole('button', { name: /^Mülakat Kayıtları \(\d+\)/ });
    if (await tTab.count()) {
      await tTab.click();
      await page.waitForTimeout(2000);
      await shot(page, '32-transcripts');
      const openBtn = page.getByRole('button', { name: /Mülakat Kayıtlarını İncele/ }).first();
      if (await openBtn.count()) {
        await openBtn.click();
        await page.waitForTimeout(1500);
        await shot(page, '33-transcript-dialog');
        await page.keyboard.press('Escape');
        await page.waitForTimeout(800);
      }
    }

    // Sentez
    const rapBtn = page.getByRole('button', { name: /Raporu Ol/ }).first();
    if (await rapBtn.count()) {
      await rapBtn.click();
      await page.waitForTimeout(3000);
      await shot(page, '34-synthesizing');
      // Rapor oluşana kadar bekle (buton kaybolur veya rapor sekmesi dolar)
      await page.waitForTimeout(5000);
      await shot(page, '35-after-synthesize');
    } else {
      await shot(page, '35-report-already-exists');
    }

    // Kanıt zinciri
    const evTab = page.getByRole('button', { name: /^Kanıt Zinciri/ });
    if (await evTab.count()) {
      await evTab.click();
      await page.waitForTimeout(2500);
      await shot(page, '36-evidence-chain');
    }

    // Sentez raporu
    const repTab = page.getByRole('button', { name: /^Sentez Raporu/ });
    if (await repTab.count()) {
      await repTab.click();
      await page.waitForTimeout(2500);
      await shot(page, '37-report-tab');
    }
  });

  test('persona kartından gelen odak, ilgili mülakat kartını vurgular', async ({ page }) => {
    await login(page, 'pro');

    const res = await page.request.get('/api/client/studies', {
      headers: { 'X-Username': 'pro' },
    });
    const studies = await res.json();
    const study = studies[0];

    await page.goto(`/client/studies/${study.id}`);
    await page.getByRole('button', { name: /^Personalar \(\d+\)/ }).click();
    await page.waitForTimeout(1200);

    // İkinci persona kartındaki "İncele" → Mülakat sekmesinde 2. kart vurgulanır.
    const jump = page.getByRole('button', { name: /Mülakat Kayıtlarını İncele/ });
    await expect(jump.nth(1)).toBeVisible({ timeout: 30_000 });
    await jump.nth(1).click();
    await page.waitForTimeout(2000);

    await expect(page.locator('[data-interview-index="1"].ring-2')).toHaveCount(1);
    await shot(page, '38-transcript-focus');
  });
});
