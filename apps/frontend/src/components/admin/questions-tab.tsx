"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
} from "@/components/ui/dialog";
import {
  Heart,
  HeartOff,
  Trash2,
  Pencil,
  Check,
  X,
} from "lucide-react";
import type {
  CuratedQuestion,
} from "@/features/admin/types";

interface QuestionsTabProps {
  questions: CuratedQuestion[];
  editingQuestion: number | null;
  onEditingQuestionChange: (id: number | null) => void;
  editPurpose: string;
  onEditPurposeChange: (value: string) => void;
  onRequestDelete: (id: number) => void;
  onToggleLike: (id: number, current: boolean) => void;
  onSavePurpose: (id: number) => void;
}

/** Soru koleksiyonu sekmesi (refactor R3). */
export function QuestionsTab({
  questions,
  editingQuestion,
  onEditingQuestionChange,
  editPurpose,
  onEditPurposeChange,
  onRequestDelete,
  onToggleLike,
  onSavePurpose,
}: QuestionsTabProps) {
  return (
    <>
  <div className="mb-6">
    <p className="text-sm text-muted-foreground">
      Araştırma motorunun sihirbaz sohbetinde kullandığı seçilmiş soru havuzu. Beğenilen sorular aktif
      simülasyonlarda öneri olarak kullanılır.
    </p>
  </div>
  <div className="flex justify-between items-center mb-2">
    <span className="text-sm font-semibold text-muted-foreground">{questions.length} soru</span>
  </div>
  <Card>
    <CardContent className="pt-6">
      {questions.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
          Henüz koleksiyonda soru bulunmuyor. Simülasyonlar tamamlandıkça sorular buraya eklenir.
        </div>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
          {questions.map(q => (
            <div
              key={q.id}
              className="p-4 border border-border rounded-xl hover:border-[#d9d9dd] transition-colors space-y-2"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-[#212121] font-medium leading-relaxed flex-1">{q.question}</p>
                <div className="flex items-center gap-1.5 shrink-0">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onToggleLike(q.id, q.is_liked)}
                    className={`h-8 w-8 p-0 ${
                      q.is_liked ? "text-red-500 hover:text-red-600" : "text-muted-foreground hover:text-red-400"
                    }`}
                  >
                    {q.is_liked ? <Heart size={15} fill="currentColor" /> : <HeartOff size={15} />}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      onEditingQuestionChange(q.id);
                      onEditPurposeChange(q.purpose_context || "");
                    }}
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                  >
                    <Pencil size={14} />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onRequestDelete(q.id)}
                    className="h-8 w-8 p-0 text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                {q.research_category && <Badge variant="outline" className="text-[10px]">{q.research_category}</Badge>}
                {q.research_title && <span>&quot;{q.research_title}&quot;</span>}
                {!q.is_liked && (
                  <Badge variant="secondary" className="text-[10px] text-[#93939f]">
                    Pasif (simülasyonda kullanılmıyor)
                  </Badge>
                )}
              </div>

              {editingQuestion === q.id && (
                <div className="flex gap-2 mt-2 animate-in fade-in slide-in-from-top-1 duration-200">
                  <Input
                    value={editPurpose}
                    onChange={e => onEditPurposeChange(e.target.value)}
                    placeholder="Bu sorunun amacı / bağlamı..."
                    className="text-xs h-8 flex-1 bg-background text-foreground"
                  />
                  <Button
                    size="sm"
                    className="h-8 gap-1.5 text-xs bg-[#17171c] text-white hover:opacity-85"
                    onClick={() => onSavePurpose(q.id)}
                  >
                    <Check size={13} />
                    Kaydet
                  </Button>
                  <Button size="sm" variant="ghost" className="h-8" onClick={() => onEditingQuestionChange(null)}>
                    <X size={13} />
                  </Button>
                </div>
              )}
              {q.purpose_context && editingQuestion !== q.id && (
                <p className="text-xs text-[#ff7759]/80 italic">Amaç: {q.purpose_context}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </CardContent>
  </Card>
    </>
  );
}
