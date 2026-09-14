"use client";

import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import Logo from "@/components/logo";

interface AdminHeaderProps {
  adminKey: string;
  onAdminKeyChange: (value: string) => void;
}

/** Admin panel başlığı + admin anahtarı girişi (refactor R3). */
export function AdminHeader({ adminKey, onAdminKeyChange }: AdminHeaderProps) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-6">
      <div className="flex items-center gap-4">
        <Link href="/" className="flex items-center gap-2">
          <Logo size={36} strokeColor="#17171c" />
          <span className="font-semibold text-base text-[#17171c]">Clarere</span>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-primary">Clarere Yönetici Paneli</h1>
          <p className="text-sm text-muted-foreground">Sistem, Kullanıcı ve İçerik Yönetimi</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="password"
          value={adminKey}
          onChange={(e) => onAdminKeyChange(e.target.value)}
          placeholder="Admin anahtarı"
          className="w-48 px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <Button
          onClick={() => {
            localStorage.setItem("clarere_admin_key", adminKey.trim());
            toast.success("Admin anahtarı kaydedildi.");
          }}
          variant="outline"
          size="sm"
        >
          Kaydet
        </Button>
      </div>
    </header>
  );
}
