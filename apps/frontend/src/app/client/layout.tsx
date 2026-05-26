"use client";

import Link from "next/link";
import { Toaster } from "@/components/ui/sonner";
import { useState, useEffect, Suspense } from "react";
import { Menu, X, LogOut, User, Zap, ArrowUpRight, FileText } from "lucide-react";
import { UsernameModal } from "@/components/username-modal";
import { useClientPlan } from "@/hooks/use-client-plan";
import Logo from "@/components/logo";

interface SidebarStudy {
  id: string;
  title?: string;
}

// ── Sidebar Studies Widget ───────────────────────────────────────────────────

function SidebarStudiesWidget() {
  const [studies, setStudies] = useState<SidebarStudy[]>([]);

  useEffect(() => {
    const username = localStorage.getItem("appq_username") || "";
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000";
    const headers: Record<string, string> = username ? { "X-Username": username } : {};
    fetch(`${apiBase}/api/client/studies`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        // En son 5 araştırmayı gösterelim
        setStudies(data.slice(0, 5));
      })
      .catch(() => {});
  }, []);

  if (studies.length === 0) return null;

  return (
    <div className="pt-4 mt-2 border-t border-border/50">
      <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2 px-3">
        Son Araştırmalar
      </h4>
      <div className="flex flex-col gap-0.5">
        {studies.map(study => (
          <Link 
            key={study.id} 
            href={`/client/studies/${study.id}`}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground text-[12px] font-medium transition-colors group"
          >
            <FileText size={13} className="shrink-0 text-muted-foreground group-hover:text-foreground transition-colors" />
            <span className="truncate">{study.title || "İsimsiz Proje"}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

// ── Sidebar Plan Widget ──────────────────────────────────────────────────────

function SidebarPlanWidget() {
  const { plan, loading } = useClientPlan();

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-background p-3 space-y-2 animate-pulse">
        <div className="h-3 bg-muted rounded w-2/3" />
        <div className="h-2 bg-muted rounded w-full" />
        <div className="h-2 bg-muted rounded w-1/2" />
      </div>
    );
  }

  const used = plan.period_simulations;
  const max = plan.limits.max_simulations;
  const isUnlimited = max >= 9999;
  const pct = isUnlimited ? 100 : Math.min(Math.round((used / max) * 100), 100);
  const isNearLimit = !isUnlimited && pct >= 80;
  const remaining = isUnlimited ? null : Math.max(0, max - used);

  const periodEnd = (() => {
    if (!plan.period_start) return null;
    const start = new Date(plan.period_start);
    const days = plan.billing_cycle === "annual" ? 365 : 30;
    start.setDate(start.getDate() + days);
    return start.toLocaleDateString("tr-TR", { day: "numeric", month: "long" });
  })();

  const PLAN_COLORS: Record<string, { bg: string; text: string }> = {
    Free: { bg: "bg-[#eeece7]", text: "text-[#17171c]" },
    Starter: { bg: "bg-[#f1f5ff]", text: "text-[#1863dc]" },
    Pro: { bg: "bg-[#edfce9]", text: "text-[#003c33]" },
    Enterprise: { bg: "bg-amber-100", text: "text-amber-800" },
  };
  const planColor = PLAN_COLORS[plan.plan_type] ?? PLAN_COLORS.Free;
  const showUpgrade = plan.plan_type === "Free" || plan.plan_type === "Starter";

  return (
    <div className={`rounded-xl border p-3 space-y-2.5 transition-colors ${isNearLimit ? "border-amber-300 bg-amber-50" : "border-border bg-background"
      }`}>
      {/* Plan badge + icon */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Zap size={12} className={isNearLimit ? "text-amber-500" : "text-muted-foreground"} />
          <span className="text-[11px] font-semibold text-muted-foreground">Plan</span>
        </div>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${planColor.bg} ${planColor.text}`}>
          {plan.plan_type}
        </span>
      </div>

      {/* Usage */}
      {!isUnlimited ? (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-muted-foreground">
              Bu dönem kullanım
            </span>
            <span className={`text-[11px] font-bold tabular-nums ${isNearLimit ? "text-amber-600" : "text-[#212121]"
              }`}>
              {used} / {max}
            </span>
          </div>
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${isNearLimit ? "bg-amber-500" : "bg-[#003c33]"
                }`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-[10px] text-muted-foreground/70">
            {remaining === 0
              ? "Limit doldu"
              : `${remaining} araştırma hakkı kaldı`}
          </p>
        </div>
      ) : (
        <p className="text-[11px] text-[#003c33] font-semibold">Sinirsiz araştırma</p>
      )}

      {/* Period reset */}
      {periodEnd && (
        <p className="text-[10px] text-muted-foreground/60 border-t border-border pt-2">
          Sıfırlanma: <span className="font-medium text-muted-foreground">{periodEnd}</span>
        </p>
      )}

      {/* Upgrade CTA */}
      {showUpgrade && (
        <Link
          href="/client/upgrade"
          className="flex items-center justify-between w-full px-2.5 py-1.5 rounded-lg bg-[#17171c] text-white text-[11px] font-semibold hover:opacity-85 transition-opacity"
        >
          <span>Planı Yükselt</span>
          <ArrowUpRight size={12} />
        </Link>
      )}
    </div>
  );
}

// ── Layout ───────────────────────────────────────────────────────────────────

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [currentUsername, setCurrentUsername] = useState<string | null>(null);

  useEffect(() => {
    const username = localStorage.getItem("appq_username");
    const timer = setTimeout(() => {
      if (!username) {
        setShowModal(true);
      } else {
        setCurrentUsername(username);
      }
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  function handleLogout() {
    localStorage.removeItem("appq_username");
    window.location.href = "/";
  }

  return (
    <div className="h-screen bg-background text-foreground flex flex-col md:flex-row overflow-hidden">

      {showModal && (
        <Suspense>
          <UsernameModal onComplete={(username) => {
            setCurrentUsername(username);
            setShowModal(false);
          }} />
        </Suspense>
      )}

      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between p-4 border-b border-border bg-sidebar">
        <Link href="/" className="flex items-center gap-2">
          <Logo size={32} strokeColor="#17171c" />
          <span className="font-semibold tracking-tight text-lg">Clarere</span>
        </Link>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 border border-border rounded-md hover:bg-sidebar-accent transition-colors"
          aria-label="Toggle menu"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 border-r border-border bg-sidebar flex flex-col transition-transform duration-300 md:translate-x-0 md:static md:z-auto
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        {/* Logo */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-border">
          <Link href="/" className="flex items-center gap-2">
            <Logo size={32} strokeColor="#17171c" />
            <span className="font-semibold tracking-tight text-lg">Clarere</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1 border border-border rounded-md hover:bg-sidebar-accent transition-colors"
            aria-label="Close menu"
          >
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 flex-1 px-3 py-4">
          <Link
            href="/client"
            onClick={() => setSidebarOpen(false)}
            className="px-3 py-2 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground text-sm font-medium transition-colors"
          >
            Dashboard
          </Link>
          <Link
            href="/client/new"
            onClick={() => setSidebarOpen(false)}
            className="px-3 py-2 rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground text-sm font-medium transition-colors"
          >
            Yeni Araştırma
          </Link>
          
          <SidebarStudiesWidget />
        </nav>

        {/* Bottom: Plan widget + user */}
        <div className="px-3 pb-5 space-y-3 border-t border-border pt-4">
          {/* Plan widget */}
          <SidebarPlanWidget />

          {/* User row */}
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <User size={13} className="text-muted-foreground shrink-0" />
              <span className="text-xs font-medium text-foreground truncate">
                {currentUsername ?? "Misafir"}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors shrink-0"
              title="Çıkış Yap"
            >
              <LogOut size={12} />
              Çıkış
            </button>
          </div>
        </div>
      </aside>

      {/* Backdrop */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 md:hidden animate-in fade-in"
        />
      )}

      <main className="flex-1 overflow-auto flex flex-col relative">
        {children}
      </main>
      <Toaster />
    </div>
  );
}
