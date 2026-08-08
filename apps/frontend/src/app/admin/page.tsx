"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Settings,
  Users,
  Activity,
  ListOrdered,
  MessageSquare,
  Heart,
  HeartOff,
  Trash2,
  Plus,
  Save,
  Loader2,
  Pencil,
  Check,
  X,
  Code,
  ChevronDown,
  ChevronRight,
  BarChart3,
  Cpu,
  Zap,
  Database,
  ThumbsUp,
  ThumbsDown,
  Eye,
  Info,
} from "lucide-react";
import Logo from "@/components/logo";

// Import modular components
import { FeedbackTable } from "@/components/admin/feedback-table";
import { ClientsTab } from "@/components/admin/clients-tab";
import { ConfigTab } from "@/components/admin/config-tab";
import { PersonasTab } from "@/components/admin/personas-tab";

function InfoTooltip({ text }: { text: string }) {
  return (
    <div className="relative group inline-flex items-center ml-1.5 align-middle">
      <div className="flex items-center justify-center w-4 h-4 rounded-full bg-[#eeece7] text-[#616161] text-[12px] cursor-help font-medium hover:bg-[#d9d9dd] transition-colors">
        ?
      </div>
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 px-3 py-2 bg-[#17171c] border border-[#212121] text-white text-[12px] rounded-[8px] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-[9999] pointer-events-none font-normal normal-case leading-relaxed text-center">
        {text}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-[#17171c]" />
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-[#212121] -z-10 mt-[1px]" />
      </div>
    </div>
  );
}

// ─── Type Definitions ────────────────────────────────────────────────────────

interface AdminConfig {
  b2c_model?: string;
  b2b_model?: string;
  pii_active?: string;
  pii_terms?: string;
  wizard_prompt?: string;
  persona_interview_prompt?: string;
  synthesis_prompt?: string;
  [key: string]: string | undefined;
}

interface ClientInfo {
  username: string;
  email: string;
  plan_type: string;
  total_simulations: number;
  tokens_used: number;
  max_simulations: number;
  max_tokens: number;
  status: string;
  plan_start?: string;
  plan_end?: string;
  created_at?: string;
}

interface PersonaInfo {
  id: string;
  name: string;
  age: number;
  city: string;
  segment: string;
  role_title?: string;
  is_global: boolean;
  ses_group?: string;
  respondent_type?: string;
  settlement_type?: string;
  stance?: string;
  bio?: string;
  traits?: string;
  attributes?: string;
  goals?: string;
  objections?: string;
  price_sensitivity?: number;
  digital_confidence?: number;
  is_locked?: boolean;
}

interface AuditLog {
  id: string;
  created_at: string;
  study_id?: string;
  persona_name: string;
  error_reason: string;
  action_taken: string;
}

interface CuratedQuestion {
  id: number;
  question: string;
  research_title?: string;
  research_category?: string;
  purpose_context?: string;
  is_liked: boolean;
  created_at?: string;
}

interface FeedbackItem {
  id: number;
  username?: string;
  study_id?: string;
  item_type?: string;
  vote: number;
  comment?: string;
  created_at?: string;
}

interface MetricsData {
  totals: { clients: number; tokens_used: number; tokens_capacity: number; simulations: number };
  plan_distribution: { plan_type: string; count: number; total_tokens: number; total_sims: number }[];
  clients: {
    username: string;
    plan_type: string;
    tokens_used: number;
    max_tokens: number;
    total_simulations: number;
    max_simulations: number;
    period_simulations: number;
  }[];
  study_stats: { total: number; avg_quality: number; with_report: number; archived: number; error_count: number };
  categories: { category: string; count: number }[];
  models: { b2c: string; b2b: string; orchestrator: string };
}

interface SchemaField {
  key: string;
  type: string;
  required?: boolean;
  desc: string;
}

interface AgentSchemas {
  brief_schema: {
    description: string;
    fields: SchemaField[];
    defaults: Record<string, string>;
  };
  persona_schema: { description: string; fields: SchemaField[] };
  interview_schema: { description: string; prompt_variables: string[]; output: Record<string, string> };
  synthesis_schema: { description: string; inputs: string[]; output_fields: string[] };
  default_interview_questions: string[];
  concept_pools: Record<string, { persona_name: string; focus_areas: string; questions: string[] }>;
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function AdminPage() {
  const [config, setConfig] = useState<AdminConfig>({});
  const [clients, setClients] = useState<ClientInfo[]>([]);
  const [personas, setPersonas] = useState<PersonaInfo[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [questions, setQuestions] = useState<CuratedQuestion[]>([]);
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [schemas, setSchemas] = useState<AgentSchemas | null>(null);
  const [schemasLoading, setSchemasLoading] = useState(false);
  const [expandedPool, setExpandedPool] = useState<string | null>(null);
  const [editingDefaultQ, setEditingDefaultQ] = useState(false);
  const [draftQuestions, setDraftQuestions] = useState<string[]>([]);
  const [savingDefaults, setSavingDefaults] = useState(false);
  const [briefDefaults, setBriefDefaults] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [savingConfig, setSavingConfig] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  // Edit question purpose states
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null);
  const [editPurpose, setEditPurpose] = useState("");
  const [deleteQuestionTarget, setDeleteQuestionTarget] = useState<number | null>(null);
  const [deletingQuestion, setDeletingQuestion] = useState(false);

  const fetchAll = useCallback(() => {
    Promise.all([
      fetch("/api/admin/config").then(r => r.json()),
      fetch("/api/admin/clients").then(r => r.json()),
      fetch("/api/admin/personas").then(r => r.json()),
      fetch("/api/admin/audit_logs").then(r => r.json()),
      fetch("/api/admin/questions").then(r => r.json()),
      fetch("/api/admin/feedbacks").then(r => r.json()),
    ])
      .then(([conf, cli, pers, lg, qs, fbs]) => {
        setConfig(conf);
        setClients(Array.isArray(cli) ? cli : []);
        setPersonas(Array.isArray(pers) ? pers : []);
        setLogs(Array.isArray(lg) ? lg : []);
        setQuestions(Array.isArray(qs) ? qs : []);
        setFeedbacks(Array.isArray(fbs) ? fbs : []);
        setLoading(false);
      })
      .catch(err => {
        console.error("FetchAll Error:", err);
        toast.error(`Veriler yüklenirken hata oluştu: ${err.message || err}`);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ── Config Saving ──────────────────────────────────────────────────────────
  const saveConfig = async (key: string, value: string) => {
    setSavingConfig(key);
    try {
      const res = await fetch("/api/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
      });
      if (!res.ok) throw new Error();
      toast.success("Ayar kaydedildi.");
      fetchAll();
    } catch {
      toast.error("Ayar kaydedilemedi.");
    } finally {
      setSavingConfig(null);
    }
  };

  // ── Question Management ─────────────────────────────────────────────────────
  const toggleLike = async (id: number, current: boolean) => {
    try {
      await fetch(`/api/admin/questions/${id}/like?is_liked=${!current}`, { method: "PUT" });
      setQuestions(prev => prev.map(q => (q.id === id ? { ...q, is_liked: !current } : q)));
      toast.success("Beğeni güncellendi.");
    } catch {
      toast.error("İşlem başarısız.");
    }
  };

  const savePurpose = async (id: number) => {
    try {
      await fetch(`/api/admin/questions/${id}/purpose?purpose=${encodeURIComponent(editPurpose)}`, { method: "PUT" });
      setQuestions(prev => prev.map(q => (q.id === id ? { ...q, purpose_context: editPurpose } : q)));
      setEditingQuestion(null);
      toast.success("Amaç güncellendi.");
    } catch {
      toast.error("Güncelleme başarısız.");
    }
  };

  const deleteQuestion = async (id: number) => {
    setDeletingQuestion(true);
    try {
      await fetch(`/api/admin/questions/${id}`, { method: "DELETE" });
      setQuestions(prev => prev.filter(q => q.id !== id));
      toast.success("Soru silindi.");
      setDeleteQuestionTarget(null);
    } catch {
      toast.error("Silme başarısız.");
    } finally {
      setDeletingQuestion(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="h-10 w-10 animate-spin text-[#ff7759] mx-auto" />
          <p className="text-muted-foreground text-sm font-medium animate-pulse">Yönetici paneli yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-4 sm:p-8">
      <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4">
        <header className="flex items-center justify-between border-b border-border pb-6">
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
        </header>

        <Tabs defaultValue="clients" orientation="vertical" className="flex flex-col md:flex-row gap-6 w-full">
          <TabsList className="flex flex-col h-auto w-full md:w-64 bg-muted p-2 rounded-lg gap-2 justify-start items-stretch">
            <TabsTrigger value="clients" className="justify-start px-4 py-2.5 w-full">
              <Users size={16} className="mr-3" />
              <span>Danışanlar</span>
            </TabsTrigger>
            <TabsTrigger value="config" className="justify-start px-4 py-2.5 w-full">
              <Settings size={16} className="mr-3" />
              <span>Yapılandırma</span>
            </TabsTrigger>
            <TabsTrigger value="personas" className="justify-start px-4 py-2.5 w-full">
              <ListOrdered size={16} className="mr-3" />
              <span>Personalar</span>
            </TabsTrigger>
            <TabsTrigger value="questions" className="justify-start px-4 py-2.5 w-full">
              <MessageSquare size={16} className="mr-3" />
              <span>Soru Koleksiyonu</span>
            </TabsTrigger>
            <TabsTrigger value="feedbacks" className="justify-start px-4 py-2.5 w-full">
              <Heart size={16} className="mr-3" />
              <span>Geri Bildirimler</span>
            </TabsTrigger>
            <TabsTrigger value="logs" className="justify-start px-4 py-2.5 w-full">
              <Activity size={16} className="mr-3" />
              <span>Denetim Kayıtları</span>
            </TabsTrigger>
            <TabsTrigger
              value="schemas"
              className="justify-start px-4 py-2.5 w-full"
              onClick={() => {
                if (!schemas) {
                  setSchemasLoading(true);
                  fetch("/api/admin/schemas")
                    .then(r => r.json())
                    .then(d => {
                      setSchemas(d);
                      setBriefDefaults(d.brief_schema.defaults);
                      setDraftQuestions(d.default_interview_questions);
                    })
                    .catch(() => toast.error("Şemalar yüklenemedi."))
                    .finally(() => setSchemasLoading(false));
                }
              }}
            >
              <Code size={16} className="mr-3" />
              <span>Ajan Şablonları</span>
            </TabsTrigger>
            <TabsTrigger
              value="metrics"
              className="justify-start px-4 py-2.5 w-full"
              onClick={() => {
                if (!metrics && !metricsLoading) {
                  setMetricsLoading(true);
                  fetch("/api/admin/metrics")
                    .then(r => r.json())
                    .then(d => setMetrics(d))
                    .catch(() => toast.error("Metrikler yüklenemedi."))
                    .finally(() => setMetricsLoading(false));
                }
              }}
            >
              <BarChart3 size={16} className="mr-3" />
              <span>Metrikler</span>
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 w-full min-w-0">
            <TabsContent value="clients" className="mt-0 outline-none">
              <ClientsTab clients={clients} onRefresh={fetchAll} />
            </TabsContent>

            <TabsContent value="config" className="mt-0 outline-none">
              <ConfigTab config={config} savingConfig={savingConfig} saveConfig={saveConfig} />
            </TabsContent>

            <TabsContent value="personas" className="mt-0 outline-none">
              <PersonasTab personas={personas} onRefresh={fetchAll} />
            </TabsContent>

            <TabsContent value="questions" className="mt-6 flex-1 outline-none">
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
                                onClick={() => toggleLike(q.id, q.is_liked)}
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
                                  setEditingQuestion(q.id);
                                  setEditPurpose(q.purpose_context || "");
                                }}
                                className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                              >
                                <Pencil size={14} />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => setDeleteQuestionTarget(q.id)}
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
                                onChange={e => setEditPurpose(e.target.value)}
                                placeholder="Bu sorunun amacı / bağlamı..."
                                className="text-xs h-8 flex-1 bg-background text-foreground"
                              />
                              <Button
                                size="sm"
                                className="h-8 gap-1.5 text-xs bg-[#17171c] text-white hover:opacity-85"
                                onClick={() => savePurpose(q.id)}
                              >
                                <Check size={13} />
                                Kaydet
                              </Button>
                              <Button size="sm" variant="ghost" className="h-8" onClick={() => setEditingQuestion(null)}>
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
            </TabsContent>

            <TabsContent value="feedbacks" className="mt-6 flex-1 outline-none">
              <div className="mb-6">
                <p className="text-sm text-muted-foreground">
                  Kullanıcılardan gelen simülasyon ve sistem geri bildirimleri ile genel değerlendirme skorları.
                </p>
              </div>

              {(() => {
                const total = feedbacks.length;
                const likes = feedbacks.filter(f => f.vote === 1).length;
                const dislikes = feedbacks.filter(f => f.vote === -1).length;
                const withComment = feedbacks.filter(f => f.comment && f.comment.trim().length > 0).length;
                const likeRate = total > 0 ? Math.round((likes / total) * 100) : 0;
                const commentRate = total > 0 ? Math.round((withComment / total) * 100) : 0;

                const typeCounts: Record<string, number> = {};
                feedbacks.forEach(f => {
                  const t = f.item_type || "genel";
                  typeCounts[t] = (typeCounts[t] || 0) + 1;
                });
                const topType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";

                return (
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <Card className="border-l-4 border-l-slate-400 shadow-sm">
                      <CardContent className="pt-5 pb-4">
                        <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">Toplam Kayıt</p>
                        <p className="text-4xl font-black text-slate-900 dark:text-white mt-1">{total}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          <span className="text-emerald-600 font-semibold">{likes} beğeni</span>
                          {" · "}
                          <span className="text-red-500 font-semibold">{dislikes} beğenmedi</span>
                        </p>
                      </CardContent>
                    </Card>

                    <Card
                      className={`border-l-4 shadow-sm ${
                        likeRate >= 70
                          ? "border-l-emerald-500"
                          : likeRate >= 40
                          ? "border-l-amber-500"
                          : "border-l-red-500"
                      }`}
                    >
                      <CardContent className="pt-5 pb-4">
                        <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">Beğeni Oranı</p>
                        <p
                          className={`text-4xl font-black mt-1 ${
                            likeRate >= 70
                              ? "text-emerald-600 dark:text-emerald-400"
                              : likeRate >= 40
                              ? "text-amber-600 dark:text-amber-400"
                              : "text-red-600 dark:text-red-400"
                          }`}
                        >
                          %{likeRate}
                        </p>
                        <div className="mt-2 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${
                              likeRate >= 70 ? "bg-emerald-500" : likeRate >= 40 ? "bg-amber-500" : "bg-red-500"
                            }`}
                            style={{ width: `${likeRate}%` }}
                          />
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-l-4 border-l-sky-400 shadow-sm">
                      <CardContent className="pt-5 pb-4">
                        <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">Yorum İçeren</p>
                        <p className="text-4xl font-black text-sky-600 dark:text-sky-400 mt-1">%{commentRate}</p>
                        <p className="text-xs text-muted-foreground mt-1">{withComment} kayıtta yorum var</p>
                      </CardContent>
                    </Card>

                    <Card className="border-l-4 border-l-indigo-400 shadow-sm">
                      <CardContent className="pt-5 pb-4">
                        <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">
                          En Çok Değerlendirilen
                        </p>
                        <p className="text-lg font-black text-[#1863dc] dark:text-[#4c6ee6] mt-1 truncate">{topType}</p>
                        <p className="text-xs text-muted-foreground mt-1">{typeCounts[topType] ?? 0} kayıt</p>
                      </CardContent>
                    </Card>
                  </div>
                );
              })()}

              <FeedbackTable feedbacks={feedbacks} />
            </TabsContent>

            <TabsContent value="logs" className="mt-6 flex-1 outline-none">
              <div className="mb-6">
                <p className="text-sm text-muted-foreground">
                  Simülasyon motorundaki kalite uyarıları, hallüsinasyon tespitleri ve aksiyon kayıtları.
                </p>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-muted-foreground">{logs.length} kayıt</span>
              </div>
              <Card>
                <CardContent className="pt-6">
                  <div className="overflow-x-auto w-full">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Tarih</TableHead>
                          <TableHead>Persona</TableHead>
                          <TableHead>Hata / Uyarı</TableHead>
                          <TableHead>Alınan Aksiyon</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {logs.length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={4} className="text-center py-10 text-muted-foreground">
                              Denetim kaydı bulunmuyor.
                            </TableCell>
                          </TableRow>
                        ) : (
                          logs.map(log => (
                            <TableRow key={log.id}>
                              <TableCell className="text-muted-foreground text-xs font-mono">
                                {new Date(log.created_at).toLocaleString("tr-TR")}
                              </TableCell>
                              <TableCell className="font-medium">{log.persona_name}</TableCell>
                              <TableCell>
                                <span className="text-red-600 dark:text-red-400 text-sm font-medium">
                                  {log.error_reason}
                                </span>
                              </TableCell>
                              <TableCell className="text-sm text-muted-foreground">{log.action_taken}</TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="schemas" className="mt-6 flex-1 outline-none space-y-6">
              <div className="mb-6">
                <p className="text-sm text-muted-foreground">
                  Ajanlara iletilen veri yapıları, varsayılan soru havuzları ve brief şablonları.
                </p>
              </div>

              {schemasLoading && (
                <div className="flex items-center gap-3 py-12 justify-center text-muted-foreground">
                  <Loader2 size={20} className="animate-spin" />
                  Şemalar yükleniyor...
                </div>
              )}

              {schemas && !schemas.brief_schema && (
                <div className="flex items-center gap-3 py-4 text-amber-600 dark:text-amber-400 text-sm">
                  ⚠️ Şema verisi beklenmeyen formatta geldi. Backend&apos;in çalıştığından emin olun.
                </div>
              )}

              {schemas?.brief_schema && (
                <>
                  <Card className="border-[#d9d9dd] bg-[#edfce9]/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-bold text-[#003c33]">Veri Akış Şeması</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap items-center gap-2 text-sm font-mono">
                        {[
                          { label: "Brief (Defne)", color: "bg-[#edfce9] text-[#003c33]" },
                          { label: "→", color: "text-muted-foreground" },
                          { label: "ResearchPlan", color: "bg-[#f1f5ff] text-[#1863dc]" },
                          { label: "→", color: "text-muted-foreground" },
                          { label: "Persona[]", color: "bg-[#edfce9] text-[#003c33]" },
                          { label: "→", color: "text-muted-foreground" },
                          { label: "Interview[]", color: "bg-amber-100 text-amber-800" },
                          { label: "→", color: "text-muted-foreground" },
                          { label: "ResearchReport", color: "bg-rose-100 text-rose-800" },
                        ].map((s, i) => (
                          <span key={i} className={`px-2.5 py-1 rounded-lg font-semibold text-xs ${s.color}`}>
                            {s.label}
                          </span>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {[
                      {
                        title: "Brief Şeması",
                        desc: schemas.brief_schema?.description ?? "",
                        badge: "Defne → intake.py",
                        badgeColor: "border-[#d9d9dd] text-[#003c33]",
                        rows: (schemas.brief_schema?.fields ?? []).map(f => [
                          f.key,
                          f.type,
                          f.required ? "Zorunlu" : "Opsiyonel",
                          f.desc,
                        ]),
                        headers: ["Alan", "Tip", "Durum", "Açıklama"],
                      },
                      {
                        title: "Persona Şeması",
                        desc: schemas.persona_schema?.description ?? "",
                        badge: "workflow.py → LLM",
                        badgeColor: "border-[#003c33]/30 text-[#003c33] dark:border-emerald-800",
                        rows: (schemas.persona_schema?.fields ?? []).map(f => [f.key, f.type, "", f.desc]),
                        headers: ["Alan", "Tip", "", "Açıklama"],
                      },
                      {
                        title: "Mülakat Turu Çıktısı",
                        desc: schemas.interview_schema?.description ?? "",
                        badge: "interview turn → LLM",
                        badgeColor: "border-amber-200 text-amber-700 dark:border-amber-800",
                        rows: Object.entries(schemas.interview_schema?.output ?? {}).map(([k, v]) => [k, "", "", v]),
                        headers: ["Alan", "", "", "Açıklama"],
                      },
                      {
                        title: "Sentez Raporu Çıktısı",
                        desc: schemas.synthesis_schema?.description ?? "",
                        badge: "analytics.py",
                        badgeColor: "border-rose-200 text-rose-700 dark:border-rose-800",
                        rows: (schemas.synthesis_schema?.output_fields ?? []).map(f => [f, "", "", ""]),
                        headers: ["Alan", "", "", ""],
                      },
                    ].map(card => (
                      <Card key={card.title} className="overflow-hidden">
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between gap-2">
                            <CardTitle className="text-sm font-bold">{card.title}</CardTitle>
                            <Badge variant="outline" className={`text-[10px] font-mono shrink-0 ${card.badgeColor}`}>
                              {card.badge}
                            </Badge>
                          </div>
                          <CardDescription className="text-xs">{card.desc}</CardDescription>
                        </CardHeader>
                        <CardContent className="p-0">
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="border-t border-b border-border bg-muted/40">
                                  {card.headers.filter(Boolean).map(h => (
                                    <th
                                      key={h}
                                      className="text-left py-1.5 px-3 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]"
                                    >
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {card.rows.map((row, ri) => (
                                  <tr
                                    key={ri}
                                    className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                                  >
                                    {row
                                      .filter((_, ci) => card.headers[ci])
                                      .map((cell, ci) => (
                                        <td
                                          key={ci}
                                          className={`py-1.5 px-3 ${
                                            ci === 0 ? "font-mono font-bold text-[#003c33]" : "text-muted-foreground"
                                          } ${
                                            ci === 2 && cell === "Zorunlu"
                                              ? "text-red-600 dark:text-red-400 font-semibold"
                                              : ""
                                          }`}
                                        >
                                          {cell}
                                        </td>
                                      ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-bold">Mülakat Prompt Değişkenleri</CardTitle>
                      <CardDescription>Her persona–soru turunda modele gönderilen bağlam değişkenleri.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-1.5">
                        {(schemas.interview_schema?.prompt_variables ?? []).map(v => (
                          <Badge key={v} variant="outline" className="text-[10px] font-mono bg-[#f5f4f1]">
                            {v}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-bold">Brief Varsayılan Değerleri</CardTitle>
                      <CardDescription>
                        Yeni araştırma oluşturulduğunda Defne&apos;ye iletilecek varsayılan brief değerleri.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries({
                          default_market: "Hedef Pazar",
                          default_category: "Varsayılan Kategori",
                          default_expected_price: "Varsayılan Fiyat Modeli",
                          default_sales_channel: "Varsayılan Satış Kanalı",
                          default_success_metric: "Varsayılan Başarı Kriteri",
                        }).map(([key, label]) => (
                          <div key={key} className="space-y-1.5">
                            <Label className="text-xs">{label}</Label>
                            <div className="flex gap-2">
                              <Input
                                id={`brief-default-${key}`}
                                className="h-8 text-xs bg-background text-foreground"
                                defaultValue={briefDefaults[key] || ""}
                                placeholder="Boş bırakılabilir"
                              />
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-8 shrink-0 text-slate-800"
                                disabled={savingDefaults}
                                onClick={async () => {
                                  const el = document.getElementById(`brief-default-${key}`) as HTMLInputElement;
                                  if (!el) return;
                                  setSavingDefaults(true);
                                  try {
                                    await fetch("/api/admin/schemas/brief-defaults", {
                                      method: "PUT",
                                      headers: { "Content-Type": "application/json" },
                                      body: JSON.stringify({ [key]: el.value }),
                                    });
                                    toast.success(`${label} kaydedildi.`);
                                  } catch {
                                    toast.error("Kaydedilemedi.");
                                  } finally {
                                    setSavingDefaults(false);
                                  }
                                }}
                              >
                                {savingDefaults ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-sm font-bold">Varsayılan Mülakat Soruları</CardTitle>
                          <CardDescription className="mt-0.5">
                            workflow.py DEFAULT_QUESTIONS — system_config&apos;den override edilebilir.
                          </CardDescription>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-1.5 h-8 text-slate-800"
                          onClick={() => {
                            setEditingDefaultQ(!editingDefaultQ);
                            if (!editingDefaultQ) setDraftQuestions([...schemas.default_interview_questions]);
                          }}
                        >
                          <Pencil size={12} />
                          {editingDefaultQ ? "İptal" : "Düzenle"}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {editingDefaultQ ? (
                        <>
                          {draftQuestions.map((q, qi) => (
                            <div key={qi} className="flex gap-2">
                              <span className="text-xs font-mono text-muted-foreground w-5 shrink-0 mt-2.5">
                                {qi + 1}.
                              </span>
                              <Textarea
                                className="text-xs min-h-0 h-auto resize-none bg-background text-foreground"
                                rows={2}
                                value={q}
                                onChange={e => {
                                  const next = [...draftQuestions];
                                  next[qi] = e.target.value;
                                  setDraftQuestions(next);
                                }}
                              />
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-8 w-8 p-0 shrink-0 mt-1 text-red-500 hover:text-red-600"
                                onClick={() => setDraftQuestions(prev => prev.filter((_, i) => i !== qi))}
                              >
                                <X size={13} />
                              </Button>
                            </div>
                          ))}
                          <div className="flex gap-2 mt-3">
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-1.5 text-slate-800"
                              onClick={() => setDraftQuestions(prev => [...prev, ""])}
                            >
                              <Plus size={12} /> Soru Ekle
                            </Button>
                            <Button
                              size="sm"
                              className="gap-1.5 bg-[#17171c] hover:bg-[#17171c]/90 text-white"
                              disabled={savingDefaults}
                              onClick={async () => {
                                setSavingDefaults(true);
                                try {
                                  await fetch("/api/admin/schemas/interview-questions", {
                                    method: "PUT",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ questions: draftQuestions.filter(Boolean) }),
                                  });
                                  setSchemas(prev =>
                                    prev ? { ...prev, default_interview_questions: draftQuestions } : prev
                                  );
                                  setEditingDefaultQ(false);
                                  toast.success("Mülakat soruları güncellendi.");
                                } catch {
                                  toast.error("Kaydedilemedi.");
                                } finally {
                                  setSavingDefaults(false);
                                }
                              }}
                            >
                              {savingDefaults ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                              Kaydet
                            </Button>
                          </div>
                        </>
                      ) : (
                        <ol className="space-y-1.5">
                          {schemas.default_interview_questions.map((q, qi) => (
                            <li key={qi} className="flex gap-2 text-xs">
                              <span className="font-mono text-muted-foreground shrink-0">{qi + 1}.</span>
                              <span className="text-[#212121]">{q}</span>
                            </li>
                          ))}
                        </ol>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-bold">Kavram Havuzları (Concept Pools)</CardTitle>
                      <CardDescription>
                        intake.py → CONCEPT_POOLS — Defne&apos;nin ürün tipine göre seçtiği soru &amp; rol havuzları.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {Object.entries(schemas.concept_pools).map(([name, pool]) => (
                        <div key={name} className="border border-border rounded-lg overflow-hidden">
                          <button
                            type="button"
                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/40 transition-colors text-left"
                            onClick={() => setExpandedPool(expandedPool === name ? null : name)}
                          >
                            <div>
                              <div className="font-semibold text-sm">{pool.persona_name}</div>
                              <div className="text-xs text-muted-foreground font-mono">{name}</div>
                            </div>
                            {expandedPool === name ? (
                              <ChevronDown size={15} className="text-muted-foreground" />
                            ) : (
                              <ChevronRight size={15} className="text-muted-foreground" />
                            )}
                          </button>
                          {expandedPool === name && (
                            <div className="px-4 pb-4 space-y-3 border-t border-border bg-muted/20">
                              <div className="mt-3">
                                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1">
                                  Odak Alanları
                                </div>
                                <p className="text-xs text-[#616161] leading-relaxed">{pool.focus_areas}</p>
                              </div>
                              <div>
                                <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1.5">
                                  Soru Havuzu ({pool.questions.length})
                                </div>
                                <ol className="space-y-1">
                                  {pool.questions.map((q, qi) => (
                                    <li key={qi} className="flex gap-2 text-xs">
                                      <span className="font-mono text-muted-foreground shrink-0">{qi + 1}.</span>
                                      <span className="text-[#212121]">{q}</span>
                                    </li>
                                  ))}
                                </ol>
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>

            <TabsContent value="metrics" className="mt-6 flex-1 outline-none space-y-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
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
                            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
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
                            <div className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground mb-0.5">
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
                      <CardContent className="p-0">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-border bg-muted/40">
                              {["Plan", "Danışan", "Token (toplam)", "Simülasyon"].map(h => (
                                <th
                                  key={h}
                                  className="text-left py-2 px-4 text-[10px] font-bold uppercase text-muted-foreground"
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
                </>
              )}
            </TabsContent>
          </div>
        </Tabs>
      </div>

      {/* Question Delete Confirmation Modal */}
      <Dialog open={!!deleteQuestionTarget} onOpenChange={(o) => !o && setDeleteQuestionTarget(null)}>
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
              onClick={() => setDeleteQuestionTarget(null)}
              className="flex-1 h-9 px-4 text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors"
            >
              İptal
            </button>
            <button
              onClick={() => deleteQuestionTarget && deleteQuestion(deleteQuestionTarget)}
              disabled={deletingQuestion}
              className="flex-1 h-9 px-4 text-sm font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {deletingQuestion && <Loader2 size={14} className="animate-spin" />}
              Evet, Sil
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}