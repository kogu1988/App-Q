import { test, expect } from '@playwright/test';
import { login, shot, waitIntakeIdle } from '../helpers';

/**
 * Uçtan uca araştırma akışı (gerçek DeepSeek çağrıları).
 *
 * Kapsam: Defne brief → araştırma (plan + 5 persona + batch mülakat) →
 * çalışma detayı → transkriptler → sentez raporu → kanıt zinciri.
 *
 * NOT: Çalışma süresi ve token maliyeti nedeniyle `pro` (sınırsız) kullanılır.
 */
test.describe.serial('Araştırma akışı (pro)', () => {
  test('Defne → personalar → mülakat → sentez raporu', async ({ page }) => {
    test.setTimeout(1_200_000);

    await login(page, 'pro');
    await page.goto('/client/new');

    // 1) Mod seç → Defne ile başla
    await page.getByRole('button', { name: /Defne ile Başla/ }).click();
    const ta = page.getByPlaceholder(/Yanıtınızı yazın/);
    await expect(ta).toBeVisible({ timeout: 30_000 });
    await shot(page, '10-defne-greeting');

    // 2) Fikri anlat
    const idea = [
      'Evcil hayvan sahipleri için premium bir mobil takip ve yönetim uygulaması düşünüyorum. Adı BuddyNote.',
      'Köpek, kedi, kuş ve tavşan sahiplerinin aşı takvimini, veteriner belgelerini, günlük rutinlerini',
      've masraflarını tek bir yerde toplayan, estetik ve yapay zeka destekli bir merkez.',
      'Sorun: bu bilgiler veteriner karnesi, telefon notları ve dağınık uygulamalar arasında kayboluyor,',
      'sahiplerini strese sokuyor. Hedef kitle: 25-45 yaş, şehirli, evcil hayvanını ailesinden sayan,',
      'dijital araçlara açık kullanıcılar. Fiyat: ücretsiz (reklamlı-kısıtlı) ve premium (reklamsız-kısıtsız)',
      'aylık 24.99 dolar, yıllık ödemede indirim. Rakipler: 11pets, PetDesk, Waggle.',
      'Başarı kriteri: premium dönüşüm oranı ve 30 günlük elde tutma.',
    ].join(' ');

    await ta.fill(idea);
    await ta.press('Enter');
    await waitIntakeIdle(page);
    await shot(page, '11-defne-turn1');

    const answers = [
      'Başarı kriteri: ilk 6 ayda 1.000 indirme ve 100 ödeyen kullanıcı. Fiyatı Türkiye pazarı için TL karşılığı olarak düşünüyorum, aylık yaklaşık 1000 TL. Yıllık ödemede indirim olsun.',
      'Panel 5 persona olsun, bütçe standart. Araştırma Türkiye geneli, büyükşehirler önceliğiyle olsun. Bu bilgiler yeterliyse araştırmayı başlatabiliriz.',
      'Evet, brief tamam. Araştırmayı başlatabiliriz.',
      'Brief tamam, onaylıyorum. Başlayalım.',
      'Onaylıyorum, araştırmayı başlat.',
    ];

    for (let i = 0; i < answers.length; i++) {
      if ((await page.getByText('Brief hazır!').count()) > 0) break;
      await ta.fill(answers[i]);
      await ta.press('Enter');
      await waitIntakeIdle(page);
      await shot(page, `12-defne-turn${i + 2}`);
    }

    const briefReady = (await page.getByText('Brief hazır!').count()) > 0;
    if (!briefReady) await shot(page, '13-brief-NOT-ready');
    expect(briefReady, 'Defne brief tamamlanmadı').toBeTruthy();

    // 3) Araştırmayı başlat → simulating → study
    await page.getByRole('button', { name: /Araştırmayı Başlat/ }).click();
    await page.waitForURL(/\/client\/studies\//, { timeout: 900_000 });
    await page.waitForLoadState('networkidle').catch(() => {});

    // Çalışma detayı yüklendi mi? (sekmeler görünür olmalı)
    const personasTab = page.getByRole('button', { name: /^Personalar \(\d+\)/ });
    await expect(personasTab).toBeVisible({ timeout: 180_000 });
    await shot(page, '14-study-overview');

    // 4) Personalar sekmesi (Big Five, SES, stance)
    await personasTab.click();
    await page.waitForTimeout(2000);
    await expect(page.getByText(/Sentetik Kitle Paneli/)).toBeVisible({ timeout: 30_000 });
    await shot(page, '15-personas');

    // 5) Mülakat transkriptleri
    const transcriptTab = page.getByRole('button', { name: /^Mülakat Kayıtları \(\d+\)/ });
    if (await transcriptTab.count()) {
      await transcriptTab.click();
      await page.waitForTimeout(2000);
      await shot(page, '16-transcripts');
      // İlk transkripti aç
      const openBtn = page.getByRole('button', { name: /Mülakat Kayıtlarını İncele/ }).first();
      if (await openBtn.count()) {
        await openBtn.click();
        await page.waitForTimeout(1500);
        await shot(page, '17-transcript-dialog');
        await page.keyboard.press('Escape');
        await page.waitForTimeout(800);
      }
    }

    // 6) Sentez raporu (buton metni ASCII: "Raporu Olustur")
    const rapBtn = page.getByRole('button', { name: /Raporu Ol/ }).first();
    if (await rapBtn.count()) {
      await rapBtn.click();
      await page.waitForTimeout(2000);
      await shot(page, '18-synthesizing');
      await page.waitForTimeout(3000);
      await shot(page, '19-after-synthesize');
    } else {
      await shot(page, '19-report-already-exists');
    }

    // 7) Kanıt zinciri + sentez raporu sekmeleri
    const evTab = page.getByRole('button', { name: /^Kanıt Zinciri/ });
    if (await evTab.count()) {
      await evTab.click();
      await page.waitForTimeout(2500);
      await shot(page, '20-evidence-chain');
    }

    const repTab = page.getByRole('button', { name: /^Sentez Raporu/ });
    if (await repTab.count()) {
      await repTab.click();
      await page.waitForTimeout(2500);
      await shot(page, '21-report-tab');
    }
  });
});
