"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { FileText } from "lucide-react";

interface Study {
  id: string;
  title?: string;
  category?: string;
  updated_at: string;
  has_report: boolean;
}


// ── Dashboard ─────────────────────────────────────────────────────────────────


export default function ClientDashboard() {
  const [studies, setStudies] = useState<Study[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const username = localStorage.getItem("appq_username") || "";
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000";
    const headers: Record<string, string> = username ? { "X-Username": username } : {};
    fetch(`${apiBase}/api/client/studies`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => { setStudies(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 sm:p-8 space-y-6 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4">
      {/* ── PRESET SHARP CARBON GLOW CARD ────────────────────────────────────── */}
      <div className="bg-[#17171c] text-white p-6 sm:p-8 rounded-[2px] border border-white/10 relative overflow-hidden shadow-lg">
        {/* Decorative subtle ambient orange glow */}
        <div className="absolute right-0 top-0 w-64 h-64 bg-[#ff7759]/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight" style={{ fontFamily: "var(--font-heading, 'Space Grotesk', sans-serif)" }}>
              Karanlıkta kalmış her fikir, sorulmamış bir soruyla başlar.
            </h2>
            <p className="text-white/60 text-sm sm:text-base max-w-2xl leading-relaxed">
              Bugün o soruları sormaya başlayın. Karşınızdaki kişi sentetik olabilir. Ama cevapları fazlasıyla gerçek.
            </p>
          </div>
          <Link href="/client/new" className="shrink-0">
            <Button className="bg-[#ff7759] hover:bg-[#ff7759]/90 text-[#17171c] font-semibold rounded-[2px] px-6 py-5 text-sm transition-all duration-300 transform hover:scale-[1.02]">
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
