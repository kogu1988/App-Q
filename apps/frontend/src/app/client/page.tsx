"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { FileText, Plus, Zap } from "lucide-react";
import { useClientPlan } from "@/hooks/use-client-plan";

interface Study {
  id: string;
  title?: string;
  category?: string;
  updated_at: string;
  has_report: boolean;
}

// ── Kullanım Sayacı Widget ─────────────────────────────────────────────────────

function UsageWidget() {
  const { plan, loading } = useClientPlan();
  if (loading) return null;

  // Bu dönemde kullanılan hak (toplam değil)
  const used = plan.period_simulations;
  const max = plan.limits.max_simulations;
  const isUnlimited = max >= 9999;
  const pct = isUnlimited ? 100 : Math.min(Math.round((used / max) * 100), 100);
  const isNearLimit = !isUnlimited && pct >= 80;

  // Dönem bitiş tarihi
  const periodEnd = (() => {
    if (!plan.period_start) return null;
    const start = new Date(plan.period_start);
    const days = plan.billing_cycle === "annual" ? 365 : 30;
    start.setDate(start.getDate() + days);
    return start.toLocaleDateString("tr-TR", { day: "numeric", month: "long" });
  })();

  const planColors: Record<string, string> = {
    Free:       "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    Starter:    "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
    Pro:        "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
    Enterprise: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  };

  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border transition-colors ${
      isNearLimit
        ? "border-amber-300 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-700"
        : "border-border bg-card"
    }`}>
      <Zap size={14} className={isNearLimit ? "text-amber-500" : "text-muted-foreground"} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <span className="text-xs font-medium text-muted-foreground">
            {isUnlimited
              ? `${used} araştırma kullanıldı`
              : `${used} / ${max} araştırma (bu dönem)`}
          </span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${planColors[plan.plan_type] ?? planColors.Free}`}>
            {plan.plan_type}
          </span>
        </div>
        {!isUnlimited && (
          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isNearLimit ? "bg-amber-500" : "bg-indigo-500"
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
        )}
        {periodEnd && (
          <p className="text-[10px] text-muted-foreground/60 mt-1">
            Dönem yenileme: {periodEnd}
          </p>
        )}
      </div>
      {(plan.plan_type === "Free" || plan.plan_type === "Starter") && (
        <Link
          href="/#pricing"
          className="text-[10px] font-semibold text-accent hover:underline whitespace-nowrap"
        >
          Yükselt →
        </Link>
      )}
    </div>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export default function ClientDashboard() {
  const [studies, setStudies] = useState<Study[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const username = localStorage.getItem("appq_username") || "";
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const headers: Record<string, string> = username ? { "X-Username": username } : {};
    fetch(`${apiBase}/api/client/studies`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => { setStudies(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 sm:p-8 space-y-6 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground text-sm sm:text-base">Geçmiş araştırma projeleriniz ve sonuçları.</p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <UsageWidget />
          <Link href="/client/new" className="w-full sm:w-auto">
            <Button className="w-full sm:w-auto gap-2">
              <Plus size={16} />
              Yeni Araştırma
            </Button>
          </Link>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Araştırma Geçmişi</CardTitle>
          <CardDescription>Son gerçekleştirdiğiniz sentetik simülasyonların raporları.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground text-sm">Yükleniyor...</div>
          ) : studies.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
              Henüz bir araştırma bulunmuyor. Yeni bir araştırma başlatın.
            </div>
          ) : (
            <div className="overflow-x-auto w-full">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Proje Adı</TableHead>
                    <TableHead>Kategori</TableHead>
                    <TableHead>Tarih</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {studies.map((study) => (
                    <TableRow key={study.id}>
                      <TableCell className="font-medium">{study.title || "İsimsiz Proje"}</TableCell>
                      <TableCell>{study.category || "-"}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(study.updated_at).toLocaleDateString("tr-TR")}
                      </TableCell>
                      <TableCell>
                        {study.has_report ? (
                          <Badge variant="default" className="bg-green-600 hover:bg-green-700">Tamamlandı</Badge>
                        ) : (
                          <Badge variant="secondary">Taslak</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {study.has_report && (
                          <Link href={`/client/studies/${study.id}`}>
                            <Button variant="ghost" size="sm" className="gap-2">
                              <FileText size={16} />
                              Raporu Gör
                            </Button>
                          </Link>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
