"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ThumbsUp, ThumbsDown } from "lucide-react";

interface FeedbackItem {
  id: number;
  username?: string;
  study_id?: string;
  item_type?: string;
  vote: number;
  comment?: string;
  created_at?: string;
}

export function FeedbackTable({ feedbacks }: { feedbacks: FeedbackItem[] }) {
  const [voteFilter, setVoteFilter] = useState<"all" | "like" | "dislike">("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const itemTypes = ["all", ...Array.from(new Set(feedbacks.map(f => f.item_type || "genel")))];

  const filtered = feedbacks.filter(f => {
    const voteOk = voteFilter === "all" || (voteFilter === "like" ? f.vote === 1 : f.vote === -1);
    const typeOk = typeFilter === "all" || (f.item_type || "genel") === typeFilter;
    return voteOk && typeOk;
  });

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">
              Kullanıcı Geri Bildirimleri{" "}
              <span className="text-muted-foreground font-normal text-sm">
                ({filtered.length} / {feedbacks.length} kayıt)
              </span>
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Araştırma mülakat yanıtlarına verilen oylar ve yorumlar.
            </CardDescription>
          </div>

          {/* Filtreler */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Oy Yönü Toggle */}
            <div className="flex rounded-lg border border-border overflow-hidden text-xs font-semibold">
              {(["all", "like", "dislike"] as const).map(v => (
                <button
                  key={v}
                  onClick={() => setVoteFilter(v)}
                  className={`px-3 py-1.5 transition-colors ${
                    voteFilter === v
                      ? v === "like"
                        ? "bg-emerald-600 text-white"
                        : v === "dislike"
                        ? "bg-red-500 text-white"
                        : "bg-primary text-white dark:bg-border-light dark:text-primary"
                      : "bg-card text-muted-foreground hover:bg-soft-stone dark:hover:bg-surface-dark"
                  }`}
                >
                  {v === "all" ? (
                    "Tümü"
                  ) : v === "like" ? (
                    <span className="flex items-center gap-1">
                      <ThumbsUp className="w-3.5 h-3.5" /> Beğeni
                    </span>
                  ) : (
                    <span className="flex items-center gap-1">
                      <ThumbsDown className="w-3.5 h-3.5" /> Beğenmedi
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Tür Filtresi */}
            {itemTypes.length > 2 && (
              <select
                value={typeFilter}
                onChange={e => setTypeFilter(e.target.value)}
                className="text-xs border border-border rounded-lg px-2.5 py-1.5 bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-focus-blue cursor-pointer"
              >
                {itemTypes.map(t => (
                  <option key={t} value={t}>
                    {t === "all" ? "Tüm Türler" : t}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground border-t border-border text-sm">
            {feedbacks.length === 0 ? "Henüz geri bildirim bulunmuyor." : "Seçili filtreye uygun kayıt yok."}
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Tarih</TableHead>
                  <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Kullanıcı</TableHead>
                  <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Araştırma</TableHead>
                  <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Tür</TableHead>
                  <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Oy</TableHead>
                  <TableHead className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Yorum</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(fb => {
                  const hasComment = fb.comment && fb.comment.trim().length > 0;
                  return (
                    <TableRow
                      key={fb.id}
                      className={
                        hasComment
                          ? "bg-amber-50/40 dark:bg-amber-950/10 hover:bg-amber-50/80 dark:hover:bg-amber-950/20"
                          : undefined
                      }
                    >
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                        {fb.created_at ? new Date(fb.created_at).toLocaleString("tr-TR") : "—"}
                      </TableCell>
                      <TableCell className="font-medium text-sm">{fb.username || "—"}</TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">
                        {fb.study_id ? fb.study_id.slice(0, 10) + "…" : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[10px] font-semibold">
                          {fb.item_type || "genel"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {fb.vote === 1 ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-sm">
                            <ThumbsUp className="w-3.5 h-3.5 mr-1" /> Beğendi
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-500 dark:text-red-400 font-bold text-sm">
                            <ThumbsDown className="w-3.5 h-3.5 mr-1" /> Beğenmedi
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-xs min-w-0">
                        {hasComment ? (
                          <span
                            className="inline-block text-xs bg-amber-100 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40 rounded-md px-2 py-0.5 max-w-[200px] truncate"
                            title={fb.comment}
                          >
                            {fb.comment}
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
