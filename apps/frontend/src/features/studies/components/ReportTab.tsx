"use client";

import Link from "next/link";
import { Lock, Globe, MessageSquare, Send, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PlanGate } from "@/components/plan-gate";
import { PSMChart } from "./PSMChart";
import { ChannelBarChart } from "./ChannelBarChart";
import { renderMarkdown } from "../lib/render-markdown";
import type { Persona, PersonaInterview, StudyDetail } from "../types";

interface ReportTabProps {
  study: StudyDetail;
  personas: Persona[];
  interviews: PersonaInterview[];
  planType: string;
  isCompleted: boolean;
  chatMessages: Array<{ role: string; content: string }>;
  chatInput: string;
  onChatInputChange: (value: string) => void;
  sendingChat: boolean;
  onSendChat: () => void;
}

/** Sentez raporu sekmesi (refactor R2-6). Davranış ve görsel çıktı korunmuştur. */
export function ReportTab({
  study,
  personas,
  interviews,
  planType,
  isCompleted,
  chatMessages,
  chatInput,
  onChatInputChange,
  sendingChat,
  onSendChat,
}: ReportTabProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div>
        <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Yapay Zeka Sentez Raporu</h2>
        <p className="text-muted-foreground text-sm">Sentetik mülakatlardan elde edilen pazar analizleri, itirazlar ve ürün geliştirme tavsiyeleri.</p>
      </div>

      {/* Öne çıkan sayılar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Persona", value: personas.length },
          { label: "Mülakat Yanıtı", value: interviews.reduce((acc, iv) => acc + (iv.turns?.length || 0), 0) },
          { label: "Bulgu", value: study?.findings?.length ?? 0 },
          { label: "Öneri", value: study?.recommendations?.length ?? 0 },
        ].map(s => (
          <div key={s.label} className="rounded-xl border border-[#d9d9dd] bg-white dark:bg-[#212121] p-4 text-center">
            <div className="text-3xl font-black text-[#003c33] dark:text-[#edfce9]">{s.value}</div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-[#93939f] mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Rapor metrikleri + veri kökeni (S3) */}
      {study?.report_metrics && (study.report_metrics.findings_total ?? 0) > 0 && (
        <div className="rounded-xl border border-[#d9d9dd] bg-[#f5f4f1]/40 dark:bg-[#212121]/40 p-4 space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f]">Rapor Metrikleri</span>
            <span className="text-[10px] text-[#93939f]">Yönlendirici hipotez — istatistiksel temsil iddiası taşımaz</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Kanıtlı Bulgu", value: `${study.report_metrics.findings_with_evidence ?? 0}/${study.report_metrics.findings_total ?? 0}` },
              { label: "Bulgu Başına Kanıt", value: study.report_metrics.evidence_per_finding ?? 0 },
              { label: "Kanıtta Persona", value: study.report_metrics.unique_personas_in_evidence ?? 0 },
              { label: "Karşı Kanıt Oranı", value: study.report_metrics.refuting_ratio ?? 0 },
              { label: "Yanıt Tamamlama", value: study.report_metrics.answer_completion_rate ?? 0 },
              { label: "Harici Kaynak", value: study.report_metrics.external_evidence_count ?? 0 },
              { label: "Kaynaksız Bulgu", value: study.report_metrics.unsourced_findings ?? 0 },
            ].map(m => (
              <div key={m.label} className="rounded-lg border border-[#d9d9dd]/70 bg-white dark:bg-[#17171c] px-3 py-2">
                <div className="text-lg font-black text-[#003c33] dark:text-[#edfce9]">{m.value}</div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#93939f]">{m.label}</div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-2 text-[10px]">
            <span className="px-2 py-0.5 rounded-full border border-[#d9d9dd] text-[#616161] dark:text-[#93939f]">Sentetik: persona mülakatları</span>
            <span className="px-2 py-0.5 rounded-full border border-[#d9d9dd] text-[#616161] dark:text-[#93939f]">Algoritmik: PSM / SES / kalite</span>
            <span className="px-2 py-0.5 rounded-full border border-[#d9d9dd] text-[#616161] dark:text-[#93939f]">Harici: web doğrulama</span>
          </div>
        </div>
      )}

      {!isCompleted ? (
        <div className="text-center py-16 text-muted-foreground border border-dashed border-border rounded-xl bg-[#f5f4f1]/50">
          Bu araştırma henüz tamamlanmamış veya nihai sentez raporu üretilmemiş.
        </div>
      ) : planType === "Free" ? (
        <div className="space-y-4">
          {/* Teaser: Executive Summary clearly visible */}
          {study.report_markdown && (
            <Card className="shadow-sm border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/30 dark:bg-emerald-950/10">
              <CardContent className="p-5">
                <p className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase mb-2">Önizleme</p>
                <div className="text-sm text-[#616161] dark:text-[#e5e7eb] leading-relaxed line-clamp-4">
                  {study.report_markdown.split('\n').slice(0, 8).map((line, i) => <p key={i} className="my-1">{line}</p>)}
                </div>
              </CardContent>
            </Card>
          )}
          {/* Blurred full report + gradient CTA */}
          <div className="relative rounded-2xl overflow-hidden border border-[#d9d9dd]">
            <div className="filter blur-md pointer-events-none select-none opacity-20 p-6 space-y-4">
              {study.report_markdown && study.report_markdown.split('\n').slice(8, 30).map((line, i) => (
                <div key={i} className="h-3 bg-[#93939f] rounded" style={{width: `${70 + ((i * 13) % 30)}%`}} />
              ))}
            </div>
            <div className="absolute inset-x-0 bottom-0 flex flex-col items-center pb-6 pt-24"
              style={{background: "linear-gradient(to top, white 0%, white 50%, transparent 100%)"}}>
              <div className="text-center space-y-3 max-w-sm px-4">
                <Lock className="mx-auto text-amber-600" size={18} />
                <h3 className="text-base font-black text-[#212121]">Raporun Tamamını Gör</h3>
                <p className="text-xs text-muted-foreground">Fiyat analizi, kanıt zinciri ve karar önerileri seni bekliyor.</p>
                <Link href="/client/upgrade" className="inline-flex w-full">
                  <Button className="w-full bg-[#003c33] hover:bg-[#003c33]/90 text-white font-semibold rounded-xl py-2.5 text-sm">
                    Planı Yükselt →
                  </Button>
                </Link>
                <p className="text-[10px] text-muted-foreground">2 araştırma hakkı veya 1 ay · Tam rapor için plan gerekir</p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Van Westendorp PSM Card (Tüm planlar) */}
          <PlanGate currentPlan={planType} requiredPlan="Free" featureName="Van Westendorp Fiyat Analizi">
          {study?.van_westendorp && (
            <Card className="shadow-sm border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] overflow-hidden">
              <CardHeader className="pb-3 bg-[#f1f5ff]/60 dark:bg-[#071829]/20">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-base text-[#1863dc] dark:text-[#4c6ee6]">
                      Van Westendorp Fiyat Hassasiyet Ölçeri (PSM)
                    </CardTitle>
                    <CardDescription className="mt-0.5">
                      Sentetik mülakat yanıtlarından çıkarılan kabul edilebilir fiyat aralığı.
                    </CardDescription>
                  </div>
                  <Badge className="bg-[#1863dc] text-white text-xs shrink-0">
                    {study.van_westendorp.currency}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                {/* Key metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "PMC", sublabel: "Alt Kabul Sınırı", value: study.van_westendorp.pmc, color: "text-[#1863dc] dark:text-[#4c6ee6]", bg: "bg-[#f1f5ff] dark:bg-[#071829]/20 border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)]" },
                    { label: "OPP", sublabel: "Optimal Fiyat", value: study.van_westendorp.opp, color: "text-teal-700 dark:text-teal-400", bg: "bg-teal-50 dark:bg-teal-950/20 border-teal-100 dark:border-teal-900/30" },
                    { label: "IPP", sublabel: "Beklenti Noktası", value: study.van_westendorp.ipp, color: "text-sky-600 dark:text-sky-400", bg: "bg-sky-50 dark:bg-sky-950/20 border-sky-100 dark:border-sky-900/30" },
                    { label: "PME", sublabel: "Üst Kabul Sınırı", value: study.van_westendorp.pme, color: "text-pink-600 dark:text-pink-400", bg: "bg-pink-50 dark:bg-pink-950/20 border-pink-100 dark:border-pink-900/30" },
                  ].map(m => (
                    <div key={m.label} className={`p-3 rounded-xl border ${m.bg} text-center`}>
                      <div className={`text-2xl font-black ${m.color}`}>
                        {m.value.toLocaleString("tr-TR")} ₺
                      </div>
                      <div className="text-[10px] font-bold text-muted-foreground uppercase mt-1">{m.label}</div>
                      <div className="text-[10px] text-muted-foreground">{m.sublabel}</div>
                    </div>
                  ))}
                </div>

                {/* Acceptable range banner */}
                <div className="flex items-center gap-3 p-3 bg-[#f1f5ff] dark:bg-[#071829]/20 border border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] rounded-xl text-sm">
                  <div className="w-3 h-3 rounded-sm bg-[#e5e7eb] dark:bg-[rgba(24,99,220,0.25)] shrink-0" />
                  <span className="text-muted-foreground">Kabul edilebilir fiyat aralığı:</span>
                  <span className="font-bold text-[#1863dc] dark:text-[#4c6ee6]">
                    {study.van_westendorp.acceptable_range[0].toLocaleString("tr-TR")} ₺
                    {" — "}
                    {study.van_westendorp.acceptable_range[1].toLocaleString("tr-TR")} ₺
                  </span>
                </div>

                {/* SVG Chart */}
                <PSMChart data={study.van_westendorp} />

                {/* Methodology note */}
                <p className="text-xs text-muted-foreground italic border-t border-border/50 pt-3">
                  {study.van_westendorp.methodology_note}
                </p>
              </CardContent>
            </Card>
          )}
          </PlanGate>

          {/* Brand Health Card (Pro+) */}
          <PlanGate currentPlan={planType} requiredPlan="Pro" featureName="Marka Sağlığı Analizi">
          {study?.brand_health && (
            <Card className="shadow-sm border-sky-100 dark:border-sky-900/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-sky-700 dark:text-sky-400">Marka Sağlığı — Yardımsız Bilinirlik</CardTitle>
                <CardDescription>
                  {study.brand_health.top_of_mind
                    ? `"${study.brand_health.top_of_mind}" en çok akla gelen rakip (${study.brand_health.total_mentions} toplam anma).`
                    : "Rakip marka anma verisi bulunamadı."}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Unaided recall counts */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(study.brand_health.unaided_recall)
                    .filter(([k]) => k !== "diğer")
                    .sort(([,a],[,b]) => b - a)
                    .map(([brand, count]) => (
                      <div key={brand} className="p-3 border border-border rounded-xl text-center">
                        <div className="text-xl font-black text-sky-600 dark:text-sky-400">{count}</div>
                        <div className="text-xs text-muted-foreground mt-1 truncate">{brand}</div>
                      </div>
                    ))}
                </div>
                {/* Associations */}
                {Object.keys(study.brand_health.associations).length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase">Çağrışım Haritası</p>
                    {Object.entries(study.brand_health.associations).map(([brand, words]) => (
                      <div key={brand} className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold text-[#616161] w-24 shrink-0">{brand}</span>
                        {words.map(w => (
                          <Badge key={w} variant="outline" className="text-[10px] font-medium">{w}</Badge>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
          </PlanGate>

          {/* Channel Discovery Card */}
          {study?.channel_map && study.channel_map.length > 0 && (
            <Card className="shadow-sm border-emerald-100/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-emerald-700 dark:text-emerald-400">Keşif Kanalı Haritası</CardTitle>
                <CardDescription>Sentetik personaların ürünü keşfetmek için tercih ettiği kanallar.</CardDescription>
              </CardHeader>
              <CardContent>
                <ChannelBarChart data={study.channel_map} />
              </CardContent>
            </Card>
          )}

          {/* Synthesis markdown report */}
          <Card className="shadow-sm">
            <CardContent className="p-6 sm:p-10 prose prose-slate max-w-none dark:prose-invert">
              {renderMarkdown(study.report_markdown)}
            </CardContent>
          </Card>

          {/* External Evidence Verification */}
          {study?.external_evidence && study.external_evidence.length > 0 && (
            <Card className="shadow-sm border-[#003c33]/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Globe size={16} className="text-[#1863dc]" />
                  Harici Kanıt Doğrulaması
                </CardTitle>
                <CardDescription>Açık web ve literatür taraması ile bulguların teyit edilmesi.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {study.external_evidence.map((ev, i) => (
                  <div key={i} className="flex gap-3 items-start p-3 bg-[#f5f4f1] rounded-lg border border-border/60">
                    <Globe size={14} className="shrink-0 mt-0.5 text-[#93939f]" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-sm text-[#212121]">{ev.source_title}</span>
                        <Badge variant="outline" className="text-[10px]">{ev.relevance}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{ev.snippet}</p>
                      {ev.source_url && (
                        <a href={ev.source_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-[#1863dc] hover:underline mt-1 inline-block">
                          Kaynağa Git →
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Research Copilot Chat */}
          <Card className="shadow-sm border-[#003c33]/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare size={16} className="text-[#1863dc]" />
                Araştırma Asistanı
              </CardTitle>
              <CardDescription>Raporla ilgili sorular sorun</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-60 overflow-y-auto mb-3">
                {chatMessages.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-3">
                    Rapordaki bulgular, personalar veya öneriler hakkında soru sorabilirsiniz.
                  </p>
                )}
                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] p-2.5 rounded-xl text-xs leading-relaxed ${
                        msg.role === "user"
                          ? "bg-[#1863dc] text-white rounded-br-sm"
                          : "bg-[#eeece7] text-[#616161] rounded-bl-sm"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {sendingChat && (
                  <div className="flex justify-start">
                    <div className="bg-[#eeece7] text-[#93939f] p-2.5 rounded-xl rounded-bl-sm text-xs">
                      <Loader2 size={14} className="animate-spin inline mr-1.5" />
                      Düşünüyor...
                    </div>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Input
                  value={chatInput}
                  onChange={(e) => onChatInputChange(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") onSendChat(); }}
                  placeholder="Örn: Şüpheciler neden reddetti?"
                  className="text-sm"
                  disabled={sendingChat}
                />
                <Button
                  onClick={onSendChat}
                  disabled={!chatInput.trim() || sendingChat}
                  size="sm"
                  className="shrink-0 bg-[#17171c] text-white hover:opacity-85 dark:bg-[#ffffff] dark:text-[#17171c]"
                >
                  {sendingChat ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                  <span className="ml-1.5 hidden sm:inline">Gönder</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
