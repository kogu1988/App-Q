"use client";

import { Loader2, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface DeleteQuestionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  deleting: boolean;
  onConfirm: () => void;
}

/** Soru silme onay modalı (refactor R3). Metin ve görsel yapı birebir korunmuştur. */
export function DeleteQuestionModal({ open, onOpenChange, deleting, onConfirm }: DeleteQuestionModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-50 border border-red-200 shrink-0">
              <Trash2 size={18} className="text-red-600" />
            </div>
            <div>
              <DialogTitle className="text-base">Soruyu Sil</DialogTitle>
              <DialogDescription className="text-sm mt-0.5">
                Bu soru koleksiyondan kalıcı olarak silinecek. Bu işlem geri alınamaz.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-2">
          <button
            onClick={() => onOpenChange(false)}
            className="flex-1 h-9 px-4 text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors"
          >
            İptal
          </button>
          <button
            onClick={onConfirm}
            disabled={deleting}
            className="flex-1 h-9 px-4 text-sm font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {deleting && <Loader2 size={14} className="animate-spin" />}
            Evet, Sil
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
