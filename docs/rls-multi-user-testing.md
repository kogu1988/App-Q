# RLS & Multi-User Test Checklist

> `studies` tablosuna eklenen tenant/org RLS entegrasyonunu doğrulamak için.
> Bu değişiklikler gerçek DB'de test edilmemiştir (commit `a17cf9d`).

## Ön Koşul

```powershell
docker compose up -d postgres redis
python launch.py
```

Backend `:4000`, frontend `:4001`. Test kullanıcıları: `free`, `flex`, `starter`, `pro`, `enterprise`.

---

## 1. Tenant İzolasyonu (studies)

**Amaç:** Bir kullanıcı başka kullanıcının çalışmalarını görmemeli.

1. `X-Username: free` header ile bir araştırma oluştur (client `/studies` POST).
2. `X-Username: pro` header ile `GET /api/client/studies` çağır.
3. **Beklenen:** `pro` kullanıcısı `free`'nin çalışmasını GÖRMEMELİ.
4. `X-Username: free` ile tekrar `GET /api/client/studies`.
5. **Beklenen:** `free` kendi çalışmasını görmeli.

> ⚠️ Legacy çalışmalar (`created_by IS NULL OR ''`) herkese görünür — bu bilinçli geriye dönük uyumluluk. Yeni çalışmalar tenant'a bağlanır.

## 2. Multi-User Org Paylaşımı

**Amaç:** Aynı organizasyondaki kullanıcılar birbirinin çalışmalarını paylaşmalı.

1. Admin olarak org oluştur (admin anahtarı `X-Admin-Key` header'ında):
   ```http
   POST /api/admin/organizations
   {"org_id": "org_test", "name": "Test Org", "owner_username": "pro"}
   ```
2. İkinci üye ekle:
   ```http
   POST /api/admin/organizations/members
   {"org_id": "org_test", "username": "enterprise", "role": "member"}
   ```
3. `X-Username: pro` ile araştırma oluştur → `org_id=org_test` otomatik bağlanmalı (`create_or_update_study` bunu yapar).
4. `X-Username: enterprise` ile `GET /api/client/studies`.
5. **Beklenen:** `enterprise`, `pro`'nun org çalışmasını GÖRMELİ (RLS `org_id = current_org` sayesinde).
6. `X-Username: free` (org üyesi değil) ile `GET /api/client/studies`.
7. **Beklenen:** `free` bu çalışmayı GÖRMEMELİ.

## 3. Veritabanı Doğrulaması

```sql
-- RLS politikasının varlığı
SELECT policyname, tablename FROM pg_policies WHERE tablename = 'studies';
-- Beklenen: studies_tenant_policy

-- Yeni kolonlar
SELECT column_name FROM information_schema.columns WHERE table_name = 'studies';
-- Beklenen: created_by, org_id mevcut

-- Organizasyon tabloları
SELECT * FROM organizations;
SELECT * FROM organization_members;
```

## 4. Hata Senaryoları

- **Org tablosu yokken get_db:** `clarere.current_org` sorgusu try/except içinde → sessizce geçmeli, istek normal çalışmalı.
- **Anonymous (header yok):** kendi çalışmaları (`created_by=''`) görünmeli; RLS çökmemeli.

## Başarısızlık Belirtileri

- `GET /studies` boş liste dönüyorsa: RLS çok kısıtlayıcı → `studies_tenant_policy`'yi kontrol et.
- `GET /studies` herkese her şeyi döndürüyorsa: RLS aktif değil → `ALTER TABLE studies ENABLE ROW LEVEL SECURITY` çalıştı mı kontrol et.
