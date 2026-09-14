"use client";

import { Compass, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PlanGate } from "@/components/plan-gate";
import type { ResearchBriefDetail, ResearchPlan, StudyDetail, StudyMetadata } from "../types";

interface SummaryTabProps {
  brief?: ResearchBriefDetail;
  metadata?: StudyMetadata;
  plan?: ResearchPlan;
  study: StudyDetail;
  planType: string;
}

/** Özet & Hedefler sekmesi (refactor R2-1). Görsel çıktı R2 öncesiyle birebir aynıdır. */
export function SummaryTab({ brief, metadata, plan, study, planType }: SummaryTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="lg:col-span-2 space-y-6">
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-action-blue dark:text-focus-blue text-lg">
              <Compass size={20} />
              Araştırma Brief&apos;i ve Bağlam
            </CardTitle>
            <CardDescription>Başlangıçta tanımlanan araştırma problemi.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3.5 bg-muted-surface border border-border rounded-lg">
                <span className="text-xs font-semibold text-muted-foreground block uppercase">Marka / Ürün</span>
                <span className="font-bold text-ink dark:text-border-light">{brief?.title || metadata?.title || "Belirtilmemiş"}</span>
              </div>
              {(brief?.category || metadata?.category) && (
                <div className="p-3.5 bg-muted-surface border border-border rounded-lg">
                  <span className="text-xs font-semibold text-muted-foreground block uppercase">Kategori</span>
                  <span className="font-bold text-ink dark:text-border-light">{brief?.category || metadata?.category}</span>
                </div>
              )}
              <div className="p-3.5 bg-muted-surface border border-border rounded-lg sm:col-span-2">
                <span className="text-xs font-semibold text-muted-foreground block uppercase">Fiyat Modeli</span>
                <span className="font-bold text-ink dark:text-border-light leading-relaxed">{brief?.expected_price || "Belirtilmedi"}</span>
              </div>
              {brief?.target_users && brief.target_users.length > 0 && (
                <div className="p-3.5 bg-muted-surface border border-border rounded-lg sm:col-span-2">
                  <span className="text-xs font-semibold text-muted-foreground block uppercase">Hedef Kitle</span>
                  <span className="font-medium text-body-muted dark:text-border-light text-sm leading-relaxed">{brief.target_users.join(" · ")}</span>
                </div>
              )}
              {brief?.competitors && brief.competitors.length > 0 && (
                <div className="p-3.5 bg-muted-surface border border-border rounded-lg sm:col-span-2">
                  <span className="text-xs font-semibold text-muted-foreground block uppercase">Rakipler</span>
                  <span className="font-medium text-body-muted dark:text-border-light text-sm leading-relaxed">{brief.competitors.join(" · ")}</span>
                </div>
              )}
              {brief?.success_metric && (
                <div className="p-3.5 bg-muted-surface border border-border rounded-lg">
                  <span className="text-xs font-semibold text-muted-foreground block uppercase">Başarı Kriteri</span>
                  <span className="font-medium text-body-muted dark:text-border-light text-sm leading-relaxed">{brief.success_metric}</span>
                </div>
              )}
              {brief?.sales_channel && (
                <div className="p-3.5 bg-muted-surface border border-border rounded-lg">
                  <span className="text-xs font-semibold text-muted-foreground block uppercase">Satış Kanalı</span>
                  <span className="font-medium text-body-muted dark:text-border-light text-sm leading-relaxed">{brief.sales_channel}</span>
                </div>
              )}
              {(brief?.panel_size || brief?.geography) && (
                <div className="p-3.5 bg-muted-surface border border-border rounded-lg sm:col-span-2">
                  <span className="text-xs font-semibold text-muted-foreground block uppercase">Panel & Coğrafya</span>
                  <span className="font-medium text-body-muted dark:text-border-light text-sm leading-relaxed">{[brief?.panel_size, brief?.geography].filter(Boolean).join(" · ")}</span>
                </div>
              )}
            </div>
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-muted-foreground uppercase block">Araştırma Problemi (Brief Context)</span>
              <p className="text-body-muted text-sm leading-relaxed bg-muted-surface/50 border border-border/60 p-4 rounded-xl">
                {brief?.idea || "Brief bağlamı girilmemiş."}
              </p>
            </div>
          </CardContent>
        </Card>

        {plan && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Araştırma Hedefleri ve Varsayımlar</CardTitle>
              <CardDescription>Brief doğrultusunda simüle edilen hedefler.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {plan.objective && (
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-muted-foreground uppercase block">Ana Araştırma Hedefi</span>
                  <p className="text-ink text-sm font-medium bg-muted-surface p-4 rounded-xl border border-border">
                    {plan.objective}
                  </p>
                </div>
              )}

              {plan.assumptions && plan.assumptions.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-muted-foreground uppercase block">Test Edilen Varsayımlar (Assumptions)</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {plan.assumptions.map((ass: string, i: number) => (
                      <div key={i} className="flex gap-2 p-3 bg-pale-blue/30 dark:bg-dark-navy/10 border border-border-light/50 dark:border-action-blue/10 rounded-lg text-sm">
                        <span className="font-bold text-action-blue dark:text-focus-blue">#{i + 1}</span>
                        <span className="text-body-muted ">{ass}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-6">
        {/* Quality summary widget */}
        {metadata?.quality_score && (
          <Card className="shadow-sm border-l-4 border-l-emerald-500 overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold uppercase text-muted-foreground">Araştırma Kalite Skoru</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-black text-emerald-600 dark:text-emerald-400">{metadata.quality_score}</span>
                <span className="text-muted-text font-semibold text-xl">/100</span>
                <Badge className="ml-2 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 hover:bg-emerald-50 border border-emerald-200">
                  Sınıf: {metadata.quality_grade || "A"}
                </Badge>
              </div>
              {metadata.quality_summary && (
                <p className="text-body-muted text-xs leading-relaxed border-t border-border pt-3">
                  {metadata.quality_summary}
                </p>
              )}
              {/* Bias Detection Flags */}
              {study?.research_quality && (
                (() => {
                  const rq = study.research_quality;
                  const flags = [
                    (rq.straight_lining_count || 0) > 0 && {
                      icon: "🔁",
                      label: "Tekdüze Yanıt Kalıbı",
                      count: rq.straight_lining_count || 0,
                      color: "text-red-600 dark:text-red-400",
                      bg: "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/40",
                    },
                    (rq.acquiescence_count || 0) > 0 && {
                      icon: "🟠",
                      label: "Aşırı Uzlaşmacılık",
                      count: rq.acquiescence_count || 0,
                      color: "text-orange-600 dark:text-orange-400",
                      bg: "bg-orange-50 dark:bg-orange-950/20 border-orange-200 dark:border-orange-900/40",
                    },
                    (rq.social_desirability_count || 0) > 0 && {
                      icon: "💬",
                      label: "Sosyal Beğeni Etkisi",
                      count: rq.social_desirability_count || 0,
                      color: "text-amber-600 dark:text-amber-400",
                      bg: "bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/40",
                    },
                  ].filter(Boolean) as Array<{ icon: string; label: string; count: number; color: string; bg: string }>;

                  return flags.length > 0 ? (
                    <div className="space-y-2 border-t border-border pt-3">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase">Yanıt Sapması Uyarıları</p>
                      {flags.map(f => (
                        <div key={f.label} className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium ${f.bg}`}>
                          <span>{f.icon}</span>
                          <span className={f.color}>{f.label}</span>
                          <Badge variant="outline" className="ml-auto text-[10px]">{f.count} persona</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 border-t border-border pt-3">
                      <CheckCircle2 size={14} />
                      <span>Yanıt sapması tespit edilmedi.</span>
                    </div>
                  );
                })()
              )}
            </CardContent>
          </Card>
        )}

        {/* RFI Card — Research Fidelity Index (tüm planlarda açık) */}
        <PlanGate currentPlan={planType} requiredPlan="Free" featureName="Araştırma Bütünlüğü (RFI)">
        {study?.research_quality && (
          study.research_quality.warning_count !== undefined ||
          study.research_quality.rfi !== undefined ||
          (study.research_quality.flags && study.research_quality.flags.length >= 0) ||
          study.research_quality.summary !== undefined ||
          (study.research_quality.phases_passed && study.research_quality.phases_passed.length >= 0)
        ) && (
          (() => {
            const rq = study.research_quality!;
            const rfi = rq.rfi ?? null;
            const components = rq.components ?? {};
            const validity = rq.valid ?? (rfi !== null ? rfi >= 0.65 : null);
            const warnings = rq.warning_count ?? 0;
            const phasesPassed = rq.phases_passed ?? [];
            const phasesFlagged = rq.phases_flagged ?? [];
            const flags = rq.flags ?? [];
            const adversarialSummary = rq.interpretation ?? rq.summary ?? "";

            const rfiColor = rfi === null ? "text-muted-text" : rfi >= 0.80 ? "text-emerald-600 dark:text-emerald-400" : rfi >= 0.65 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400";
            const borderColor = rfi === null ? "border-l-hairline" : rfi >= 0.80 ? "border-l-emerald-500" : rfi >= 0.65 ? "border-l-amber-500" : "border-l-red-500";
            const COMPONENT_COLORS: Record<string, string> = {
              PGR: "var(--color-series-1)", CNS: "var(--color-series-3)", AC: "var(--color-series-4)",
              PR: "var(--color-series-5)", PCal: "var(--color-series-6)", CRA: "var(--color-series-7)",
            };
            const componentColor = (key: string) => COMPONENT_COLORS[key] ?? "var(--color-series-neutral)";
            const COMPONENT_LABELS: Record<string, string> = {
              PGR: "Kapsam (PGR)", CNS: "Yenilik (CNS)", AC: "Tutarlılık (AC)",
              PR: "Temsil (PR)", PCal: "Kalibrasyon", CRA: "Uyum (CRA)",
            };

            return (
              <Card className={`shadow-sm border-l-4 ${borderColor} overflow-hidden`}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold uppercase text-muted-foreground flex items-center gap-2">
                    Araştırma Bütünlüğü (RFI)
                    <Badge
                      className={validity === null
                        ? "bg-muted-surface text-body-muted border border-hairline"
                        : validity
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200"
                        : "bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400 border border-red-200 dark:border-red-900/40"}
                    >
                      {validity === null ? "Ölçülmedi" : validity ? "Geçerli" : "Eşik Altı"}
                    </Badge>
                  </CardTitle>
                  <CardDescription className="text-[10px]">Bilimsel simülasyon temelli bütünlük ölçütü — yanıt kalitesi ve tutarlılık denetimi.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {rfi !== null && (
                    <div className="flex items-baseline gap-2">
                      <span className={`text-4xl font-black ${rfiColor}`}>{(rfi * 100).toFixed(1)}</span>
                      <span className="text-muted-text font-semibold">/100</span>
                      <span className="text-xs text-muted-foreground">eşik ≥65</span>
                    </div>
                  )}

                  {/* RFI Component Bar Chart */}
                  {Object.keys(components).length > 0 && (
                    <div className="space-y-2 border-t border-border pt-3">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase">Bileşen Profili</p>
                      {Object.entries(components).map(([key, val]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-[10px] font-semibold text-body-muted w-28 shrink-0">{COMPONENT_LABELS[key] ?? key}</span>
                          <div className="flex-1 bg-soft-stone rounded-full h-2 overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-700"
                              style={{ width: `${(val as number) * 100}%`, backgroundColor: componentColor(key) }}
                            />
                          </div>
                          <span className="text-[10px] font-bold tabular-nums w-8 text-right" style={{ color: componentColor(key) }}>
                            {((val as number) * 100).toFixed(0)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Adversarial Review özeti */}
                  {(phasesPassed.length > 0 || phasesFlagged.length > 0) && (
                    <div className="space-y-1.5 border-t border-border pt-3">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase">Adversarial Review Aşamaları</p>
                      <div className="flex flex-wrap gap-1.5">
                        {phasesPassed.map(ph => (
                          <Badge key={ph} className="text-[10px] bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200">
                            ✓ {ph}
                          </Badge>
                        ))}
                        {phasesFlagged.map(ph => (
                          <Badge key={ph} className="text-[10px] bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400 border border-amber-200 dark:border-amber-900/40">
                            ⚠ {ph}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Uyarı listesi */}
                  {flags.filter(f => f.severity === "warning" || f.severity === "fail").slice(0, 3).length > 0 && (
                    <div className="space-y-1.5 border-t border-border pt-3">
                      <p className="text-[10px] font-bold text-muted-foreground uppercase">Dikkat Gerektiren Noktalar ({warnings})</p>
                      {flags.filter(f => f.severity === "warning" || f.severity === "fail").slice(0, 3).map((f, i) => (
                        <div key={i} className="text-[10px] text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-md px-2.5 py-1.5 leading-relaxed">
                          {f.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {adversarialSummary && (
                    <p className="text-[10px] text-body-muted border-t border-border pt-2 leading-relaxed">
                      {adversarialSummary}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })()
        )}
        </PlanGate>
      </div>
    </div>
  );
}
