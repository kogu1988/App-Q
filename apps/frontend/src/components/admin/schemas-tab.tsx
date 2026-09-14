"use client";

import { toast } from "sonner";
import { getAdminHeaders } from "@/lib/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
} from "@/components/ui/dialog";
import {
  Plus,
  Save,
  Loader2,
  Pencil,
  X,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import type {
  AgentSchemas,
} from "@/features/admin/types";

import type { Dispatch, SetStateAction } from "react";

interface SchemasTabProps {
  schemas: AgentSchemas | null;
  onSchemasChange: Dispatch<SetStateAction<AgentSchemas | null>>;
  schemasLoading: boolean;
  expandedPool: string | null;
  onExpandedPoolChange: Dispatch<SetStateAction<string | null>>;
  editingDefaultQ: boolean;
  onEditingDefaultQChange: Dispatch<SetStateAction<boolean>>;
  draftQuestions: string[];
  onDraftQuestionsChange: Dispatch<SetStateAction<string[]>>;
  savingDefaults: boolean;
  onSavingDefaultsChange: Dispatch<SetStateAction<boolean>>;
  briefDefaults: Record<string, string>;
}

/** Ajan sablonlari sekmesi (refactor R3). */
export function SchemasTab({
  schemas,
  onSchemasChange,
  schemasLoading,
  expandedPool,
  onExpandedPoolChange,
  editingDefaultQ,
  onEditingDefaultQChange,
  draftQuestions,
  onDraftQuestionsChange,
  savingDefaults,
  onSavingDefaultsChange,
  briefDefaults,
}: SchemasTabProps) {
  return (
    <>
  <div className="mb-6">
    <p className="text-sm text-muted-foreground">
      Ajanlara iletilen veri yapıları, varsayılan soru havuzları ve brief şablonları.
    </p>
  </div>

  {schemasLoading && (
    <div className="flex items-center gap-3 py-12 justify-center text-muted-foreground">
      <Loader2 size={20} className="animate-spin" />
      Şemalar yükleniyor...
    </div>
  )}

  {schemas && !schemas.brief_schema && (
    <div className="flex items-center gap-3 py-4 text-amber-600 dark:text-amber-400 text-sm">
      ⚠️ Şema verisi beklenmeyen formatta geldi. Backend&apos;in çalıştığından emin olun.
    </div>
  )}

  {schemas?.brief_schema && (
    <>
      <Card className="border-[#d9d9dd] bg-[#edfce9]/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold text-[#003c33]">Veri Akış Şeması</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2 text-sm font-mono">
            {[
              { label: "Brief (Defne)", color: "bg-[#edfce9] text-[#003c33]" },
              { label: "→", color: "text-muted-foreground" },
              { label: "ResearchPlan", color: "bg-[#f1f5ff] text-[#1863dc]" },
              { label: "→", color: "text-muted-foreground" },
              { label: "Persona[]", color: "bg-[#edfce9] text-[#003c33]" },
              { label: "→", color: "text-muted-foreground" },
              { label: "Interview[]", color: "bg-amber-100 text-amber-800" },
              { label: "→", color: "text-muted-foreground" },
              { label: "ResearchReport", color: "bg-rose-100 text-rose-800" },
            ].map((s, i) => (
              <span key={i} className={`px-2.5 py-1 rounded-lg font-semibold text-xs ${s.color}`}>
                {s.label}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {[
          {
            title: "Brief Şeması",
            desc: schemas.brief_schema?.description ?? "",
            badge: "Defne → intake.py",
            badgeColor: "border-[#d9d9dd] text-[#003c33]",
            rows: (schemas.brief_schema?.fields ?? []).map(f => [
              f.key,
              f.type,
              f.required ? "Zorunlu" : "Opsiyonel",
              f.desc,
            ]),
            headers: ["Alan", "Tip", "Durum", "Açıklama"],
          },
          {
            title: "Persona Şeması",
            desc: schemas.persona_schema?.description ?? "",
            badge: "workflow.py → LLM",
            badgeColor: "border-[#003c33]/30 text-[#003c33] dark:border-emerald-800",
            rows: (schemas.persona_schema?.fields ?? []).map(f => [f.key, f.type, "", f.desc]),
            headers: ["Alan", "Tip", "", "Açıklama"],
          },
          {
            title: "Mülakat Turu Çıktısı",
            desc: schemas.interview_schema?.description ?? "",
            badge: "interview turn → LLM",
            badgeColor: "border-amber-200 text-amber-700 dark:border-amber-800",
            rows: Object.entries(schemas.interview_schema?.output ?? {}).map(([k, v]) => [k, "", "", v]),
            headers: ["Alan", "", "", "Açıklama"],
          },
          {
            title: "Sentez Raporu Çıktısı",
            desc: schemas.synthesis_schema?.description ?? "",
            badge: "analytics.py",
            badgeColor: "border-rose-200 text-rose-700 dark:border-rose-800",
            rows: (schemas.synthesis_schema?.output_fields ?? []).map(f => [f, "", "", ""]),
            headers: ["Alan", "", "", ""],
          },
        ].map(card => (
          <Card key={card.title} className="overflow-hidden">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="text-sm font-bold">{card.title}</CardTitle>
                <Badge variant="outline" className={`text-[10px] font-mono shrink-0 ${card.badgeColor}`}>
                  {card.badge}
                </Badge>
              </div>
              <CardDescription className="text-xs">{card.desc}</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-t border-b border-border bg-muted/40">
                      {card.headers.filter(Boolean).map(h => (
                        <th
                          key={h}
                          className="text-left py-1.5 px-3 font-mono text-[#93939f] uppercase tracking-wider text-[10px]"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {card.rows.map((row, ri) => (
                      <tr
                        key={ri}
                        className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                      >
                        {row
                          .filter((_, ci) => card.headers[ci])
                          .map((cell, ci) => (
                            <td
                              key={ci}
                              className={`py-1.5 px-3 ${
                                ci === 0 ? "font-mono font-bold text-[#003c33]" : "text-muted-foreground"
                              } ${
                                ci === 2 && cell === "Zorunlu"
                                  ? "text-red-600 dark:text-red-400 font-semibold"
                                  : ""
                              }`}
                            >
                              {cell}
                            </td>
                          ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold">Mülakat Prompt Değişkenleri</CardTitle>
          <CardDescription>Her persona–soru turunda modele gönderilen bağlam değişkenleri.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-1.5">
            {(schemas.interview_schema?.prompt_variables ?? []).map(v => (
              <Badge key={v} variant="outline" className="text-[10px] font-mono bg-[#f5f4f1]">
                {v}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold">Brief Varsayılan Değerleri</CardTitle>
          <CardDescription>
            Yeni araştırma oluşturulduğunda Defne&apos;ye iletilecek varsayılan brief değerleri.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries({
              default_market: "Hedef Pazar",
              default_category: "Varsayılan Kategori",
              default_expected_price: "Varsayılan Fiyat Modeli",
              default_sales_channel: "Varsayılan Satış Kanalı",
              default_success_metric: "Varsayılan Başarı Kriteri",
            }).map(([key, label]) => (
              <div key={key} className="space-y-1.5">
                <Label className="text-xs">{label}</Label>
                <div className="flex gap-2">
                  <Input
                    id={`brief-default-${key}`}
                    className="h-8 text-xs bg-background text-foreground"
                    defaultValue={briefDefaults[key] || ""}
                    placeholder="Boş bırakılabilir"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 shrink-0 text-[#212121]"
                    disabled={savingDefaults}
                    onClick={async () => {
                      const el = document.getElementById(`brief-default-${key}`) as HTMLInputElement;
                      if (!el) return;
                      onSavingDefaultsChange(true);
                      try {
                        await fetch("/api/admin/schemas/brief-defaults", {
                          method: "PUT",
                          headers: { "Content-Type": "application/json", ...getAdminHeaders() },
                          body: JSON.stringify({ [key]: el.value }),
                        });
                        toast.success(`${label} kaydedildi.`);
                      } catch {
                        toast.error("Kaydedilemedi.");
                      } finally {
                        onSavingDefaultsChange(false);
                      }
                    }}
                  >
                    {savingDefaults ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold">Varsayılan Mülakat Soruları</CardTitle>
              <CardDescription className="mt-0.5">
                workflow.py DEFAULT_QUESTIONS — system_config&apos;den override edilebilir.
              </CardDescription>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 h-8 text-[#212121]"
              onClick={() => {
                onEditingDefaultQChange(!editingDefaultQ);
                if (!editingDefaultQ) onDraftQuestionsChange([...schemas.default_interview_questions]);
              }}
            >
              <Pencil size={12} />
              {editingDefaultQ ? "İptal" : "Düzenle"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {editingDefaultQ ? (
            <>
              {draftQuestions.map((q, qi) => (
                <div key={qi} className="flex gap-2">
                  <span className="text-xs font-mono text-muted-foreground w-5 shrink-0 mt-2.5">
                    {qi + 1}.
                  </span>
                  <Textarea
                    className="text-xs min-h-0 h-auto resize-none bg-background text-foreground"
                    rows={2}
                    value={q}
                    onChange={e => {
                      const next = [...draftQuestions];
                      next[qi] = e.target.value;
                      onDraftQuestionsChange(next);
                    }}
                  />
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 p-0 shrink-0 mt-1 text-red-500 hover:text-red-600"
                    onClick={() => onDraftQuestionsChange(prev => prev.filter((_, i) => i !== qi))}
                  >
                    <X size={13} />
                  </Button>
                </div>
              ))}
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 text-[#212121]"
                  onClick={() => onDraftQuestionsChange(prev => [...prev, ""])}
                >
                  <Plus size={12} /> Soru Ekle
                </Button>
                <Button
                  size="sm"
                  className="gap-1.5 bg-[#17171c] text-white hover:opacity-85"
                  disabled={savingDefaults}
                  onClick={async () => {
                    onSavingDefaultsChange(true);
                    try {
                      await fetch("/api/admin/schemas/interview-questions", {
                        method: "PUT",
                        headers: { "Content-Type": "application/json", ...getAdminHeaders() },
                        body: JSON.stringify({ questions: draftQuestions.filter(Boolean) }),
                      });
                      onSchemasChange(prev =>
                        prev ? { ...prev, default_interview_questions: draftQuestions } : prev
                      );
                      onEditingDefaultQChange(false);
                      toast.success("Mülakat soruları güncellendi.");
                    } catch {
                      toast.error("Kaydedilemedi.");
                    } finally {
                      onSavingDefaultsChange(false);
                    }
                  }}
                >
                  {savingDefaults ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                  Kaydet
                </Button>
              </div>
            </>
          ) : (
            <ol className="space-y-1.5">
              {schemas.default_interview_questions.map((q, qi) => (
                <li key={qi} className="flex gap-2 text-xs">
                  <span className="font-mono text-muted-foreground shrink-0">{qi + 1}.</span>
                  <span className="text-[#212121]">{q}</span>
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold">Kavram Havuzları (Concept Pools)</CardTitle>
          <CardDescription>
            intake.py → CONCEPT_POOLS — Defne&apos;nin ürün tipine göre seçtiği soru &amp; rol havuzları.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {Object.entries(schemas.concept_pools).map(([name, pool]) => (
            <div key={name} className="border border-border rounded-lg overflow-hidden">
              <button
                type="button"
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/40 transition-colors text-left"
                onClick={() => onExpandedPoolChange(expandedPool === name ? null : name)}
              >
                <div>
                  <div className="font-semibold text-sm">{pool.persona_name}</div>
                  <div className="text-xs text-muted-foreground font-mono">{name}</div>
                </div>
                {expandedPool === name ? (
                  <ChevronDown size={15} className="text-muted-foreground" />
                ) : (
                  <ChevronRight size={15} className="text-muted-foreground" />
                )}
              </button>
              {expandedPool === name && (
                <div className="px-4 pb-4 space-y-3 border-t border-border bg-muted/20">
                  <div className="mt-3">
                    <div className="text-[10px] font-mono text-[#93939f] uppercase tracking-wider mb-1">
                      Odak Alanları
                    </div>
                    <p className="text-xs text-[#616161] leading-relaxed">{pool.focus_areas}</p>
                  </div>
                  <div>
                    <div className="text-[10px] font-mono text-[#93939f] uppercase tracking-wider mb-1.5">
                      Soru Havuzu ({pool.questions.length})
                    </div>
                    <ol className="space-y-1">
                      {pool.questions.map((q, qi) => (
                        <li key={qi} className="flex gap-2 text-xs">
                          <span className="font-mono text-muted-foreground shrink-0">{qi + 1}.</span>
                          <span className="text-[#212121]">{q}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </>
  )}
    </>
  );
}
