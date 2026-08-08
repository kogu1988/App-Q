"use client";

import { useState } from "react";
import { useClientPlan } from "@/hooks/use-client-plan";
import { toast } from "sonner";
import {
  Check, Zap, ArrowLeft, CreditCard, Shield,
  Sparkles, Building2, ChevronRight, Lock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

// ─── Plan Data ────────────────────────────────────────────────────────────────

const PLANS = [
  {
    key: "Free",
    name: "Free Trial",
    monthlyPrice: 0,
    annualPrice: 0,
    description: "Sistem özelliklerini denemek için",
    color: "border-[#d9d9dd]",
    badge: null,
    features: [
      "3 günlük ücretsiz deneme",
      "Toplam 2 adet araştırma hakkı",
      "İstediğiniz kadar persona (maks 10)",
      "Persona sohbetlerini izleme",
      "Temel Rapor (Adversarial Review & RFI Skoru)",
    ],
    locked: [
      "Araştırma raporları (Paywall/Blur)",
      "Takip sorusu (probing) sorma",
      "Özel mülakat sorusu ekleme",
      "A/B Test simülasyonları",
    ],
  },
  {
    key: "Flex",
    name: "Research Pack (Esnek)",
    monthlyPrice: 1990,
    annualPrice: 1990,
    description: "Taahhüt vermeden tek seferlik paket arayanlar için",
    color: "border-[#b8b7b3]",
    badge: "Tek Seferlik",
    features: [
      "Süre sınırı yoktur (Ömür boyu kullanım)",
      "Toplam 3 adet araştırma hakkı",
      "A/B Test simülasyonları dahil",
      "Araştırma başına 3 takip sorusu",
      "RFI, Adversarial & SES Cross-tab",
    ],
    locked: [
      "White-label (Markasız raporlar)",
      "B2B persona modu",
    ],
  },
  {
    key: "Starter",
    name: "Starter",
    monthlyPrice: 2690,
    annualPrice: 2150, // ~20% discount
    description: "Büyüyen ekipler ve danışmanlar için ideal",
    color: "border-[#003c33]",
    badge: "En Popüler",
    features: [
      "Ayda 10 araştırma hakkı",
      "Maks 10 persona",
      "A/B Test simülasyonları dahil",
      "Mülakat taslağı iyileştirme",
      "Araştırma başına 3 takip sorusu (probing)",
      "Araştırma başına 2 'Araştırmayla Konuş'",
      "PDF rapor export & SES cross-tab tablosu",
      "Gerçek zamanlı stream & RFI Skoru",
      "3 günlük ücretsiz deneme",
    ],
    locked: [
      "White-label (Markasız raporlar)",
      "Sınırsız araştırma/takip",
      "B2B persona modu",
    ],
  },
  {
    key: "Pro",
    name: "Pro",
    monthlyPrice: 6790,
    annualPrice: 5430, // ~20% discount
    description: "Ajanslar ve profesyonel araştırmacılar için",
    color: "border-[#ff7759]",
    badge: "Önerilen",
    features: [
      "Sınırsız araştırma sayısı",
      "Sınırsız takip sorusu (probing)",
      "Sınırsız 'Araştırmayla Konuş'",
      "White-label (Markasız/Özel logolu) raporlar",
      "B2B persona modu",
      "Marka Sağlığı analizi",
      "3 günlük ücretsiz deneme",
    ],
    locked: [],
  },
  {
    key: "Enterprise",
    name: "Enterprise",
    monthlyPrice: 51000,
    annualPrice: 40800,
    description: "Büyük ölçekli AI destekli araştırmalar için",
    color: "border-[#17171c]",
    badge: "Kurumsal",
    features: [
      "Sınırsız her şey & custom metodolojiler",
      "%100 Yerel Veri Lokalizasyonu (2026 KVKK Uyumlu)",
      "Çok kullanıcılı organizasyon & audit log",
      "Özel entegrasyonlar ve API erişimi",
      "Atanmış müşteri başarı temsilcisi",
      "PDF export & SES cross-tab",
      "7/24 Öncelikli destek",
    ],
    locked: [],
  },
];

// ─── Upgrade Page ─────────────────────────────────────────────────────────────

export default function UpgradePage() {
  const { plan, loading } = useClientPlan();
  const [billing, setBilling] = useState<"monthly" | "annual">("monthly");
  const [selected, setSelected] = useState<string | null>(null);
  const [step, setStep] = useState<"select" | "confirm" | "done">("select");
  const [upgrading, setUpgrading] = useState(false);

  const currentPlan = plan.plan_type;

  const handleSelect = (planKey: string) => {
    if (planKey === currentPlan) return;
    const planOrder = ["Free", "Flex", "Starter", "Pro", "Enterprise"];
    if (planOrder.indexOf(planKey) <= planOrder.indexOf(currentPlan)) return;
    setSelected(planKey);
    setStep("confirm");
  };

  const handleUpgrade = async () => {
    if (!selected) return;
    setUpgrading(true);
    const username = typeof window !== "undefined" ? localStorage.getItem("clarere_username") : null;
    if (!username) {
      toast.error("Kullanıcı oturumu bulunamadı.");
      setUpgrading(false);
      return;
    }
    try {
      const res = await fetch("/api/client/upgrade-plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Username": username,
        },
        body: JSON.stringify({ new_plan: selected, billing_cycle: billing }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || "Plan güncellenemedi.");
      }
      setStep("done");
      // Force plan refresh
      setTimeout(() => {
        window.location.href = "/client";
      }, 2500);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bir hata oluştu.");
    } finally {
      setUpgrading(false);
    }
  };

  const selectedPlan = PLANS.find(p => p.key === selected);

  // ── Done ──
  if (step === "done") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8 text-center animate-in fade-in duration-500">
        <div className="h-16 w-16 rounded-full bg-[#edfce9] flex items-center justify-center mb-6 shadow-sm">
          <Check size={32} className="text-[#003c33]" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-[#17171c] mb-2">
          Plan Güncellendi!
        </h2>
        <p className="text-muted-foreground mb-2">
          <span className="font-semibold text-[#003c33]">{selected}</span> planına geçildi.
        </p>
        <p className="text-sm text-muted-foreground">Dashboard&apos;a yönlendiriliyorsunuz...</p>
      </div>
    );
  }

  // ── Confirm Step ──
  if (step === "confirm" && selectedPlan) {
    const isFlex = selectedPlan.key === "Flex";
    const price = isFlex ? selectedPlan.monthlyPrice : (billing === "annual" ? selectedPlan.annualPrice : selectedPlan.monthlyPrice);
    const saving = !isFlex && selectedPlan.monthlyPrice > 0
      ? Math.round((1 - selectedPlan.annualPrice / selectedPlan.monthlyPrice) * 100)
      : 0;

    return (
      <div className="p-4 sm:p-8 max-w-lg mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
        <button
          onClick={() => setStep("select")}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
        >
          <ArrowLeft size={15} /> Geri dön
        </button>

        <h2 className="text-2xl font-extrabold tracking-tight mb-1">Planı Onayla</h2>
        <p className="text-muted-foreground text-sm mb-8">
          {currentPlan} → <span className="font-semibold text-[#003c33]">{selectedPlan.name}</span>
        </p>

        {/* Order Summary */}
        <div className="rounded-2xl border border-[#d9d9dd] p-5 space-y-4 mb-6 bg-[#f5f4f1]/30">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">{selectedPlan.name} Plan</span>
            {selectedPlan.badge && (
              <Badge className="bg-[#003c33] text-white text-[10px]">{selectedPlan.badge}</Badge>
            )}
          </div>

          {/* Billing Toggle */}
          {!isFlex ? (
            <div className="flex gap-2">
              {(["monthly", "annual"] as const).map(cycle => (
                <button
                  key={cycle}
                  onClick={() => setBilling(cycle)}
                  className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${
                    billing === cycle
                      ? "border-[#17171c] bg-[#17171c] text-white"
                      : "border-[#d9d9dd] text-muted-foreground hover:border-[#17171c]"
                  }`}
                >
                  {cycle === "monthly" ? "Aylık" : "Yıllık"}
                  {cycle === "annual" && saving > 0 && (
                    <span className="ml-1 text-[10px] text-[#ff7759] font-bold">-%{saving}</span>
                  )}
                </button>
              ))}
            </div>
          ) : (
            <div className="py-2.5 px-4 rounded-xl text-xs font-semibold border border-[#b8b7b3] bg-[#b8b7b3]/10 text-amber-800 text-center">
              ⚠️ Bu paket tek seferliktir, abonelik taahhüdü veya yenileme içermez.
            </div>
          )}

          <div className="flex items-end justify-between pt-2 border-t border-[#d9d9dd]">
            <span className="text-muted-foreground text-sm">Tutar</span>
            <div className="text-right">
              <span className="text-2xl font-extrabold text-[#17171c]">
                {price === 0 ? "Ücretsiz" : `₺${price.toLocaleString("tr-TR")}`}
              </span>
              {price > 0 && !isFlex && (
                <span className="text-xs text-muted-foreground ml-1">
                  / {billing === "annual" ? "ay (yıllık fatura)" : "ay"}
                </span>
              )}
              {isFlex && (
                <span className="text-xs text-muted-foreground ml-1 font-semibold">
                  (Tek Seferlik Ödeme)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Features included */}
        <div className="space-y-2 mb-8">
          {selectedPlan.features.map(f => (
            <div key={f} className="flex items-center gap-2 text-sm">
              <Check size={14} className="text-[#003c33] shrink-0" />
              <span>{f}</span>
            </div>
          ))}
        </div>

        {/* Trust badges */}
        <div className="flex gap-4 text-[11px] text-muted-foreground mb-6">
          <div className="flex items-center gap-1"><Shield size={12} /> SSL Güvenli</div>
          <div className="flex items-center gap-1"><Lock size={12} /> KVKK Uyumlu</div>
          <div className="flex items-center gap-1"><CreditCard size={12} /> Kolay Ödeme</div>
        </div>

        <Button
          onClick={handleUpgrade}
          disabled={upgrading}
          className="w-full bg-[#17171c] hover:opacity-85 text-white font-semibold gap-2 h-12 text-base rounded-xl"
        >
          {upgrading ? (
            <>İşleniyor...</>
          ) : (
            <>{selectedPlan.name} Planını Aktifleştir <ChevronRight size={16} /></>
          )}
        </Button>

        <p className="text-center text-xs text-muted-foreground mt-3">
          Demo ortamı — gerçek ödeme alınmaz.
        </p>
      </div>
    );
  }

  // ── Select Plan ──
  return (
    <div className="p-4 sm:p-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="max-w-6xl mx-auto">
        <Link
          href="/client"
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
        >
          <ArrowLeft size={15} /> Dashboard&apos;a dön
        </Link>

        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={18} className="text-[#ff7759]" />
            <h1 className="text-2xl font-extrabold tracking-tight">Planını Yükselt</h1>
          </div>
          <p className="text-muted-foreground text-sm">
            Şu anki planın: <span className="font-semibold text-[#17171c]">{loading ? "..." : currentPlan}</span>
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex flex-wrap items-center gap-3 mb-8 w-full">
          <div className="flex items-center gap-2 bg-[#f5f4f1]/80 p-1 rounded-full border border-[#d9d9dd]">
            {(["monthly", "annual"] as const).map(cycle => (
              <button
                key={cycle}
                onClick={() => setBilling(cycle)}
                className={`px-5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                  billing === cycle
                    ? "bg-[#17171c] text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {cycle === "monthly" ? "Aylık" : "Yıllık"}
                {cycle === "annual" && (
                  <span className="ml-1.5 text-[9px] font-bold text-[#ff7759] bg-[#ff7759]/10 px-1.5 py-0.5 rounded-full">%20 indirim</span>
                )}
              </button>
            ))}
          </div>
          <span className="text-xs text-muted-foreground font-semibold italic">
            * Research Pack (Esnek) abonelik değildir, tek seferlik bir pakettir.
          </span>
        </div>

        {/* Plan Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {PLANS.filter(p => p.key !== "Enterprise").map(p => {
            const planOrder = ["Free", "Flex", "Starter", "Pro", "Enterprise"];
            const isCurrent = p.key === currentPlan;
            const isDowngrade = planOrder.indexOf(p.key) < planOrder.indexOf(currentPlan);
            const isFlex = p.key === "Flex";
            const price = isFlex ? p.monthlyPrice : (billing === "annual" ? p.annualPrice : p.monthlyPrice);
            const disabled = isCurrent || isDowngrade;

            return (
              <button
                key={p.key}
                disabled={disabled}
                onClick={() => handleSelect(p.key)}
                className={`relative flex flex-col text-left p-5 rounded-2xl border-2 transition-all duration-200 ${
                  isCurrent
                    ? "border-[#003c33] bg-[#edfce9]/40 cursor-default"
                    : isDowngrade
                    ? "border-[#d9d9dd] opacity-40 cursor-not-allowed"
                    : selected === p.key
                    ? `${p.color} shadow-lg scale-[1.02]`
                    : `${p.color} hover:shadow-md hover:scale-[1.01]`
                }`}
              >
                {/* Badge */}
                {p.badge && (
                  <span className="absolute top-3 right-3 text-[9px] font-bold px-2 py-0.5 rounded-full bg-[#ff7759] text-white">
                    {p.badge}
                  </span>
                )}
                {isCurrent && (
                  <span className="absolute top-3 right-3 text-[9px] font-bold px-2 py-0.5 rounded-full bg-[#edfce9] text-[#003c33] border border-[#003c33]/30">
                    Mevcut Plan
                  </span>
                )}

                {/* Icon */}
                <div className={`h-8 w-8 rounded-lg flex items-center justify-center mb-3 ${
                  p.key === "Pro" ? "bg-[#fff3f0]" :
                  p.key === "Starter" ? "bg-[#edfce9]" : "bg-[#eeece7]"
                }`}>
                  {p.key === "Pro" ? <Sparkles size={16} className="text-[#ff7759]" /> :
                   p.key === "Starter" ? <Zap size={16} className="text-[#003c33]" /> :
                   <Building2 size={16} className="text-[#616161]" />}
                </div>

                <div className="font-bold text-base mb-0.5">{p.name}</div>
                <div className="text-[11px] text-muted-foreground mb-4 min-h-[32px] leading-tight">{p.description}</div>

                {/* Price */}
                <div className="mb-4">
                  {price === 0 ? (
                    <span className="text-xl font-extrabold">Ücretsiz</span>
                  ) : (
                    <div className="flex items-end gap-1">
                      <span className="text-xl font-extrabold">₺{price.toLocaleString("tr-TR")}</span>
                      <span className="text-[10px] text-muted-foreground mb-0.5 font-semibold">
                        {isFlex ? " / 3 Araştırma" : "/ ay"}
                      </span>
                    </div>
                  )}
                </div>

                {/* Features */}
                <ul className="space-y-1.5 flex-1 mb-4">
                  {p.features.map(f => (
                    <li key={f} className="flex items-start gap-1.5 text-[11px] leading-snug">
                      <Check size={12} className="text-[#003c33] shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                  {p.locked.map(f => (
                    <li key={f} className="flex items-start gap-1.5 text-[11px] leading-snug opacity-40">
                      <Lock size={11} className="shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                {!disabled && (
                  <div className={`mt-auto w-full py-2 rounded-xl text-xs font-semibold text-center transition-all ${
                    p.key === "Pro"
                      ? "bg-[#ff7759] text-white"
                      : "bg-[#17171c] text-white"
                  }`}>
                    {p.name} Seç
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Enterprise CTA */}
        <div className="rounded-2xl border-2 border-[#17171c] p-6 flex flex-col md:flex-row items-start md:items-center justify-between bg-[#f5f4f1]/50 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge className="bg-[#17171c] text-white text-[10px] font-bold">ENTERPRISE</Badge>
              <span className="font-extrabold text-base text-[#17171c]">Kurumsal Çözüm</span>
            </div>
            <p className="text-xs text-muted-foreground leading-tight max-w-xl">
              Sınırsız her şey, custom metodolojiler, özel entegrasyonlar, atanmış destek ekibi ve **%100 Yerel Veri Lokalizasyonu (2026 KVKK Uyumlu)** kurumsal garantisi ile organizasyonunuzu ölçeklendirin.
            </p>
          </div>
          <a
            href="mailto:hello@clarere.com?subject=Enterprise Plan Talebi"
            className="px-5 py-2.5 rounded-xl bg-[#17171c] text-white text-xs font-semibold hover:opacity-85 transition-opacity shrink-0 w-full md:w-auto text-center"
          >
            İletişime Geç (₺51.000 / Ay)
          </a>
        </div>
      </div>
    </div>
  );
}

