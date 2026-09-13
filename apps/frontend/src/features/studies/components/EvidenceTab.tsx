"use client";

import { Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FindingCard } from "./FindingCard";
import { DECISION_CONFIG } from "../lib/constants";
import type { StudyDetail } from "../types";

interface EvidenceTabProps {
  study: StudyDetail;
}

/** Kanıt zinciri ve karar katmanı sekmesi (refactor R2-5). */
export function EvidenceTab({ study }: EvidenceTabProps) {
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div>
        <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Kanıt Zinciri ve Karar Katmanı</h2>
        <p className="text-muted-foreground text-sm">Mülakatlardan çıkarılan bulgular, kanıt alıntıları ve karar sinyalleri.</p>
      </div>

      {(!study?.findings || study.findings.length === 0) ? (
        <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
          <p>Bu araştırmaya ait kanıt zinciri verisi bulunamadı.</p>
          <p className="text-xs mt-2 text-muted-foreground/70">Sentez raporu oluşturulduktan sonra bulgular ve kanıt zinciri burada görüntülenecektir.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Decision Items Summary */}
          {study?.decision_items && study.decision_items.length > 0 && (
            <Card className="shadow-sm border-[#003c33]/20">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Zap size={18} className="text-amber-500" />
                  Karar Önerileri
                </CardTitle>
                <CardDescription>Kanıt zincirinden türetilen aksiyon önerileri.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {study.decision_items.map((di, i) => {
                  const dc = DECISION_CONFIG[di.signal] || DECISION_CONFIG.INVESTIGATE;
                  const DcIcon = dc.icon;
                  return (
                    <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${dc.bg}`}>
                      <DcIcon size={16} className={`shrink-0 mt-0.5 ${dc.color}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm text-[#212121]">{di.title}</span>
                          <Badge className={`text-[10px] ${dc.bg} ${dc.color}`}>{dc.label}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{di.recommended_action}</p>
                        <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground">
                          <span>Güven: %{Math.round(di.confidence * 100)}</span>
                          <span className="text-emerald-600">Destekleyen: {di.supporting_count}</span>
                          <span className="text-red-500">İtiraz: {di.refuting_count}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {/* Findings List */}
          {study.findings.map((finding) => {
            const dc = DECISION_CONFIG[finding.decision_signal] || DECISION_CONFIG.INVESTIGATE;
            const DcIcon = dc.icon;
            const confPct = Math.round(finding.confidence * 100);
            const barColor = confPct >= 75 ? "bg-emerald-500" : confPct >= 50 ? "bg-amber-500" : "bg-red-500";

            return (
              <FindingCard key={finding.id} finding={finding} dc={dc} DcIcon={DcIcon} confPct={confPct} barColor={barColor} />
            );
          })}
        </div>
      )}
    </div>
  );
}
