"use client";

import Link from "next/link";
import { Check, X } from "lucide-react";
import { Reveal } from "@/features/landing/hooks/use-reveal";

import { useState } from "react";
import { FEATURES, PLAN_META, PLAN_PRICES } from "./plans";

/** Fiyatlandırma bölümü: plan kartları, Enterprise bandı ve karşılaştırma tablosu (refactor R4-2). */
export function PricingSection() {
  const [cardBilling, setCardBilling] = useState<Record<string, "monthly" | "annual">>({});
  const getBilling = (name: string) => cardBilling[name] ?? "monthly";
  const toggleBilling = (name: string) =>
    setCardBilling((prev) => ({ ...prev, [name]: prev[name] === "annual" ? "monthly" : "annual" }));

  return (
  <section id="pricing" className="bg-white max-w-full px-6 py-24 scroll-mt-16">
    <div className="max-w-6xl mx-auto">
    <Reveal>
      <div className="mb-12">
        <p className="mono-label text-[#93939f] mb-3">Planlar</p>
        <h2 className="display-section text-[#17171c] mb-2">Fiyatlandırma</h2>
        <p className="text-[#616161] text-base">İstediğin zaman yükselt veya düşür. Gizli ücret yok.</p>
      </div>
    </Reveal>

    {/* Plan Cards — first 4 */}
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      {PLAN_META.filter(p => p.name !== "Enterprise").map((plan, idx) => {
        const prices = PLAN_PRICES[plan.name];
        const isVariable = prices.monthly === null;
        const isAnnual = getBilling(plan.name) === "annual";
        const showAnnual = isAnnual && plan.hasBillingToggle && prices.annual;

        const priceDisplay = isVariable
          ? "Özel"
          : showAnnual
            ? `$${prices.annual!.toLocaleString("en-US")}`
            : `$${prices.monthly!.toLocaleString("en-US")}`;

        const periodDisplay = isVariable
          ? ""
          : plan.isOneTime
            ? " / paket"
            : "/ay";

        return (
          <Reveal key={plan.name} delay={idx * 60}>
            <div
              className={`relative rounded-[8px] border p-6 flex flex-col gap-4 h-full transition-colors ${plan.highlight
                  ? "border-[#17171c] bg-[#17171c] text-white shadow-xl md:hover:border-[#ff7759]"
                  : "border-[#d9d9dd] bg-white md:hover:border-[#ff7759]/50"
                }`}
            >
              {plan.highlight && (
                <div
                  className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-xs font-bold tracking-wider uppercase bg-coral text-white"
                >
                  En Popüler
                </div>
              )}

              {plan.isOneTime && (
                <div
                  className={`absolute top-3 right-3 px-2.5 py-0.5 rounded-full text-[9px] font-bold tracking-wider uppercase ${
                    plan.highlight
                      ? "bg-white/10 text-white border border-white/20"
                      : "bg-coral/10 text-coral border border-coral/20"
                  }`}
                >
                  Tek Seferlik
                </div>
              )}

              <div>
                <h3 className="text-base font-semibold mb-0.5">{plan.name}</h3>
                <p className={`text-xs ${plan.highlight ? "text-white/55" : "text-[#93939f]"}`}>{plan.description}</p>
              </div>

              {/* Billing toggle */}
              {plan.hasBillingToggle && (
                <div
                  className={`flex items-center gap-0.5 p-0.5 self-start rounded-full border ${plan.highlight ? "border-white/20 bg-white/10" : "border-[#d9d9dd] bg-[#f5f4f1]"
                    }`}
                >
                  <button
                    onClick={() => toggleBilling(plan.name)}
                    className={`px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${!isAnnual
                        ? plan.highlight ? "bg-white text-[#17171c] shadow-sm" : "bg-white text-[#17171c] shadow-sm"
                        : plan.highlight ? "text-white/50" : "text-[#93939f]"
                      }`}
                  >
                    Aylık
                  </button>
                  <button
                    onClick={() => toggleBilling(plan.name)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all ${isAnnual
                        ? plan.highlight ? "bg-white text-[#17171c] shadow-sm" : "bg-white text-[#17171c] shadow-sm"
                        : plan.highlight ? "text-white/50" : "text-[#93939f]"
                      }`}
                  >
                    Yıllık
                    <span className="text-[9px] font-bold bg-[#ff7759] text-white px-1 py-0.5 rounded-full leading-none">
                      -20%
                    </span>
                  </button>
                </div>
              )}

              <div>
                <div className="flex items-end gap-1">
                  <span className="text-3xl font-bold tracking-tight tracking-tighter">{priceDisplay}</span>
                  <span className={`text-sm mb-0.5 ${plan.highlight ? "text-white/55" : "text-[#93939f]"}`}>{periodDisplay}</span>
                </div>
                <p
                  className="text-xs mt-1 transition-opacity duration-300 min-h-[16px]"
                  style={{ color: plan.highlight ? "#edfce9" : "#003c33" }}
                >
                  {plan.isOneTime
                    ? "Ömür boyu kullanım, taahhüt yok"
                    : isVariable
                      ? "Gereksinimlerinize göre kapsam"
                      : showAnnual
                        ? `Yıllık faturalandırılır (toplam $${(prices.annual! * 12).toLocaleString("en-US")})`
                        : `Aylık faturalandırılır`
                  }
                </p>
              </div>

              <ul className="space-y-1.5 flex-1">
                {plan.limits.map((l) => (
                  <li key={l} className={`flex items-start gap-2 text-sm ${plan.highlight ? "text-white/80" : "text-[#616161]"}`}>
                    <Check size={13} color={plan.highlight ? "#edfce9" : "#003c33"} className="shrink-0 mt-1" />
                    <span className="leading-tight">{l}</span>
                  </li>
                ))}
                {plan.isOneTime && (
                  <li className={`flex items-center gap-2 text-xs pt-1 border-t mt-1 ${plan.highlight ? "border-white/10 text-white/30" : "border-[#d9d9dd] text-[#93939f]/60"}`}>
                    <Check size={11} className="shrink-0" color={plan.highlight ? "#edfce9" : "#003c33"} />
                    Kullanım süresi sınırı yoktur
                  </li>
                )}
                {!plan.isOneTime && !isVariable && (
                  <li className={`flex items-center gap-2 text-xs pt-1 border-t mt-1 ${plan.highlight ? "border-white/10 text-white/30" : "border-[#d9d9dd] text-[#93939f]/60"}`}>
                    <X size={11} className="shrink-0" />
                    Kullanılmayan haklar devretmez
                  </li>
                )}
              </ul>

              <Link
                href={plan.ctaHref}
                className={`w-full flex items-center justify-center py-2.5 rounded-full text-sm font-semibold transition-colors ${plan.highlight
                    ? "bg-white text-[#17171c] hover:bg-white/90"
                    : "bg-[#17171c] text-white hover:opacity-85 btn-pill-primary"
                  }`}
              >
                {plan.cta}
              </Link>
            </div>
          </Reveal>
        );
      })}
    </div>

    {/* Enterprise — full width banner below */}
    {PLAN_META.filter(p => p.name === "Enterprise").map((plan, idx) => {
      return (
        <Reveal key={plan.name} delay={idx * 60}>
          <div className="w-full rounded-[8px] border border-[#d9d9dd] bg-[#f5f4f1] p-6 flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-12">
            <div className="flex-1">
              <h3 className="text-base font-semibold mb-0.5">{plan.name}</h3>
              <p className="text-xs text-[#93939f]">{plan.description}</p>
              <ul className="flex flex-wrap gap-x-5 gap-y-1 mt-3">
                {plan.limits.map((limit) => (
                  <li key={limit} className="flex items-center gap-1.5 text-xs text-[#616161]">
                    <Check size={12} className="text-[#003c33] shrink-0" />
                    {limit}
                  </li>
                ))}
              </ul>
            </div>
            <a
              href={plan.ctaHref}
              className="shrink-0 px-6 py-2.5 rounded-lg text-sm font-semibold bg-[#17171c] text-white hover:bg-[#17171c]/85 transition-colors"
            >
              {plan.cta}
            </a>
          </div>
        </Reveal>
      );
    })}

    {/* Comparison table */}
    <Reveal>
      <div className="overflow-x-auto rounded-[8px] border border-[#d9d9dd]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#d9d9dd] bg-[#f5f4f1]">
              <th className="text-left px-5 py-3.5 font-medium text-[#93939f]">Özellik</th>
              {PLAN_META.map((p) => (
                <th
                  key={p.name}
                  className={`text-center px-4 py-3.5 font-semibold ${p.highlight ? "text-[#17171c]" : "text-[#616161]"}`}
                >
                  {p.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {FEATURES.map((f, i) => (
              <tr
                key={f.label}
                className={`border-b border-[#f2f2f2] ${i % 2 === 0 ? "bg-white" : "bg-[#fafafa]"}`}
              >
                <td className="px-5 py-3 font-medium text-[#212121]">{f.label}</td>
                {f.plans.map((has, j) => (
                  <td key={j} className="px-4 py-3 text-center">
                    {has
                      ? <Check size={14} color="#003c33" className="mx-auto" />
                      : <X size={14} className="text-[#d9d9dd] mx-auto" />}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-center text-xs text-[#93939f] mt-4">
        Tüm fiyatlar KDV hariçtir. Yıllık faturalamalarda %20 indirim uygulanır.
      </p>
    </Reveal>
    </div>
  </section>
  );
}
