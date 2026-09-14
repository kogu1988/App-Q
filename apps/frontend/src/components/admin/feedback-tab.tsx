"use client";

import { Card, CardContent } from "@/components/ui/card";
import {
} from "@/components/ui/dialog";
import {
} from "lucide-react";
import { FeedbackTable } from "@/components/admin/feedback-table";
import type {
  FeedbackItem,
} from "@/features/admin/types";

interface FeedbackTabProps {
  feedbacks: FeedbackItem[];
}

/** Geri bildirim sekmesi: ozet kartlari + tablo (refactor R3). */
export function FeedbackTab({ feedbacks }: FeedbackTabProps) {
  return (
    <>
  <div className="mb-6">
    <p className="text-sm text-muted-foreground">
      Kullanıcılardan gelen simülasyon ve sistem geri bildirimleri ile genel değerlendirme skorları.
    </p>
  </div>

  {(() => {
    const total = feedbacks.length;
    const likes = feedbacks.filter(f => f.vote === 1).length;
    const dislikes = feedbacks.filter(f => f.vote === -1).length;
    const withComment = feedbacks.filter(f => f.comment && f.comment.trim().length > 0).length;
    const likeRate = total > 0 ? Math.round((likes / total) * 100) : 0;
    const commentRate = total > 0 ? Math.round((withComment / total) * 100) : 0;

    const typeCounts: Record<string, number> = {};
    feedbacks.forEach(f => {
      const t = f.item_type || "genel";
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });
    const topType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";

    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card className="border-l-4 border-l-[#93939f] shadow-sm">
          <CardContent className="pt-5 pb-4">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[#93939f]">Toplam Kayıt</p>
            <p className="text-4xl font-black text-[#17171c] dark:text-[#e5e7eb] mt-1">{total}</p>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-emerald-600 font-semibold">{likes} beğeni</span>
              {" · "}
              <span className="text-red-500 font-semibold">{dislikes} beğenmedi</span>
            </p>
          </CardContent>
        </Card>

        <Card
          className={`border-l-4 shadow-sm ${
            likeRate >= 70
              ? "border-l-emerald-500"
              : likeRate >= 40
              ? "border-l-amber-500"
              : "border-l-red-500"
          }`}
        >
          <CardContent className="pt-5 pb-4">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[#93939f]">Beğeni Oranı</p>
            <p
              className={`text-4xl font-black mt-1 ${
                likeRate >= 70
                  ? "text-emerald-600 dark:text-emerald-400"
                  : likeRate >= 40
                  ? "text-amber-600 dark:text-amber-400"
                  : "text-red-600 dark:text-red-400"
              }`}
            >
              %{likeRate}
            </p>
            <div className="mt-2 h-1.5 bg-[#eeece7] dark:bg-[#2c2c33] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  likeRate >= 70 ? "bg-emerald-500" : likeRate >= 40 ? "bg-amber-500" : "bg-red-500"
                }`}
                style={{ width: `${likeRate}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-sky-400 shadow-sm">
          <CardContent className="pt-5 pb-4">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[#93939f]">Yorum İçeren</p>
            <p className="text-4xl font-black text-sky-600 dark:text-sky-400 mt-1">%{commentRate}</p>
            <p className="text-xs text-muted-foreground mt-1">{withComment} kayıtta yorum var</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-indigo-400 shadow-sm">
          <CardContent className="pt-5 pb-4">
            <p className="text-[11px] font-mono uppercase tracking-wider text-[#93939f]">
              En Çok Değerlendirilen
            </p>
            <p className="text-lg font-black text-[#1863dc] dark:text-[#4c6ee6] mt-1 truncate">{topType}</p>
            <p className="text-xs text-muted-foreground mt-1">{typeCounts[topType] ?? 0} kayıt</p>
          </CardContent>
        </Card>
      </div>
    );
  })()}

  <FeedbackTable feedbacks={feedbacks} />
    </>
  );
}
