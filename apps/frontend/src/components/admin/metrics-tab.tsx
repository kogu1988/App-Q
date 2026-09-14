"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
} from "@/components/ui/dialog";
import {
  Users,
  Loader2,
  BarChart3,
  Cpu,
  Zap,
  Database,
} from "lucide-react";
import type {
  MetricsData,
} from "@/features/admin/types";

interface MetricsTabProps {
  metrics: MetricsData | null;
  metricsLoading: boolean;
}

/** Metrikler sekmesi (refactor R3). */
export function MetricsTab({ metrics, metricsLoading }: MetricsTabProps) {
  return (
    <>
  <div className="mb-6 flex items-center justify-between">
    <div>
      <p className="text-sm text-[#616161] dark:text-[#93939f]">
        Sistem metrikleri, aktif projeler ve kullanıcı istatistikleri.
      </p>
    </div>
  </div>

  {metricsLoading && (
    <div className="flex items-center gap-3 py-16 justify-center text-muted-foreground">
      <Loader2 size={22} className="animate-spin text-[#ff7759]" />
      Metrikler yükleniyor...
    </div>
  )}

  {metrics && (
    <>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: "Toplam Danışan",
            value: metrics.totals.clients,
            icon: <Users size={18} className="text-[#003c33]" />,
            bg: "bg-[#edfce9]/60",
            border: "border-[#003c33]/20",
          },
          {
            label: "Toplam Simülasyon",
            value: metrics.totals.simulations,
            icon: <Zap size={18} className="text-amber-600" />,
            bg: "bg-amber-50/60",
            border: "border-amber-200",
          },
          {
            label: "Toplam Araştırma",
            value: metrics.study_stats.total,
            icon: <Database size={18} className="text-[#1863dc]" />,
            bg: "bg-[#f1f5ff]/60",
            border: "border-[#1863dc]/20",
          },
          {
            label: "Ort. Kalite Skoru",
            value: metrics.study_stats.avg_quality > 0 ? `${metrics.study_stats.avg_quality}/100` : "—",
            icon: <BarChart3 size={18} className="text-[#ff7759]" />,
            bg: "bg-orange-50/60",
            border: "border-[#ff7759]/20",
          },
        ].map(kpi => (
          <Card key={kpi.label} className={`${kpi.bg} border ${kpi.border}`}>
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-[#93939f] uppercase tracking-wider">
                  {kpi.label}
                </span>
                {kpi.icon}
              </div>
              <div className="text-3xl font-bold text-[#17171c]">{kpi.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-[#d9d9dd]">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <Cpu size={16} className="text-[#ff7759]" />
            Aktif LLM Modelleri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid sm:grid-cols-3 gap-3">
            {[
              {
                label: "Flash (DeepSeek V4)",
                value: metrics.models.orchestrator,
                color: "text-[#ff7759]",
                bg: "bg-orange-50",
              },
              { label: "Flash (B2C)", value: metrics.models.b2c, color: "text-[#003c33]", bg: "bg-[#edfce9]" },
              { label: "Pro (B2B)", value: metrics.models.b2b, color: "text-[#1863dc]", bg: "bg-[#f1f5ff]" },
            ].map(m => (
              <div key={m.label} className={`rounded-lg px-4 py-3 ${m.bg}`}>
                <div className="text-[10px] font-mono uppercase tracking-wider text-[#93939f] mb-0.5">
                  {m.label}
                </div>
                <div className={`font-mono text-sm font-semibold ${m.color}`}>{m.value}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-bold">Danışan Token Kullanımı</CardTitle>
          <CardDescription>Her danışanın plan limitine göre token doluluk oranı.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {metrics.clients.map(cli => {
            const pct = cli.max_tokens > 0 ? Math.min(100, (cli.tokens_used / cli.max_tokens) * 100) : 0;
            const isWarning = pct >= 70 && pct < 90;
            const isDanger = pct >= 90;
            const barColor = isDanger ? "bg-red-500" : isWarning ? "bg-amber-400" : "bg-[#003c33]";
            const fmtToken = (n: number) =>
              n >= 1_000_000
                ? `${(n / 1_000_000).toFixed(1)}M`
                : n >= 1_000
                ? `${(n / 1_000).toFixed(0)}K`
                : String(n);

            return (
              <div key={cli.username} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-[#17171c]">{cli.username}</span>
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                      {cli.plan_type}
                    </Badge>
                    {isDanger && (
                      <Badge className="text-[10px] px-1.5 py-0 bg-red-100 text-red-700 border border-red-200">
                        Limit Dolmak Üzere
                      </Badge>
                    )}
                    {isWarning && (
                      <Badge className="text-[10px] px-1.5 py-0 bg-amber-50 text-amber-700 border border-amber-200">
                        Uyarı
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {fmtToken(cli.tokens_used)} / {fmtToken(cli.max_tokens)} ({pct.toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2 rounded-full bg-[#eeece7] overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
          {metrics.clients.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">Henüz danışan yok.</p>
          )}
        </CardContent>
      </Card>

      {/* ── Plan Dağılımı + Study Stats ── */}
      <div className="grid sm:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold">Plan Dağılımı</CardTitle>
          </CardHeader>
          <CardContent className="p-0 overflow-x-auto">
            <table className="w-full text-sm min-w-[440px]">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  {["Plan", "Danışan", "Token (toplam)", "Simülasyon"].map(h => (
                    <th
                      key={h}
                      className="text-left py-2 px-4 text-[10px] font-mono uppercase tracking-wider text-[#93939f]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.plan_distribution.map(row => (
                  <tr
                    key={row.plan_type}
                    className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                  >
                    <td className="py-2 px-4 font-semibold text-[#17171c]">{row.plan_type}</td>
                    <td className="py-2 px-4 text-muted-foreground">{row.count}</td>
                    <td className="py-2 px-4 text-muted-foreground tabular-nums">
                      {row.total_tokens >= 1_000_000
                        ? `${(row.total_tokens / 1_000_000).toFixed(1)}M`
                        : row.total_tokens >= 1_000
                        ? `${(row.total_tokens / 1_000).toFixed(0)}K`
                        : row.total_tokens ?? 0}
                    </td>
                    <td className="py-2 px-4 text-muted-foreground">{row.total_sims ?? 0}</td>
                  </tr>
                ))}
                {metrics.plan_distribution.length === 0 && (
                  <tr>
                    <td colSpan={4} className="text-center py-6 text-muted-foreground text-sm">
                      Veri yok.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold">Araştırma Özeti</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {[
              { label: "Toplam Araştırma", value: metrics.study_stats.total },
              { label: "Raporu Olan", value: metrics.study_stats.with_report },
              { label: "Arşivlenen", value: metrics.study_stats.archived },
              {
                label: "Ort. Kalite Skoru",
                value: metrics.study_stats.avg_quality > 0 ? `${metrics.study_stats.avg_quality}/100` : "—",
              },
              { label: "Denetim Hataları", value: metrics.study_stats.error_count },
            ].map(item => (
              <div
                key={item.label}
                className="flex items-center justify-between py-1 border-b border-border/40 last:border-0"
              >
                <span className="text-sm text-muted-foreground">{item.label}</span>
                <span
                  className={`font-semibold text-sm ${
                    item.label === "Denetim Hataları" && Number(item.value) > 0 ? "text-red-600" : "text-[#17171c]"
                  }`}
                >
                  {item.value}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ── Kategori Dağılımı ── */}
      {metrics.categories.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold">Araştırma Kategorileri</CardTitle>
            <CardDescription>En çok araştırılan ürün/hizmet kategorileri.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(() => {
                const maxCount = Math.max(...metrics.categories.map(c => c.count));
                return metrics.categories.map(cat => (
                  <div key={cat.category} className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground w-40 shrink-0 truncate">
                      {cat.category}
                    </span>
                    <div className="flex-1 h-2 rounded-full bg-[#eeece7] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#1863dc]/70 transition-all duration-500"
                        style={{ width: `${(cat.count / maxCount) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-muted-foreground w-6 text-right">
                      {cat.count}
                    </span>
                  </div>
                ));
              })()}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Persona Havuzu ── */}
      {metrics.persona_pool && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-bold">Persona Havuzu ({metrics.persona_pool.total || 0} persona)</CardTitle>
            <CardDescription>En çok kullanılan personalar ve stance dağılımı.</CardDescription>
          </CardHeader>
          <CardContent>
            {metrics.persona_pool.total > 0 ? (
              <>
                <div className="space-y-2">
                  {metrics.persona_pool.top_used.filter((p: { usage_count: number }) => p.usage_count > 0).slice(0, 5).map((p: { name: string; stance: string; ses_group: string; usage_count: number }) => (
                    <div key={p.name} className="flex items-center justify-between text-sm">
                      <span className="font-medium">{p.name} <span className="text-xs text-muted-foreground">({p.stance}, {p.ses_group})</span></span>
                      <Badge variant="secondary" className="text-xs">{p.usage_count} kullanım</Badge>
                    </div>
                  ))}
                </div>
                {metrics.persona_pool.stances.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {metrics.persona_pool.stances.map((s: { stance: string; count: number }) => (
                      <Badge key={s.stance} variant="outline" className="text-[10px]">{s.stance}: {s.count}</Badge>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">Henüz persona bulunmuyor. İlk araştırma sonrası otomatik eklenecek.</p>
            )}
          </CardContent>
        </Card>
      )}
    </>
  )}
    </>
  );
}
