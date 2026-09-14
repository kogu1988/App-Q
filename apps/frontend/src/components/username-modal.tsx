"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Logo from "@/components/logo";
import { setSessionMarker } from "@/lib/auth";

interface UsernameModalProps {
  onComplete: (username: string) => void;
}

function isValidUsername(v: string) {
  return /^[a-zA-Z0-9_-]{2,20}$/.test(v);
}

export function UsernameModal({ onComplete }: UsernameModalProps) {
  const [value, setValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const searchParams = useSearchParams();
  const planParam = searchParams.get("plan");



  const planLabel: Record<string, string> = {
    starter: "Starter",
    pro: "Pro",
    enterprise: "Enterprise",
  };
  const selectedPlan = planParam ? planLabel[planParam.toLowerCase()] ?? "" : "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    // Eski oturum token'ını temizle — kullanıcı değişiminde karışma olmasın.
    // Parola verilirse register sonrası yeni token set edilecek.
    localStorage.removeItem("clarere_token");

    if (!isValidUsername(value)) {
      setError("2-20 karakter, sadece harf, rakam, _ veya - kullanabilirsiniz.");
      return;
    }

    if (password && password.length < 6) {
      setError("Parola en az 6 karakter olmalı.");
      return;
    }

    setLoading(true);
    try {
      // 1. JWT kayıt (parola verildiyse) → access token sakla
      if (password) {
        const authRes = await fetch(`/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: value, password }),
        });
        if (!authRes.ok) {
          const data = await authRes.json().catch(() => ({}));
          setError(data.detail || "Kayıt başarısız.");
          return;
        }
        const authData = await authRes.json();
        localStorage.setItem("clarere_token", authData.access_token);
      }

      // 2. Kullanıcı + plan (geriye dönük uyumluluk; ?plan= yükseltmesi)
      const res = await fetch(`/api/client/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: value,
          new_plan: selectedPlan,
          billing_cycle: "monthly",
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Bir hata oluştu, tekrar deneyin.");
        return;
      }

      // Başarılı: localStorage'a kaydet
      localStorage.setItem("clarere_username", value);
      setSessionMarker(); // middleware derin bağlantı koruması
      onComplete(value);
    } catch {
      setError("Sunucuya bağlanılamadı. Lütfen tekrar deneyin.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 backdrop-blur-md">
      <div className="w-full max-w-sm mx-4 rounded-2xl border border-border bg-card shadow-2xl p-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <Logo size={36} className="text-primary" />
          <span className="font-bold text-lg tracking-tight">Clarere</span>
        </div>

        {/* Başlık */}
        <div className="space-y-1.5">
          <h2 className="text-xl font-bold tracking-tight">Hoş geldiniz</h2>
          <p className="text-sm text-muted-foreground">
            Devam etmek için bir kullanıcı adı seçin.{" "}
            <span className="text-foreground/70">Parola opsiyoneldir — güvenli JWT girişi için belirleyin.</span>
          </p>
        </div>

        {/* Plan bilgisi (varsa) */}
        {selectedPlan && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-accent/10 border border-accent/20 text-sm">
            <span className="text-accent text-xs">✦</span>
            <span>
              <span className="font-semibold text-accent">{selectedPlan}</span> planı seçildi — giriş sonrası aktif edilecek.
            </span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="username-input" className="text-sm font-medium">
              Kullanıcı adı
            </label>
            <input
              id="username-input"
              type="text"
              autoFocus
              value={value}
              onChange={(e) => {
                setValue(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ""));
                setError("");
              }}
              maxLength={20}
              placeholder="ornek-kullanici"
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
            />
            {error && (
              <p className="text-xs text-red-500 font-medium">{error}</p>
            )}
            <p className="text-[11px] text-muted-foreground">
              2–20 karakter · harf, rakam, _ veya -
            </p>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="password-input" className="text-sm font-medium">
              Parola <span className="text-muted-foreground/70 font-normal">(opsiyonel)</span>
            </label>
            <input
              id="password-input"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              placeholder="••••••"
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
            />
            <p className="text-[11px] text-muted-foreground">
              En az 6 karakter. Boş bırakırsanız oturum kimliğiyle devam edersiniz.
            </p>
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            className="w-full py-2.5 rounded-xl bg-primary text-white font-semibold text-sm hover:opacity-85 transition-opacity"
          >
            {loading ? "Yükleniyor…" : "Başla →"}
          </button>
        </form>

        <p className="text-[11px] text-center text-muted-foreground/70">
          Bu cihaza özel oturum kimliğinizdir. Dilediğiniz zaman değiştirebilirsiniz.
        </p>
      </div>
    </div>
  );
}
