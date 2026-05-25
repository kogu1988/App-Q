# Enterprise SaaS Dönüşüm Planı (App-Q)

## 📌 Hedef
Mevcut App-Q pazar araştırması platformunu, 6 adet yapısal teknik borcu kapatarak kurumsal ölçekte hizmet verebilecek (Enterprise SaaS) güvenli, izlenebilir ve ölçeklenebilir bir yapıya dönüştürmek.

---

## 🛑 Sokratik Kapı Kararları

Kullanıcının 25 Mayıs 2026 tarihli talebi doğrultusunda şu kararlar alınmıştır:

1. **Güvenlik ve İzolasyon:** Kesinlikle Namespace (Koleksiyon) kullanılacak. Veritabanı seviyesinde `pgvector` tercih edilerek Row-Level Security (RLS) ile B2B izolasyonu (Tam Açık Kaynak) sağlanacak. Pinecone bırakıldı.
2. **Gözlemlenebilirlik (Tracing):** %100 açık kaynak kodlu ve limitsiz **Langfuse** (Self-hosted) kullanılacak.
3. **Gerçeklik Bağı (Web Search):** Tavily/Exa yerine açık kaynak **SearXNG** (Arama) ve **Crawl4AI** (Okuma/Kazıma) kullanılacak.
4. **Altyapı (vLLM):** Monolitik backend yerine vLLM, `docker-compose` üzerinde bağımsız bir mikroservis (vllm-server) olarak ayağa kaldırılacak.

---

## 🛠️ Uygulama Planı (Fazlar ve Görevler)

### Faz 1: B2B Veri İzolasyonu ve Güvenlik (En Kritik)
*Müşteri verilerinin güvenliği ve prompt injection koruması sağlanacak.*
- `[ ]` `db_vectors.py` güncellenecek: Her vektör kaydına zorunlu `tenant_id` eklenecek ve sorgularda strict metadata filtrelemesi uygulanacak.
- `[ ]` `intake.py` güncellenecek: Kullanıcıdan gelen brief metinlerini zararlı girdilere karşı analiz edecek bir "Guardrail" (Llama Guard / NeMo) katmanı API'si eklenecek.

### Faz 2: Hata Toleransı ve LLMOps (Stabilite)
*Simülasyon çökmelerine karşı dayanıklılık ve ajan akışlarının görsel takibi.*
- `[ ]` `state.py` ve `workflow.py` güncellenecek: LangGraph akışına `PostgresSaver` veya `MemorySaver` (Checkpointer) entegre edilecek.
- `[ ]` Ajan döngüleri için "Max Retries" (Circuit Breaker) mekanizması eklenecek.
- `[ ]` `engine.py` güncellenecek: LangSmith/Langfuse callback'leri eklenerek ajanlar arası tüm diyalogların merkezi loglanması sağlanacak.

### Faz 3: Demografik Motor ve İnternet Erişimi (Veri Kalitesi)
*Gerçek dünya verileriyle simülasyon isabetini artırmak.*
- `[ ]` `persona_generator.py` güncellenecek: Sadece prompt bazlı değil, deterministik kural tabanlı bir "Stratification Engine" (TÜİK Dağılım Algoritması) yazılacak (Yaş, SES, Cinsiyet kotaları uygulanacak).
- `[ ]` `engine.py` güncellenecek: Ajan yeteneklerine (Tool Binding) `TavilySearch` veya eşdeğeri bir Web Arama aracı eklenecek, böylece güncel fiyat ve piyasa araştırması yapabilecekler.

### Faz 4: Ölçeklenebilir Çıkarım (Inference) Darboğazı
*On-Premise kurulumlar için eşzamanlı lokal LLM hızlandırma.*
- `[ ]` `packages/research_engine/providers/` dizinine yeni bir `VLLMProvider` sınıfı eklenecek.
- `[ ]` OpenAI API standartlarında çalışan vLLM/SGLang sunucularına bağlanmak üzere gerekli asenkron batching endpoint'leri kurgulanacak.

---

## ✅ Doğrulama Planı (Verification)
- Yeni bir Tenant ile giriş yapılıp RAG üzerinden diğer Tenant'ın verilerine erişilemediği (`Tenant Isolation`) doğrulanacak.
- Uzun süren bir ajan akışı bilinçli olarak crash edilip, sistemin kaldığı Node'dan (`Checkpointing`) yeniden başladığı test edilecek.
- Tavily tool'u ile ajana "Güncel altın fiyatı nedir?" sorusu sorulup internetten anlık veri çekebildiği doğrulanacak.
- TÜİK motoruyla 1000 persona üretilip, yaş/cinsiyet demografik dağılımının %99 isabetle sağlandığı ölçülecek.
