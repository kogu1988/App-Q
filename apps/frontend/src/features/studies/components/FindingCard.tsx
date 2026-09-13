"use client";

import { useState } from "react";
import type { ComponentType } from "react";
import { ThumbsUp, ThumbsDown, AlertTriangle, MessageSquare } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { STANCE_TR } from "../lib/constants";
import type { DecisionConfigEntry } from "../lib/constants";
import type { StudyDetail } from "../types";

/** Kanıt zinciri bulgu kartı. Görsel çıktı R1 öncesiyle birebir aynıdır. */
export function FindingCard({ finding, dc, DcIcon, confPct, barColor }: {
  finding: NonNullable<StudyDetail["findings"]>[number];
  dc: DecisionConfigEntry;
  DcIcon: ComponentType<{ size?: number; className?: string }>;
  confPct: number;
  barColor: string;
}) {
  const [showEvidence, setShowEvidence] = useState(false);

  return (
    <Card className="shadow-sm border-[#d9d9dd]/60 hover:border-[#003c33]/30 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <CardTitle className="text-base">{finding.title}</CardTitle>
              <Badge className={`text-[10px] font-bold ${dc.bg} ${dc.color}`}>
                <DcIcon size={12} className="mr-1 inline" />
                {dc.label}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1.5">{finding.summary}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        {/* Confidence Bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-[#616161]">Güven Skoru</span>
            <span className="font-bold text-[#212121]">%{confPct}</span>
          </div>
          <div className="h-2 w-full bg-[#eeece7] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${barColor}`}
              style={{ width: `${confPct}%` }}
            />
          </div>
        </div>

        {/* Support / Refute counts */}
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-emerald-600 font-medium">
            <ThumbsUp size={12} />
            Destekleyen: {finding.supporting_count} persona
          </span>
          <span className="flex items-center gap-1 text-red-500 font-medium">
            <ThumbsDown size={12} />
            İtiraz: {finding.refuting_count}
          </span>
          {finding.neutral_count > 0 && (
            <span className="text-muted-foreground">
              Nötr: {finding.neutral_count}
            </span>
          )}
        </div>

        {/* Contradiction Score */}
        {finding.contradiction_score > 0 && (
          <div className="flex items-center gap-2 p-2 rounded-md bg-amber-50 border border-amber-200 text-xs text-amber-700">
            <AlertTriangle size={14} />
            <span>Çelişki Skoru: {(finding.contradiction_score * 100).toFixed(0)}% — bu bulgu persona grupları arasında görüş ayrılığı içeriyor.</span>
          </div>
        )}

        {/* Evidence Quotes (collapsible) */}
        {finding.evidence && finding.evidence.length > 0 && (
          <div className="border-t border-border pt-3">
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="flex items-center gap-1.5 text-xs font-semibold text-[#1863dc] hover:text-[#1863dc]/80 transition-colors"
            >
              <MessageSquare size={12} />
              Kanıt Alıntıları ({finding.evidence.length})
              <span className="text-[10px]">{showEvidence ? "▲" : "▼"}</span>
            </button>
            {showEvidence && (
              <div className="space-y-2 mt-2">
                {finding.evidence.slice(0, 3).map((ev, ei) => (
                  <div key={ei} className="flex gap-2 p-2.5 bg-[#f5f4f1] rounded-lg border border-border/60 text-xs">
                    <div className="shrink-0">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        (ev.stance === "Innovator" || ev.stance === "EarlyAdopter") ? "bg-emerald-100 text-emerald-700" :
                        ev.stance === "Skeptic" ? "bg-amber-100 text-amber-700" :
                        ev.stance === "Laggard" ? "bg-red-100 text-red-700" :
                        "bg-[#eeece7] text-[#616161]"
                      }`}>{STANCE_TR[ev.stance] || ev.stance}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-[#212121]">{ev.persona_name}</span>
                      <span className="text-muted-foreground ml-1">({ev.sentiment})</span>
                      <p className="italic text-[#616161] mt-0.5 line-clamp-2">&ldquo;{ev.quote}&rdquo;</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Implication */}
        {finding.implication && (
          <div className="border-t border-border pt-3">
            <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">Çıkarım</span>
            <p className="text-xs text-[#616161] leading-relaxed">{finding.implication}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
