"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { FileText, CreditCard, ExternalLink, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { useClientPlan } from "@/hooks/use-client-plan";
import { getAuthHeaders } from "@/lib/auth";

interface Study {
  id: string;
  title?: string;
  category?: string;
  updated_at: string;
  has_report: boolean;
}

interface SubscriptionInfo {
  plan: string;
  status: string;
  current_period_end: string | null;
  paddle_customer_id: string;
}

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  active: { label: "Aktif", className: "bg-deep-green text-white" },
  trialing: { label: "Deneme", className: "bg-info-blue text-white" },
  past_due: { label: "Ödeme Gecikti", className: "bg-amber-500 text-white" },
  paused: { label: "Duraklatıldı", className: "bg-body-muted text-white" },
  canceled: { label: "İptal Edildi", className: "bg-error-dark text-white" },
  none: { label: "Abonelik Yok", className: "bg-muted text-muted-foreground" },
};

// ── Abonelik Durumu ──────────────────────────────────────────────────────────

function SubscriptionCard() {
  const [sub, setSub] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    fetch(`/api/billing/subscription`, { headers: getAuthHeaders() })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { setSub(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  async function openPortal() {
    setPortalLoading(true);
    try {
      const res = await fetch(`/api/billing/portal`, { headers: getAuthHeaders() });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || "Abonelik portalı açılamadı.");
      }
      const data = await res.json();
      if (!data?.url) throw new Error("Portal bağlantısı alınamadı.");
      window.open(data.url, "_blank", "noopener,noreferrer");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bir hata oluştu.");
    } finally {
      setPortalLoading(false);
    }
  }

  if (loading) return null;

  const status = sub?.status ?? "none";
  const statusMeta = STATUS_LABELS[status] ?? STATUS_LABELS.none;
  const periodEnd = sub?.current_period_end
    ? new Date(sub.current_period_end).toLocaleDateString("tr-TR")
    : null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CreditCard size={18} /> Abonelik
            </CardTitle>
            <CardDescription>
              {sub?.plan ? `${sub.plan} planı` : "Henüz bir aboneliğiniz yok."}
              {periodEnd ? ` · Dönem sonu: ${periodEnd}` : ""}
            </CardDescription>
          </div>
          <Badge className={statusMeta.className}>{statusMeta.label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {status === "past_due" && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 border border-amber-300">
            <AlertTriangle size={16} className="text-amber-700 mt-0.5 shrink-0" />
            <p className="text-xs text-amber-900 leading-relaxed">
              Ödemeniz alınamadı. Erişiminiz devam ediyor — kesinti yaşamamak için ödeme
              yönteminizi güncelleyin.
            </p>
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {sub?.paddle_customer_id ? (
            <Button
              size="sm"
              variant="outline"
              className="gap-2 rounded-xl"
              onClick={openPortal}
              disabled={portalLoading}
            >
              <ExternalLink size={14} />
              {portalLoading ? "Açılıyor…" : "Aboneliği Yönet"}
            </Button>
          ) : null}
          <Link href="/client/upgrade">
            <Button size="sm" className="bg-primary hover:opacity-85 text-white font-semibold rounded-xl gap-2">
              {sub?.plan && sub.plan !== "Free" ? "Planı Değiştir" : "Plan Seç"}
            </Button>
          </Link>
        </div>

        <p className="text-[11px] text-muted-foreground leading-relaxed">
          Ödemeler Paddle üzerinden alınır. Fatura ve kart bilgilerinizi Paddle müşteri
          portalından yönetebilirsiniz.
        </p>
      </CardContent>
    </Card>
  );
}


// ── Dashboard ─────────────────────────────────────────────────────────────────


export default function ClientDashboard() {
  const [studies, setStudies] = useState<Study[]>([]);
  const [loading, setLoading] = useState(true);
  const { plan: clientPlan } = useClientPlan();

  useEffect(() => {
    const headers = getAuthHeaders();
    fetch(`/api/client/studies`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => { setStudies(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 sm:p-8 space-y-6 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4">
      {clientPlan.trial_expired && (
        <div className="p-5 bg-amber-50 border-2 border-amber-300 rounded-2xl space-y-3 shadow-sm animate-in slide-in-from-top-4 duration-300">
          <div className="flex items-center gap-2">
            <span className="text-base">⚠️</span>
            <p className="text-sm font-black text-amber-900">Deneme Süreniz Doldu</p>
          </div>
          <p className="text-xs text-amber-800 leading-relaxed max-w-3xl">
            Her plan 1 aylık ücretsiz deneme ve 2 ücretsiz araştırma içerir — kredi kartı gerekmez. Karar vermeden önce platformu deneyimler, gerçek bir araştırma yürütür ve çıktıyı görürsünüz.
          </p>
          <p className="text-xs text-amber-800 leading-relaxed max-w-3xl">
            1 ay veya 2 araştırma (hangisi önce gelirse) sonunda bir plan seçmeniz istenir. Raporlarınız ve verileriniz 30 gün boyunca erişilebilir kalır; sonrasında erişim kısıtlanır. Her şeyi açık tutmak için bir plan seçin.
          </p>
          <div className="pt-1">
            <Link href="/client/upgrade">
              <Button size="sm" className="bg-primary hover:opacity-85 text-white font-semibold rounded-xl text-xs px-4">
                Plan Seç →
              </Button>
            </Link>
          </div>
        </div>
      )}

      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-primary dark:text-white">Kontrol Paneli</h1>
        <p className="text-body-muted dark:text-muted-text text-sm sm:text-base">Geçmiş araştırma projeleriniz ve sonuçları.</p>
      </div>

      <SubscriptionCard />

      {/* ── PRESET SHARP CARBON GLOW CARD ────────────────────────────────────── */}
      <div className="bg-primary text-white p-6 sm:p-8 rounded-[2px] border border-white/10 relative overflow-hidden shadow-lg">
        {/* Decorative subtle ambient orange glow */}
        <div className="absolute right-0 top-0 w-64 h-64 bg-coral/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight font-heading">
              Karanlıkta kalmış her fikir, sorulmamış bir soruyla başlar.
            </h2>
            <p className="text-white/60 text-sm sm:text-base max-w-2xl leading-relaxed">
              Bugün o soruları sormaya başlayın. Karşınızdaki kişi sentetik olabilir. Ama cevapları fazlasıyla gerçek.
            </p>
          </div>
          <Link href="/client/new" className="shrink-0">
            <Button className="bg-coral hover:bg-coral/90 text-primary font-semibold rounded-[2px] px-6 py-5 text-sm transition-all duration-300 transform hover:scale-[1.02]">
              Yeni Araştırma Başlat
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
            <div className="text-center py-8 text-body-muted dark:text-muted-text text-sm">Yükleniyor...</div>
          ) : studies.length === 0 ? (
            <div className="text-center py-12 text-body-muted dark:text-muted-text border border-dashed border-border rounded-lg">
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
                      <TableCell className="text-body-muted dark:text-muted-text">
                        {new Date(study.updated_at).toLocaleDateString("tr-TR")}
                      </TableCell>
                      <TableCell>
                        {study.has_report ? (
                          <Badge variant="default" className="bg-deep-green text-white dark:bg-pale-green dark:text-deep-green">Tamamlandı</Badge>
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
