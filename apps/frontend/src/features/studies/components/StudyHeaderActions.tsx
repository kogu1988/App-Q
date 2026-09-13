"use client";

import Link from "next/link";
import { Download, Loader2, TrendingUp, Lock, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { studyPdfRequest } from "../api/studies-api";

interface StudyHeaderActionsProps {
  studyId: string;
  isCompleted: boolean;
  interviewsCount: number;
  synthesizing: boolean;
  onSynthesize: () => void;
  /** Kullanıcının planı PDF dışa aktarmaya izin veriyor mu */
  pdfExportEnabled: boolean;
  /** Beyaz etiketli PDF dosya adı kullanılsın mı */
  whiteLabel: boolean;
  onDelete: () => void;
}

/** Study detay başlığındaki eylem butonları (refactor R2-6). */
export function StudyHeaderActions({
  studyId,
  isCompleted,
  interviewsCount,
  synthesizing,
  onSynthesize,
  pdfExportEnabled,
  whiteLabel,
  onDelete,
}: StudyHeaderActionsProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Raporu Olustur — sadece henüz tamamlanmamıs arastirmalarda */}
      {!isCompleted && interviewsCount > 0 && (
        <Button
          className="w-full sm:w-auto gap-2 bg-[#003c33] hover:bg-[#003c33]/85 text-white font-semibold"
          disabled={synthesizing}
          onClick={onSynthesize}
        >
          {synthesizing ? <Loader2 size={16} className="animate-spin" /> : <TrendingUp size={16} />}
          {synthesizing ? "Rapor Olusturuluyor..." : "Raporu Olustur"}
        </Button>
      )}

      {isCompleted && (
        !pdfExportEnabled ? (
          <Button
            variant="outline"
            className="w-full sm:w-auto gap-2 text-[#93939f] border-[#d9d9dd] cursor-not-allowed"
            onClick={() =>
              toast.error(
                <div className="flex flex-col gap-1.5">
                  <span className="font-semibold text-[13px]">PDF İndirme · Flex+ planı gerektirir</span>
                  <span className="text-xs opacity-90">Bu özelliğe erişmek için planınızı yükseltin.</span>
                  <Link href="/client/upgrade" className="text-xs underline font-bold mt-1">Planı Yükselt →</Link>
                </div>,
                { duration: 5000 }
              )
            }
          >
            <Lock size={14} />
            PDF Raporu İndir
          </Button>
        ) : (
          <Button
            className="w-full sm:w-auto btn-pill-primary gap-2"
            onClick={async () => {
              try {
                const res = await studyPdfRequest(studyId);
                if (!res.ok) {
                  const errData = await res.json().catch(() => ({}));
                  if (errData?.detail?.code === "PLAN_GATE" || (typeof errData?.detail === "string" && errData.detail.includes("plan"))) {
                    const required = errData?.detail?.required_plan || "Flex";
                    toast.error(
                      <div className="flex flex-col gap-1.5">
                        <span className="font-semibold text-[13px]">PDF İndirme · {required}+ planı gerektirir</span>
                        <span className="text-xs opacity-90">Bu özelliğe erişmek için planınızı yükseltin.</span>
                        <Link href="/client/upgrade" className="text-xs underline font-bold mt-1">Planı Yükselt →</Link>
                      </div>,
                      { duration: 5000 }
                    );
                    return;
                  }
                  throw new Error(errData?.detail || "Rapor indirilemedi.");
                }
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${whiteLabel ? "Research-Rapor" : "Clarere-Rapor"}-${studyId}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
              } catch {
                toast.error("İndirme işlemi başarısız oldu.");
              }
            }}
          >
            <Download size={16} />
            PDF Raporu İndir
          </Button>
        )
      )}

      {/* ── Sil Butonu + Onay Modalı ── */}
      <Button
        variant="outline"
        size="sm"
        onClick={onDelete}
        className="gap-2 text-red-600 border-red-200 dark:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-950/30 hover:border-red-300 transition-colors"
      >
        <Trash2 size={14} />
        Sil
      </Button>
    </div>
  );
}
