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
    name: "Free",
    monthlyPrice: 0,
    annualPrice: 0,
    description: "Fikri keşfetmeye başlamak için",
    color: "border-[#d9d9dd]",
    badge: null,
    features: [
      "2 araştırma / ay",
      "3 persona",
      "Adversarial Review",
      "RFI Skoru",
      "Temel rapor",
    ],
    locked: [
      "PDF export",
      "A/B Test modu",
      "B2B persona",
      "Gerçek zamanlı stream",
    ],
  },
  {
    key: "Starter",
    name: "Starter",
    monthlyPrice: 990,
    annualPrice: 790,
    description: "Düzenli araştırma yapan bireyler için",
    color: "border-[#003c33]",
    badge: "Popüler",
    features: [
      "10 araştırma / ay",
      "5 persona",
      "Adversarial Review",
      "RFI Skoru",
      "PDF rapor export",
      "Gerçek zamanlı stream",
      "SES cross-tab tablosu",
    ],
    locked: [
      "A/B Test modu",
      "B2B persona",
    ],
  },
  {
    key: "Pro",
    name: "Pro",
    monthlyPrice: 2990,
    annualPrice: 2390,
    description: "Ekipler ve yoğun araştırma süreçleri için",
    color: "border-[#ff7759]",
    badge: "Tam Paket",
    features: [
      "Sınırsız araştırma",
      "7 persona",
      "A/B Test simülasyonu",
      "B2B persona modu",
      "Marka Sağlığı analizi",
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
    const planOrder = ["Free", "Starter", "Pro", "Enterprise"];
    if (planOrder.indexOf(planKey) <= planOrder.indexOf(currentPlan)) return;
    setSelected(planKey);
    setStep("confirm");
  };

  const handleUpgrade = async () => {
    if (!selected) return;
    setUpgrading(true);
    const username = typeof window !== "undefined" ? localStorage.getItem("appq_username") : null;
    if (!username) {
      toast.error("Kullanıcı oturumu bulunamadı.");
      setUpgrading(false);
      return;
    }
    try {
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/client/upgrade-plan", {
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
    const price = billing === "annual" ? selectedPlan.annualPrice : selectedPlan.monthlyPrice;
    const saving = selectedPlan.monthlyPrice > 0
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

          <div className="flex items-end justify-between pt-2 border-t border-[#d9d9dd]">
            <span className="text-muted-foreground text-sm">Tutar</span>
            <div className="text-right">
              <span className="text-2xl font-extrabold text-[#17171c]">
                {price === 0 ? "Ücretsiz" : `₺${price.toLocaleString("tr-TR")}`}
              </span>
              {price > 0 && (
                <span className="text-xs text-muted-foreground ml-1">
                  / {billing === "annual" ? "ay (yıllık fatura)" : "ay"}
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
          <div className="flex items-center gap-1"><CreditCard size={12} /> İstediğin zaman iptal</div>
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
      <div className="max-w-3xl mx-auto">
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
        <div className="flex items-center gap-3 mb-8 w-fit">
          {(["monthly", "annual"] as const).map(cycle => (
            <button
              key={cycle}
              onClick={() => setBilling(cycle)}
              className={`px-5 py-2 rounded-full text-sm font-medium border transition-all ${
                billing === cycle
                  ? "border-[#17171c] bg-[#17171c] text-white shadow-sm"
                  : "border-[#d9d9dd] text-muted-foreground hover:border-[#17171c]"
              }`}
            >
              {cycle === "monthly" ? "Aylık" : "Yıllık"}
              {cycle === "annual" && (
                <span className="ml-1.5 text-[10px] font-bold text-[#ff7759]">%20 indirim</span>
              )}
            </button>
          ))}
        </div>

        {/* Plan Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {PLANS.map(p => {
            const planOrder = ["Free", "Starter", "Pro", "Enterprise"];
            const isCurrent = p.key === currentPlan;
            const isDowngrade = planOrder.indexOf(p.key) < planOrder.indexOf(currentPlan);
            const price = billing === "annual" ? p.annualPrice : p.monthlyPrice;
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
                  <span className="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#ff7759] text-white">
                    {p.badge}
                  </span>
                )}
                {isCurrent && (
                  <span className="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#edfce9] text-[#003c33] border border-[#003c33]/30">
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
                <div className="text-xs text-muted-foreground mb-4">{p.description}</div>

                {/* Price */}
                <div className="mb-4">
                  {price === 0 ? (
                    <span className="text-2xl font-extrabold">Ücretsiz</span>
                  ) : (
                    <div className="flex items-end gap-1">
                      <span className="text-2xl font-extrabold">₺{price.toLocaleString("tr-TR")}</span>
                      <span className="text-xs text-muted-foreground mb-1">/ ay</span>
                    </div>
                  )}
                </div>

                {/* Features */}
                <ul className="space-y-1.5 flex-1">
                  {p.features.map(f => (
                    <li key={f} className="flex items-start gap-1.5 text-xs">
                      <Check size={12} className="text-[#003c33] shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                  {p.locked.map(f => (
                    <li key={f} className="flex items-start gap-1.5 text-xs opacity-40">
                      <Lock size={11} className="shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                {!disabled && (
                  <div className={`mt-4 w-full py-2 rounded-xl text-sm font-semibold text-center transition-all ${
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
        <div className="rounded-2xl border border-[#d9d9dd] p-5 flex items-center justify-between bg-[#f5f4f1]/30">
          <div>
            <div className="font-bold text-sm">Enterprise</div>
            <div className="text-xs text-muted-foreground">Sınırsız persona, white-label, çok kullanıcılı organizasyon</div>
          </div>
          <a
            href="mailto:hello@clarere.com?subject=Enterprise Plan Talebi"
            className="px-4 py-2 rounded-xl bg-[#17171c] text-white text-sm font-semibold hover:opacity-85 transition-opacity shrink-0"
          >
            İletişime Geç
          </a>
        </div>
      </div>
    </div>
  );
}
