"use client";

import { MessageSquare } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BigFiveRadar } from "./BigFiveRadar";
import { STANCE_TR } from "../lib/constants";
import { readTrait } from "../lib/normalize-study";
import type { Persona, PersonaInterview, StudyDetail } from "../types";

interface PersonasTabProps {
  personas: Persona[];
  interviews: PersonaInterview[];
  study: StudyDetail;
  /** Persona kartından mülakat kaydına geçiş */
  onOpenTranscript: (interviewIndex: number) => void;
}

/** Personalar sekmesi (refactor R2-2). Görsel çıktı R2 öncesiyle birebir aynıdır. */
export function PersonasTab({ personas, interviews, study, onOpenTranscript }: PersonasTabProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div>
        <h2 className="text-xl font-bold text-primary dark:text-white">Sentetik Kitle Paneli ({personas.length})</h2>
        <p className="text-muted-foreground text-sm">Araştırmada simüle edilen ve mülakat gerçekleştirilen hedef kitle profilleri.</p>
      </div>

      {personas.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
          Bu araştırmaya ait persona kaydı bulunamadı.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {personas.map((persona: Persona, index: number) => (
            <Card key={persona.id || index} className="shadow-sm border hover:border-border-light dark:hover:border-action-blue/[0.175] hover:shadow-md transition-all duration-300 group flex flex-col justify-between overflow-hidden">
              <div>
                <div className="p-6 bg-muted-surface/50 border-b border-border/50 flex justify-between items-start gap-2">
                  <div className="space-y-0.5">
                    <h3 className="font-bold text-lg text-primary dark:text-white group-hover:text-action-blue dark:group-hover:text-focus-blue transition-colors">
                      {persona.name}
                    </h3>
                    <p className="text-xs text-muted-foreground font-semibold">
                      {persona.role_title || "Sentetik Tüketici"} • {persona.age} Yaşında
                    </p>
                  </div>
                  <Badge className="bg-pale-blue text-action-blue dark:bg-dark-navy/20 dark:text-focus-blue hover:bg-pale-blue border border-border-light dark:border-action-blue/15 text-xs">
                    {persona.segment}
                  </Badge>
                </div>

                <CardContent className="p-6 space-y-4">
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold text-muted-text uppercase tracking-wider block">Biyografi & Karakteristik</span>
                    <p className="text-body-muted text-xs leading-relaxed italic line-clamp-3">
                      &quot;{persona.bio || persona.context}&quot;
                    </p>
                  </div>

                  {/* Slider indicators */}
                  <div className="space-y-3 border-t border-border pt-4">
                    {persona.big_five ? (
                      <>
                        <span className="text-[10px] font-bold text-muted-text uppercase tracking-wider block mb-2">Kişilik Profili (Büyük Beşli)</span>
                        <BigFiveRadar bigFive={persona.big_five || {}} />
                        {[
                          { label: "Açıklık (Openness)",              key: "Openness" as const,          color: "bg-sky-500" },
                          { label: "Sorumluluk (Conscientiousness)",   key: "Conscientiousness" as const, color: "bg-blue-500" },
                          { label: "Dışadönüklük (Extraversion)",      key: "Extraversion" as const,      color: "bg-orange-500" },
                          { label: "Uyumluluk (Agreeableness)",        key: "Agreeableness" as const,     color: "bg-teal-500" },
                          { label: "Duygusal Denge (Neuroticism)",     key: "Neuroticism" as const,       color: "bg-rose-500" },
                        ].map(trait => {
                          const value = readTrait(persona.big_five, trait.key);
                          return (
                          <div key={trait.label} className="space-y-1">
                            <div className="flex justify-between text-[10px] font-semibold">
                              <span className="text-muted-foreground">{trait.label}</span>
                              <span className="text-ink ">{value}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-soft-stone rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${trait.color} rounded-full`} 
                                style={{ width: `${value}%` }}
                              />
                            </div>
                          </div>
                          );
                        })}
                      </>
                    ) : (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-semibold">
                            <span className="text-muted-foreground">Fiyat Hassasiyeti</span>
                            <span className="text-ink ">{persona.price_sensitivity}/5</span>
                          </div>
                          <div className="h-1.5 w-full bg-soft-stone rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-sky-500 rounded-full" 
                              style={{ width: `${(persona.price_sensitivity / 5) * 100}%` }}
                            />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between text-[10px] font-semibold">
                            <span className="text-muted-foreground">Dijital Güven</span>
                            <span className="text-ink ">{persona.digital_confidence}/5</span>
                          </div>
                          <div className="h-1.5 w-full bg-soft-stone rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500 rounded-full" 
                              style={{ width: `${(persona.digital_confidence / 5) * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Stance + SES details */}
                  <div className="space-y-2 border-t border-border/50 pt-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted-foreground">Pazar Yaklaşımı:</span>
                      <Badge variant="outline" className="font-semibold text-body-muted ">
                        {STANCE_TR[persona.stance] || persona.stance}
                      </Badge>
                    </div>
                    {(persona.ses_group || persona.respondent_type) && (
                      <div className="flex flex-wrap gap-1.5">
                        {persona.ses_group && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                            persona.ses_group === "AB" ? "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/20 dark:border-amber-800 dark:text-amber-400" :
                            persona.ses_group === "C1" ? "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/20 dark:border-blue-800 " :
                            persona.ses_group === "C2" ? "bg-muted-surface border-hairline text-body-muted " :
                            "bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/20 dark:border-rose-800 dark:text-rose-400"
                          }`}>SES {persona.ses_group}</span>
                        )}
                        {persona.respondent_type && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-pale-blue border border-border-light text-action-blue dark:bg-dark-navy/20 dark:border-action-blue/60 dark:text-focus-blue">
                            {({
                              potential_customer: "Potansiyel",
                              competitor_user: "Rakip",
                              churned_user: "Kaybedilmiş",
                              decision_maker: "Karar Verici",
                              individual_user: "Bireysel",
                            } as Record<string, string>)[persona.respondent_type] ?? persona.respondent_type}
                          </span>
                        )}
                        {persona.settlement_type && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 border border-emerald-200 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-800 dark:text-emerald-400">
                            {persona.settlement_type}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {persona.attributes && ["Current workflow", "Decision trigger", "Buying friction"].some(k => persona.attributes?.[k]) && (
                    <div className="space-y-2 border-t border-border/50 pt-3">
                      {[
                        { key: "Current workflow", label: "Mevcut İş Akışı" },
                        { key: "Decision trigger", label: "Karar Tetikleyicisi" },
                        { key: "Buying friction", label: "Satın Alma Sürtünmesi" },
                      ].filter(a => persona.attributes?.[a.key]).map(a => (
                        <div key={a.key} className="text-[11px] leading-relaxed">
                          <span className="font-bold text-muted-text uppercase tracking-wider">{a.label}: </span>
                          <span className="text-body-muted dark:text-muted-text">{persona.attributes?.[a.key]}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </div>

              <div className="px-6 pb-6 pt-0 flex justify-end border-t border-border/40 mt-auto">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-xs text-action-blue dark:text-focus-blue hover:text-action-blue dark:hover:text-focus-blue font-semibold gap-1.5 p-0 hover:bg-transparent"
                  onClick={() => {
                    // Find index in interviews list
                    const intIdx = interviews.findIndex((i: PersonaInterview) => i.persona?.name === persona.name);
                    if (intIdx !== -1) {
                      onOpenTranscript(intIdx);
                    }
                  }}
                >
                  <MessageSquare size={14} />
                  Mülakat Kayıtlarını İncele
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* SES x Stance Cross-Tab */}
      {study?.ses_cross_tab && study.ses_cross_tab.length > 0 && (
        <Card className="shadow-sm border-border-light dark:border-action-blue/15">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Sosyo-Ekonomik Grup × Duruş</CardTitle>
            <CardDescription>Sosyo-ekonomik gruplara göre pazar yaklaşımı dağılımı.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 pr-4 text-xs font-semibold text-muted-foreground uppercase">SES</th>
                    {["Innovator","EarlyAdopter","Mainstream","Laggard","Skeptic"].map(s => (
                      <th key={s} className="text-center py-2 px-2 text-xs font-semibold text-muted-foreground uppercase">{STANCE_TR[s] || s}</th>
                    ))}
                    <th className="text-center py-2 pl-4 text-xs font-semibold text-muted-foreground uppercase">Toplam</th>
                    <th className="text-left py-2 pl-4 text-xs font-semibold text-muted-foreground uppercase">Baskın</th>
                  </tr>
                </thead>
                <tbody>
                  {study.ses_cross_tab.map(row => (
                    <tr key={row.ses_group} className="border-b border-border/50 hover:bg-muted-surface dark:hover:bg-ink/30">
                      <td className="py-2 pr-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                          row.ses_group === "AB" ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400" :
                          row.ses_group === "C1" ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 " :
                          row.ses_group === "C2" ? "bg-soft-stone text-body-muted " :
                          "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400"
                        }`}>{row.ses_group}</span>
                      </td>
                      {["Innovator","EarlyAdopter","Mainstream","Laggard","Skeptic"].map(s => {
                        const sc = row.stance_counts as Record<string,number>;
                        const count = sc?.[s] ?? 0;
                        const max = sc ? Math.max(...Object.values(sc)) : 0;
                        return (
                          <td key={s} className="text-center py-2 px-2">
                            {count > 0 ? (
                              <span
                                className="inline-flex w-8 h-8 rounded-md text-xs font-bold items-center justify-center transition-colors"
                                style={{
                                  backgroundColor:
                                    count === max
                                      ? "var(--color-action-blue)"
                                      : `color-mix(in srgb, var(--color-action-blue) ${((0.15 + (count / max) * 0.55) * 100).toFixed(1)}%, transparent)`,
                                  color: count === max ? "var(--color-on-primary)" : "var(--color-primary)",
                                }}
                              >{count}</span>
                            ) : <span className="text-muted-foreground">—</span>}
                          </td>
                        );
                      })}
                      <td className="text-center py-2 pl-4 font-semibold">{row.total}</td>
                      <td className="py-2 pl-4"><Badge variant="outline" className="text-xs">{row.dominant_stance}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Respondent Type Summary */}
      {study?.respondent_type_summary && study.respondent_type_summary.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Katılımcı Tipi Bazında Özet</CardTitle>
            <CardDescription>Her katılımcı tipi için öne çıkan ağrı noktası ve itiraz.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {study.respondent_type_summary.map(rt => (
                <div key={rt.respondent_type} className="p-4 border border-border rounded-xl space-y-2 hover:border-border-light dark:hover:border-action-blue/[0.14] transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-ink dark:text-border-light">{rt.label}</span>
                    <Badge variant="secondary" className="text-xs">{rt.count} kişi</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Ort. fiyat hassasiyeti: <strong className="text-body-muted ">{rt.avg_price_sensitivity.toFixed(1)}/10</strong>
                  </div>
                  {rt.top_pain && (
                    <div className="text-xs bg-rose-50 dark:bg-rose-950/20 border border-rose-100 rounded-lg p-2 text-rose-700 dark:text-rose-400 italic line-clamp-2">
                      &ldquo;{rt.top_pain}&rdquo;
                    </div>
                  )}
                  {rt.top_objection && (
                    <div className="text-xs bg-amber-50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30 rounded-lg p-2 text-amber-700 dark:text-amber-400 italic line-clamp-2">
                      &ldquo;{rt.top_objection}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
