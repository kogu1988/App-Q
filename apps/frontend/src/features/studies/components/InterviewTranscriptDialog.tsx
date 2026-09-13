"use client";

import { MessageSquare, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { STANCE_TR } from "../lib/constants";
import type { InterviewTurn, PersonaInterview, StudyDetail } from "../types";

interface InterviewTranscriptDialogProps {
  interview: PersonaInterview;
  study: StudyDetail;
  planType: string;
  followUpText: string;
  onFollowUpTextChange: (value: string) => void;
  sendingFollowUp: boolean;
  onFollowUp: (personaId: string) => void;
}

/** Persona mülakat transkripti + takip sorusu dialogu (refactor R2-4). */
export function InterviewTranscriptDialog({
  interview,
  study,
  planType,
  followUpText,
  onFollowUpTextChange,
  sendingFollowUp,
  onFollowUp,
}: InterviewTranscriptDialogProps) {
  const item = interview;
  return (
    <Dialog>
      <DialogTrigger render={
        <Button variant="outline" className="w-full text-xs font-semibold gap-2 border-[#d9d9dd] hover:bg-[#f5f4f1] text-[#17171c] dark:border-[rgba(255,255,255,0.12)] dark:text-white dark:hover:bg-[#2c2c33]">
          <MessageSquare size={14} />
          Transkript Görüntüle
        </Button>
      } />
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col p-0 overflow-hidden rounded-2xl">
        <DialogHeader className="px-6 py-5 border-b border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)] bg-[#eeece7] dark:bg-[#212121]">
          <DialogTitle className="text-lg">Mülakat Transkripti · {item.persona?.name}</DialogTitle>
          <DialogDescription className="text-[#616161] dark:text-[#93939f]">
            {item.persona?.role_title} · {item.persona?.age} Yaş · {item.persona?.city} · {STANCE_TR[item.persona?.stance || ""] || item.persona?.stance} Profil
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 bg-white dark:bg-[#17171c]">
          {item.turns?.map((turn: InterviewTurn, turnIdx: number) => (
            <div key={turnIdx} className="space-y-5 border-b border-[#f2f2f2] dark:border-[rgba(255,255,255,0.08)] pb-6 last:border-0 last:pb-0">
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f]">Soru {turnIdx + 1}</span>
                <div className="h-px flex-1 bg-[#f2f2f2] dark:bg-[rgba(255,255,255,0.08)]" />
              </div>

              {/* Moderatör sorusu */}
              <div className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-full bg-[#003c33] dark:bg-[#edfce9] text-white dark:text-[#003c33] flex items-center justify-center shrink-0">
                  <MessageSquare size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f] mb-1.5">Moderatör (AI)</p>
                  <p className="text-[15px] leading-relaxed text-[#212121] dark:text-[#e5e7eb]">{turn.question}</p>
                </div>
              </div>

              {/* Persona yanıtı */}
              <div className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-full bg-[#ff7759] text-white flex items-center justify-center font-bold text-xs shrink-0">
                  {item.persona?.name.charAt(0) || "P"}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f] mb-1.5">{item.persona?.name}</p>
                  <p className="text-[15px] leading-relaxed text-[#212121] dark:text-[#e5e7eb]">{turn.answer}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        <DialogFooter className="px-6 py-4 border-t border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)] bg-[#f5f4f1]/60 dark:bg-[#212121] flex flex-col gap-3">
          {(() => {
            const followUpCount = (() => {
              let count = 0;
              study?.interviews?.forEach(inv => {
                inv.turns?.forEach(t => {
                  if (t.tags?.includes("FOLLOW-UP")) {
                    count++;
                  }
                });
              });
              return count;
            })();

            const currentPlanType = planType || "Free";
            const isFree = currentPlanType === "Free";
            const isLimited = currentPlanType === "Starter" || currentPlanType === "Flex";
            const isLimitReached = isLimited && followUpCount >= 3;

            let inputPlaceholder = `${item.persona?.name} isimli personaya ekstra bir soru sorun...`;
            let isDisabled = sendingFollowUp;
            let badgeText = "";
            let badgeColor = "bg-[#eeece7] text-[#616161] dark:bg-[#2c2c33] dark:text-[#93939f]";

            if (isFree) {
              inputPlaceholder = "Takip sorusu · Flex+ planı gerektirir.";
              isDisabled = true;
              badgeText = "Takip Sorusu · Flex+ Gerekli";
              badgeColor = "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/40";
            } else if (isLimitReached) {
              inputPlaceholder = "Takip sorusu limitine ulaştınız (3/3). Planınızı yükseltin.";
              isDisabled = true;
              badgeText = "Limit Doldu (3/3)";
              badgeColor = "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/40";
            } else if (isLimited) {
              badgeText = `Takip Sorusu Limiti: ${followUpCount}/3`;
              badgeColor = "bg-[#f1f5ff] text-[#1863dc] border-[#e5e7eb] dark:bg-[#071829] dark:text-[#4c6ee6] dark:border-[rgba(24,99,220,0.15)]";
            } else {
              badgeText = "Sınırsız Takip Sorusu";
              badgeColor = "bg-[#edfce9] text-[#003c33] border-[#d9d9dd] dark:bg-[#003c33]/20 dark:text-[#edfce9] dark:border-[#003c33]/40";
            }

            return (
              <div className="w-full space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f]">Persona ile Etkileşim (Probing)</span>
                  <Badge variant="outline" className={`text-[11px] font-semibold ${badgeColor}`}>
                    {badgeText}
                  </Badge>
                </div>
                <div className="flex gap-2 w-full">
                  <Textarea
                    placeholder={inputPlaceholder}
                    className="min-h-[60px] resize-none text-sm flex-1"
                    value={followUpText}
                    onChange={(e) => onFollowUpTextChange(e.target.value)}
                    disabled={isDisabled}
                  />
                  <Button
                    onClick={() => item.persona?.id && onFollowUp(item.persona.id)}
                    disabled={isDisabled || !followUpText.trim()}
                    className="h-auto px-6 font-semibold bg-[#17171c] hover:opacity-85 text-white"
                  >
                    {sendingFollowUp ? <Loader2 className="animate-spin w-4 h-4" /> : "Sor"}
                  </Button>
                </div>
                <span className="text-[11px] text-[#93939f]">Bu özellik ile personaya mülakat sonrası ek soru yöneltip daha derin içgörü elde edebilirsiniz.</span>
              </div>
            );
          })()}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
