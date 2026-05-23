"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Settings, Users, Activity, ListOrdered,
  MessageSquare, Heart, HeartOff, Trash2,
  Plus, Save, Loader2, Pencil, Check, X, Code, ChevronDown, ChevronRight
} from "lucide-react";

// ─── Type Definitions ────────────────────────────────────────────────────────

interface AdminConfig {
  b2c_model?: string;
  b2b_model?: string;
  pii_active?: string;
  pii_terms?: string;
  wizard_prompt?: string;
  persona_interview_prompt?: string;
  synthesis_prompt?: string;
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

interface SchemaField { key: string; type: string; required?: boolean; desc: string; }
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

// ─── Plan Templates ──────────────────────────────────────────────────────────

const PLAN_TEMPLATES: Record<string, { max_simulations: number; max_tokens: number }> = {
  Free:       { max_simulations: 2,    max_tokens: 50_000 },
  Starter:    { max_simulations: 10,   max_tokens: 200_000 },
  Pro:        { max_simulations: 50,   max_tokens: 1_000_000 },
  Enterprise: { max_simulations: 9999, max_tokens: 50_000_000 },
};

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

  // New Client Form
  const [showClientForm, setShowClientForm] = useState(false);
  const [clientForm, setClientForm] = useState({
    username: "", email: "", plan_type: "Free",
    max_simulations: 2, max_tokens: 50000,
    plan_start: "", plan_end: ""
  });
  const [savingClient, setSavingClient] = useState(false);

  // Apply plan template to form
  const applyTemplate = (planName: string) => {
    const tpl = PLAN_TEMPLATES[planName];
    if (tpl) {
      setClientForm(f => ({ ...f, plan_type: planName, max_simulations: tpl.max_simulations, max_tokens: tpl.max_tokens }));
    } else {
      setClientForm(f => ({ ...f, plan_type: planName }));
    }
  };

  const applyTemplateToEdit = (planName: string) => {
    const tpl = PLAN_TEMPLATES[planName];
    if (tpl) {
      setEditForm(f => ({ ...f, plan_type: planName, max_simulations: tpl.max_simulations, max_tokens: tpl.max_tokens }));
    } else {
      setEditForm(f => ({ ...f, plan_type: planName }));
    }
  };

  // Edit Client inline
  const [editingClient, setEditingClient] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<ClientInfo>>({});

  // Edit question purpose
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null);
  const [editPurpose, setEditPurpose] = useState("");

  const fetchAll = useCallback(() => {
    Promise.all([
      fetch("http://localhost:8000/api/admin/config").then(r => r.json()),
      fetch("http://localhost:8000/api/admin/clients").then(r => r.json()),
      fetch("http://localhost:8000/api/admin/personas").then(r => r.json()),
      fetch("http://localhost:8000/api/admin/audit_logs").then(r => r.json()),
      fetch("http://localhost:8000/api/admin/questions").then(r => r.json()),
      fetch("http://localhost:8000/api/admin/feedbacks").then(r => r.json()),
    ]).then(([conf, cli, pers, lg, qs, fbs]) => {
      setConfig(conf);
      setClients(Array.isArray(cli) ? cli : []);
      setPersonas(Array.isArray(pers) ? pers : []);
      setLogs(Array.isArray(lg) ? lg : []);
      setQuestions(Array.isArray(qs) ? qs : []);
      setFeedbacks(Array.isArray(fbs) ? fbs : []);
      setLoading(false);
    }).catch(() => {
      toast.error("Veriler yüklenirken hata oluştu.");
      setLoading(false);
    });
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // ── Config Saving ──────────────────────────────────────────────────────────
  const saveConfig = async (key: string, value: string) => {
    setSavingConfig(key);
    try {
      const res = await fetch("http://localhost:8000/api/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value })
      });
      if (!res.ok) throw new Error();
      toast.success("Ayar kaydedildi.");
    } catch {
      toast.error("Ayar kaydedilemedi.");
    } finally {
      setSavingConfig(null);
    }
  };

  // ── Client CRUD ────────────────────────────────────────────────────────────
  const createClient = async () => {
    setSavingClient(true);
    try {
      const res = await fetch("http://localhost:8000/api/admin/clients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(clientForm)
      });
      if (!res.ok) throw new Error();
      toast.success("Danışan eklendi.");
      setShowClientForm(false);
      setClientForm({ username: "", email: "", plan_type: "Free", max_simulations: 2, max_tokens: 100000, plan_start: "", plan_end: "" });
      fetchAll();
    } catch {
      toast.error("Danışan eklenemedi.");
    } finally {
      setSavingClient(false);
    }
  };

  const updateClient = async (username: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/admin/clients/${username}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: editForm.email || "",
          plan_type: editForm.plan_type || "Free",
          max_simulations: editForm.max_simulations || 2,
          max_tokens: editForm.max_tokens || 100000,
          plan_start: editForm.plan_start || "",
          plan_end: editForm.plan_end || "",
          status: editForm.status || "Aktif"
        })
      });
      if (!res.ok) throw new Error();
      toast.success("Danışan güncellendi.");
      setEditingClient(null);
      fetchAll();
    } catch {
      toast.error("Güncelleme başarısız.");
    }
  };

  const deleteClient = async (username: string) => {
    if (!confirm(`"${username}" danışanını silmek istediğinize emin misiniz?`)) return;
    try {
      const res = await fetch(`http://localhost:8000/api/admin/clients/${username}`, { method: "DELETE" });
      if (!res.ok) throw new Error();
      toast.success("Danışan silindi.");
      fetchAll();
    } catch {
      toast.error("Silme başarısız.");
    }
  };

  // ── Question Management ─────────────────────────────────────────────────────
  const toggleLike = async (id: number, current: boolean) => {
    try {
      await fetch(`http://localhost:8000/api/admin/questions/${id}/like?is_liked=${!current}`, { method: "PUT" });
      setQuestions(prev => prev.map(q => q.id === id ? { ...q, is_liked: !current } : q));
      toast.success("Beğeni güncellendi.");
    } catch {
      toast.error("İşlem başarısız.");
    }
  };

  const savePurpose = async (id: number) => {
    try {
      await fetch(`http://localhost:8000/api/admin/questions/${id}/purpose?purpose=${encodeURIComponent(editPurpose)}`, { method: "PUT" });
      setQuestions(prev => prev.map(q => q.id === id ? { ...q, purpose_context: editPurpose } : q));
      setEditingQuestion(null);
      toast.success("Amaç güncellendi.");
    } catch {
      toast.error("Güncelleme başarısız.");
    }
  };

  const deleteQuestion = async (id: number) => {
    if (!confirm("Bu soruyu koleksiyondan silmek istediğinize emin misiniz?")) return;
    try {
      await fetch(`http://localhost:8000/api/admin/questions/${id}`, { method: "DELETE" });
      setQuestions(prev => prev.filter(q => q.id !== id));
      toast.success("Soru silindi.");
    } catch {
      toast.error("Silme başarısız.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="h-10 w-10 animate-spin text-indigo-600 mx-auto" />
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
            <Link href="/" className="w-10 h-10 bg-primary text-primary-foreground flex items-center justify-center font-bold rounded-lg shadow-sm hover:opacity-90 transition-opacity">
              Q
            </Link>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-primary">Clarere Yönetici Paneli</h1>
              <p className="text-sm text-muted-foreground">Sistem, Model ve Limit Yönetimi</p>
            </div>
          </div>
        </header>

        <Tabs defaultValue="clients" className="w-full">
          <TabsList className="grid w-full grid-cols-7 bg-muted p-1 rounded-lg">
            <TabsTrigger value="clients" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md">
              <Users size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Danışanlar</span>
            </TabsTrigger>
            <TabsTrigger value="config" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md">
              <Settings size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Yapılandırma</span>
            </TabsTrigger>
            <TabsTrigger value="personas" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md">
              <ListOrdered size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Personalar</span>
            </TabsTrigger>
            <TabsTrigger value="questions" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md">
              <MessageSquare size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Soru Koleksiyonu</span>
            </TabsTrigger>
            <TabsTrigger value="feedbacks" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md">
              <Heart size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Geri Bildirimler</span>
            </TabsTrigger>
            <TabsTrigger value="logs" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md">
              <Activity size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Denetim Kayıtları</span>
            </TabsTrigger>
            <TabsTrigger value="schemas" className="data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-sm rounded-md" onClick={() => {
              if (!schemas) {
                setSchemasLoading(true);
                fetch("http://localhost:8000/api/admin/schemas")
                  .then(r => r.json())
                  .then(d => { setSchemas(d); setBriefDefaults(d.brief_schema.defaults); setDraftQuestions(d.default_interview_questions); })
                  .catch(() => toast.error("Şemalar yüklenemedi."))
                  .finally(() => setSchemasLoading(false));
              }
            }}>
              <Code size={16} className="sm:mr-2" />
              <span className="hidden sm:inline">Ajan Şablonları</span>
            </TabsTrigger>
          </TabsList>

          {/* ══════════════ TAB: CLIENTS ══════════════ */}
          <TabsContent value="clients" className="mt-6 space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Danışan Yönetimi</h2>
                <p className="text-sm text-muted-foreground">Sisteme kayıtlı kurumsal müşteriler ve simülasyon limitleri.</p>
              </div>
              <Button onClick={() => setShowClientForm(!showClientForm)} className="gap-2">
                <Plus size={16} />
                Yeni Danışan
              </Button>
            </div>

            {/* Add Client Form */}
            {showClientForm && (
              <Card className="border-indigo-200 dark:border-indigo-900/40 bg-indigo-50/30 dark:bg-indigo-950/10 animate-in fade-in slide-in-from-top-2 duration-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base text-indigo-700 dark:text-indigo-300">Yeni Danışan Ekle</CardTitle>
                </CardHeader>
                <CardContent>
                  {/* Plan Template Quick-Select */}
                  <div className="mb-4 p-3 bg-white dark:bg-slate-900 border border-border rounded-lg space-y-2">
                    <Label className="text-xs font-bold text-muted-foreground uppercase">Plan Şablonu Seç (Limitler Otomatik Dolar)</Label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(PLAN_TEMPLATES).map(([name, tpl]) => (
                        <button
                          key={name}
                          type="button"
                          onClick={() => applyTemplate(name)}
                          className={`flex flex-col items-start px-3 py-2 rounded-lg border-2 transition-all text-left ${
                            clientForm.plan_type === name
                              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/30"
                              : "border-border hover:border-indigo-300 dark:hover:border-indigo-700"
                          }`}
                        >
                          <span className={`font-bold text-sm ${clientForm.plan_type === name ? "text-indigo-700 dark:text-indigo-300" : ""}`}>{name}</span>
                          <span className="text-[10px] text-muted-foreground">
                            {tpl.max_simulations >= 9999 ? "∞" : tpl.max_simulations} sim · {tpl.max_tokens >= 1_000_000 ? (tpl.max_tokens / 1_000_000).toFixed(0) + "M" : (tpl.max_tokens / 1_000).toFixed(0) + "K"} token
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="space-y-1.5">
                      <Label>Kullanıcı Adı</Label>
                      <Input value={clientForm.username} onChange={e => setClientForm(f => ({ ...f, username: e.target.value }))} placeholder="ornek_musteri" />
                    </div>
                    <div className="space-y-1.5">
                      <Label>E-Posta</Label>
                      <Input value={clientForm.email} onChange={e => setClientForm(f => ({ ...f, email: e.target.value }))} placeholder="ornek@firma.com" />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Maks. Simülasyon</Label>
                      <Input type="number" value={clientForm.max_simulations} onChange={e => setClientForm(f => ({ ...f, max_simulations: +e.target.value }))} />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Maks. Token</Label>
                      <Input type="number" value={clientForm.max_tokens} onChange={e => setClientForm(f => ({ ...f, max_tokens: +e.target.value }))} />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Plan Bitiş (opsiyonel)</Label>
                      <Input type="date" value={clientForm.plan_end} onChange={e => setClientForm(f => ({ ...f, plan_end: e.target.value }))} />
                    </div>
                  </div>
                  <div className="flex gap-2 mt-4 justify-end">
                    <Button variant="outline" onClick={() => setShowClientForm(false)}>İptal</Button>
                    <Button onClick={createClient} disabled={savingClient || !clientForm.username} className="gap-2">
                      {savingClient && <Loader2 size={14} className="animate-spin" />}
                      Kaydet
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}


            <Card>
              <CardContent className="pt-4">
                <div className="overflow-x-auto w-full">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Kullanıcı</TableHead>
                        <TableHead>E-Posta</TableHead>
                        <TableHead>Plan</TableHead>
                        <TableHead>Kullanım</TableHead>
                        <TableHead>Token</TableHead>
                        <TableHead>Durum</TableHead>
                        <TableHead className="text-right">İşlemler</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {clients.map(cli => (
                        <TableRow key={cli.username}>
                          <TableCell className="font-medium">{cli.username}</TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {editingClient === cli.username
                              ? <Input className="h-7 text-xs" value={editForm.email || ""} onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))} />
                              : cli.email}
                          </TableCell>
                          <TableCell>
                            {editingClient === cli.username
                              ? (
                                <select
                                  className="h-7 text-xs border border-border rounded-md px-1.5 bg-background"
                                  value={editForm.plan_type || ""}
                                  onChange={e => applyTemplateToEdit(e.target.value)}
                                >
                                  {Object.keys(PLAN_TEMPLATES).map(p => (
                                    <option key={p} value={p}>{p}</option>
                                  ))}
                                </select>
                              )
                              : <Badge variant="outline">{cli.plan_type}</Badge>}
                          </TableCell>
                          <TableCell className="text-sm">
                            <span className={cli.total_simulations >= cli.max_simulations ? "text-red-600 font-semibold" : ""}>
                              {cli.total_simulations} / {editingClient === cli.username
                                ? <input className="h-7 text-xs w-16 border border-border rounded px-1 bg-background" type="number" value={editForm.max_simulations ?? cli.max_simulations} onChange={e => setEditForm(f => ({ ...f, max_simulations: +e.target.value }))} />
                                : cli.max_simulations}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {editingClient === cli.username ? (
                              <div className="flex items-center gap-1">
                                <span className="text-muted-foreground">{cli.tokens_used?.toLocaleString()} /</span>
                                <input
                                  className="h-7 text-xs w-24 border border-border rounded px-1 bg-background"
                                  type="number"
                                  value={editForm.max_tokens ?? cli.max_tokens}
                                  onChange={e => setEditForm(f => ({ ...f, max_tokens: +e.target.value }))}
                                />
                              </div>
                            ) : (
                              <span>{cli.tokens_used?.toLocaleString()} / <strong>{(cli.max_tokens >= 1_000_000 ? (cli.max_tokens / 1_000_000).toFixed(0) + "M" : cli.max_tokens >= 1_000 ? (cli.max_tokens / 1_000).toFixed(0) + "K" : cli.max_tokens)}</strong></span>
                            )}
                          </TableCell>
                          <TableCell>
                            {cli.status === "Aktif"
                              ? <Badge className="bg-emerald-600 hover:bg-emerald-700 text-xs">Aktif</Badge>
                              : <Badge variant="secondary" className="text-xs">{cli.status}</Badge>}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1.5 justify-end">
                              {editingClient === cli.username ? (
                                <>
                                  <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-emerald-600 hover:text-emerald-700" onClick={() => updateClient(cli.username)}>
                                    <Check size={14} />
                                  </Button>
                                  <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-muted-foreground" onClick={() => setEditingClient(null)}>
                                    <X size={14} />
                                  </Button>
                                </>
                              ) : (
                                <>
                                  <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground" onClick={() => { setEditingClient(cli.username); setEditForm(cli); }}>
                                    <Pencil size={14} />
                                  </Button>
                                  <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20" onClick={() => deleteClient(cli.username)}>
                                    <Trash2 size={14} />
                                  </Button>
                                </>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: CONFIG ══════════════ */}
          <TabsContent value="config" className="mt-6 space-y-6">
            <div>
              <h2 className="text-xl font-bold">Sistem Yapılandırması</h2>
              <p className="text-sm text-muted-foreground">Yapay zeka modelleri, PII/KVKK ayarları ve sistem promptları.</p>
            </div>

            {/* Model & PII Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Model & Güvenlik Ayarları</CardTitle>
                <CardDescription>B2C/B2B modelleri ve kişisel veri maskeleme yapılandırması.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  {[
                    { key: "b2c_model", label: "B2C Modeli" },
                    { key: "b2b_model", label: "B2B Modeli" },
                    { key: "pii_terms", label: "PII Maskeleme Terimleri (virgülle ayrılmış)" },
                  ].map(({ key, label }) => (
                    <div key={key} className="space-y-1.5">
                      <Label>{label}</Label>
                      <div className="flex gap-2">
                        <Input
                          id={`config-${key}`}
                          defaultValue={(config as Record<string, string>)[key] || ""}
                          className="flex-1"
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={savingConfig === key}
                          onClick={() => {
                            const el = document.getElementById(`config-${key}`) as HTMLInputElement;
                            if (el) saveConfig(key, el.value);
                          }}
                          className="shrink-0 gap-1.5"
                        >
                          {savingConfig === key ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                          Kaydet
                        </Button>
                      </div>
                    </div>
                  ))}
                  <div className="space-y-1.5">
                    <Label>PII Maskeleme (KVKK)</Label>
                    <div className="flex items-center gap-3 h-10">
                      <Badge className={config.pii_active === "true" ? "bg-emerald-600 hover:bg-emerald-700" : "bg-slate-500"}>
                        {config.pii_active === "true" ? "Aktif" : "Pasif"}
                      </Badge>
                      <Button size="sm" variant="outline" onClick={() => saveConfig("pii_active", config.pii_active === "true" ? "false" : "true")}>
                        {config.pii_active === "true" ? "Pasife Al" : "Aktive Et"}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Prompt Editors */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sistem Prompt Editörleri</CardTitle>
                <CardDescription>Araştırma sihirbazı, persona mülakat ve sentez raporu için LLM system promptları.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {[
                  { key: "wizard_prompt", label: "Araştırma Sihirbazı Promptu (Defne)" },
                  { key: "persona_interview_prompt", label: "Persona Mülakat Promptu" },
                  { key: "synthesis_prompt", label: "Sentez Raporu Promptu" },
                ].map(({ key, label }) => (
                  <div key={key} className="space-y-2">
                    <Label className="font-semibold">{label}</Label>
                    <Textarea
                      id={`prompt-${key}`}
                      defaultValue={(config as Record<string, string>)[key] || ""}
                      rows={5}
                      className="text-sm font-mono bg-slate-50 dark:bg-slate-900"
                    />
                    <div className="flex justify-end">
                      <Button
                        size="sm"
                        disabled={savingConfig === key}
                        onClick={() => {
                          const el = document.getElementById(`prompt-${key}`) as HTMLTextAreaElement;
                          if (el) saveConfig(key, el.value);
                        }}
                        className="gap-2"
                      >
                        {savingConfig === key ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                        Promptu Kaydet
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: PERSONAS ══════════════ */}
          <TabsContent value="personas" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Sentetik Tüketici Havuzu <span className="text-muted-foreground font-normal text-sm">({personas.length} persona)</span></CardTitle>
                <CardDescription>Global ve müşteri özel personaların tam listesi.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto w-full">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>İsim & Yaş</TableHead>
                        <TableHead>Lokasyon</TableHead>
                        <TableHead>Rol / Segment</TableHead>
                        <TableHead>SES</TableHead>
                        <TableHead>Katılımcı Tipi</TableHead>
                        <TableHead>Tür</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {personas.map(p => (
                        <TableRow key={p.id}>
                          <TableCell className="font-medium">{p.name}, {p.age}</TableCell>
                          <TableCell className="text-muted-foreground">{p.city}</TableCell>
                          <TableCell>{p.role_title || p.segment}</TableCell>
                          <TableCell>
                            {p.ses_group ? (
                              <Badge variant="outline" className={
                                p.ses_group === "AB" ? "border-amber-300 text-amber-700 dark:text-amber-400" :
                                p.ses_group === "C1" ? "border-blue-300 text-blue-700 dark:text-blue-400" :
                                p.ses_group === "C2" ? "border-slate-300 text-slate-600 dark:text-slate-400" :
                                "border-rose-300 text-rose-700 dark:text-rose-400"
                              }>{p.ses_group}</Badge>
                            ) : <span className="text-muted-foreground text-xs">—</span>}
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {({
                              potential_customer: "Potansiyel",
                              competitor_user: "Rakip Kullanıcı",
                              churned_user: "Kaybedilmiş",
                              decision_maker: "Karar Verici",
                              individual_user: "Bireysel",
                            } as Record<string, string>)[p.respondent_type ?? ""] ?? "—"}
                          </TableCell>
                          <TableCell>
                            {p.is_global ? <Badge variant="secondary">Global</Badge> : <Badge variant="outline">Müşteri Özel</Badge>}
                          </TableCell>
                        </TableRow>
                      ))}

                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: QUESTIONS ══════════════ */}
          <TabsContent value="questions" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Curated Soru Koleksiyonu <span className="text-muted-foreground font-normal text-sm">({questions.length} soru)</span></CardTitle>
                <CardDescription>
                  Araştırma motorunun sihirbaz sohbetinde kullandığı seçilmiş soru havuzu.
                  Beğenilen sorular aktif simülasyonlarda öneri olarak kullanılır.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {questions.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                    Henüz koleksiyonda soru bulunmuyor. Simülasyonlar tamamlandıkça sorular buraya eklenir.
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                    {questions.map(q => (
                      <div key={q.id} className="p-4 border border-border rounded-xl hover:border-indigo-200 dark:hover:border-indigo-900/40 transition-colors space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm text-slate-800 dark:text-slate-200 font-medium leading-relaxed flex-1">{q.question}</p>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => toggleLike(q.id, q.is_liked)}
                              className={`h-8 w-8 p-0 ${q.is_liked ? "text-red-500 hover:text-red-600" : "text-muted-foreground hover:text-red-400"}`}
                            >
                              {q.is_liked ? <Heart size={15} fill="currentColor" /> : <HeartOff size={15} />}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => { setEditingQuestion(q.id); setEditPurpose(q.purpose_context || ""); }}
                              className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                            >
                              <Pencil size={14} />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => deleteQuestion(q.id)}
                              className="h-8 w-8 p-0 text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                            >
                              <Trash2 size={14} />
                            </Button>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                          {q.research_category && <Badge variant="outline" className="text-[10px]">{q.research_category}</Badge>}
                          {q.research_title && <span>"{q.research_title}"</span>}
                          {!q.is_liked && <Badge variant="secondary" className="text-[10px] text-slate-500">Pasif (simülasyonda kullanılmıyor)</Badge>}
                        </div>

                        {editingQuestion === q.id && (
                          <div className="flex gap-2 mt-2 animate-in fade-in slide-in-from-top-1 duration-200">
                            <Input
                              value={editPurpose}
                              onChange={e => setEditPurpose(e.target.value)}
                              placeholder="Bu sorunun amacı / bağlamı..."
                              className="text-xs h-8 flex-1"
                            />
                            <Button size="sm" className="h-8 gap-1.5 text-xs" onClick={() => savePurpose(q.id)}>
                              <Check size={13} />
                              Kaydet
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8" onClick={() => setEditingQuestion(null)}>
                              <X size={13} />
                            </Button>
                          </div>
                        )}
                        {q.purpose_context && editingQuestion !== q.id && (
                          <p className="text-xs text-indigo-600 dark:text-indigo-400 italic">Amaç: {q.purpose_context}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: FEEDBACKS ══════════════ */}
          <TabsContent value="feedbacks" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Kullanıcı Geri Bildirimleri <span className="text-muted-foreground font-normal text-sm">({feedbacks.length} kayıt)</span></CardTitle>
                <CardDescription>Araştırma sonuçlarına verilen mülakatçı oyları ve yorumlar.</CardDescription>
              </CardHeader>
              <CardContent>
                {feedbacks.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                    Henüz geri bildirim bulunmuyor.
                  </div>
                ) : (
                  <div className="overflow-x-auto w-full">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Tarih</TableHead>
                          <TableHead>Kullanıcı</TableHead>
                          <TableHead>Araştırma ID</TableHead>
                          <TableHead>Tür</TableHead>
                          <TableHead>Oy</TableHead>
                          <TableHead>Yorum</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {feedbacks.map(fb => (
                          <TableRow key={fb.id}>
                            <TableCell className="text-xs text-muted-foreground">
                              {fb.created_at ? new Date(fb.created_at).toLocaleString("tr-TR") : "-"}
                            </TableCell>
                            <TableCell className="font-medium text-sm">{fb.username || "-"}</TableCell>
                            <TableCell className="text-xs text-muted-foreground font-mono">
                              {fb.study_id ? fb.study_id.slice(0, 12) + "..." : "-"}
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-[10px]">{fb.item_type || "genel"}</Badge>
                            </TableCell>
                            <TableCell>
                              {fb.vote === 1
                                ? <span className="text-emerald-600 font-bold flex items-center gap-1"><Heart size={14} fill="currentColor" /> Beğendi</span>
                                : <span className="text-red-500 font-bold flex items-center gap-1"><HeartOff size={14} /> Beğenmedi</span>}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground max-w-xs truncate">{fb.comment || "—"}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: AUDIT LOGS ══════════════ */}
          <TabsContent value="logs" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Denetim Kayıtları <span className="text-muted-foreground font-normal text-sm">({logs.length} kayıt)</span></CardTitle>
                <CardDescription>Simülasyon motorundaki kalite uyarıları, hallüsinasyon tespitleri ve aksiyon kayıtları.</CardDescription>
              </CardHeader>
              <CardContent>
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
                      ) : logs.map(log => (
                        <TableRow key={log.id}>
                          <TableCell className="text-muted-foreground text-xs">
                            {new Date(log.created_at).toLocaleString("tr-TR")}
                          </TableCell>
                          <TableCell className="font-medium">{log.persona_name}</TableCell>
                          <TableCell>
                            <span className="text-red-600 dark:text-red-400 text-sm font-medium">{log.error_reason}</span>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">{log.action_taken}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: SCHEMAS ══════════════ */}
          <TabsContent value="schemas" className="mt-6 space-y-6">
            <div>
              <h2 className="text-xl font-bold">Ajan Şablonları &amp; JSON Akışı</h2>
              <p className="text-sm text-muted-foreground">Ajanlara iletilen veri yapıları, varsayılan soru havuzları ve brief şablonları.</p>
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
                {/* ── Flow Diagram ── */}
                <Card className="border-indigo-100 dark:border-indigo-900/30 bg-indigo-50/20 dark:bg-indigo-950/10">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold text-indigo-700 dark:text-indigo-300">Veri Akış Şeması</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap items-center gap-2 text-sm font-mono">
                      {[
                        { label: "Brief (Defne)", color: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300" },
                        { label: "→", color: "text-muted-foreground" },
                        { label: "ResearchPlan", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
                        { label: "→", color: "text-muted-foreground" },
                        { label: "Persona[]", color: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300" },
                        { label: "→", color: "text-muted-foreground" },
                        { label: "Interview[]", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300" },
                        { label: "→", color: "text-muted-foreground" },
                        { label: "ResearchReport", color: "bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300" },
                      ].map((s, i) => (
                        <span key={i} className={`px-2.5 py-1 rounded-lg font-semibold text-xs ${s.color}`}>{s.label}</span>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* ── 4 Schema Cards ── */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {[
                    {
                      title: "Brief Şeması",
                      desc: schemas.brief_schema?.description ?? "",
                      badge: "Defne → intake.py",
                      badgeColor: "border-indigo-200 text-indigo-700 dark:border-indigo-800 dark:text-indigo-300",
                      rows: (schemas.brief_schema?.fields ?? []).map(f => [
                        f.key, f.type, f.required ? "Zorunlu" : "Opsiyonel", f.desc,
                      ]),
                      headers: ["Alan", "Tip", "Durum", "Açıklama"],
                    },
                    {
                      title: "Persona Şeması",
                      desc: schemas.persona_schema?.description ?? "",
                      badge: "workflow.py → LLM",
                      badgeColor: "border-emerald-200 text-emerald-700 dark:border-emerald-800 dark:text-emerald-300",
                      rows: (schemas.persona_schema?.fields ?? []).map(f => ([f.key, f.type, "", f.desc])),
                      headers: ["Alan", "Tip", "", "Açıklama"],
                    },
                    {
                      title: "Mülakat Turu Çıktısı",
                      desc: schemas.interview_schema?.description ?? "",
                      badge: "interview turn → LLM",
                      badgeColor: "border-amber-200 text-amber-700 dark:border-amber-800 dark:text-amber-300",
                      rows: Object.entries(schemas.interview_schema?.output ?? {}).map(([k, v]) => ([k, "", "", v])),
                      headers: ["Alan", "", "", "Açıklama"],
                    },
                    {
                      title: "Sentez Raporu Çıktısı",
                      desc: schemas.synthesis_schema?.description ?? "",
                      badge: "analytics.py",
                      badgeColor: "border-rose-200 text-rose-700 dark:border-rose-800 dark:text-rose-300",
                      rows: (schemas.synthesis_schema?.output_fields ?? []).map(f => ([f, "", "", ""])),
                      headers: ["Alan", "", "", ""],
                    },

                  ].map(card => (
                    <Card key={card.title} className="overflow-hidden">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between gap-2">
                          <CardTitle className="text-sm font-bold">{card.title}</CardTitle>
                          <Badge variant="outline" className={`text-[10px] font-mono shrink-0 ${card.badgeColor}`}>{card.badge}</Badge>
                        </div>
                        <CardDescription className="text-xs">{card.desc}</CardDescription>
                      </CardHeader>
                      <CardContent className="p-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-t border-b border-border bg-muted/40">
                                {card.headers.filter(Boolean).map(h => (
                                  <th key={h} className="text-left py-1.5 px-3 font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {card.rows.map((row, ri) => (
                                <tr key={ri} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                                  {row.filter((_, ci) => card.headers[ci]).map((cell, ci) => (
                                    <td key={ci} className={`py-1.5 px-3 ${
                                      ci === 0 ? "font-mono font-bold text-indigo-700 dark:text-indigo-300" : "text-muted-foreground"
                                    } ${ci === 2 && cell === "Zorunlu" ? "text-red-600 dark:text-red-400 font-semibold" : ""}`}>
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

                {/* ── Prompt Variables (Interview) ── */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold">Mülakat Prompt Değişkenleri</CardTitle>
                    <CardDescription>Her persona–soru turunda modele gönderilen bağlam değişkenleri.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1.5">
                      {(schemas.interview_schema?.prompt_variables ?? []).map(v => (
                        <Badge key={v} variant="outline" className="text-[10px] font-mono bg-slate-50 dark:bg-slate-900">{v}</Badge>
                      ))}

                    </div>
                  </CardContent>
                </Card>

                {/* ── Brief Defaults Editor ── */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold">Brief Varsayılan Değerleri</CardTitle>
                    <CardDescription>Yeni araştırma oluşturulduğunda Defne'ye iletilecek varsayılan brief değerleri.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries({
                        default_market:         "Hedef Pazar",
                        default_category:       "Varsayılan Kategori",
                        default_expected_price: "Varsayılan Fiyat Modeli",
                        default_sales_channel:  "Varsayılan Satış Kanalı",
                        default_success_metric: "Varsayılan Başarı Kriteri",
                      }).map(([key, label]) => (
                        <div key={key} className="space-y-1.5">
                          <Label className="text-xs">{label}</Label>
                          <div className="flex gap-2">
                            <Input
                              id={`brief-default-${key}`}
                              className="h-8 text-xs"
                              defaultValue={briefDefaults[key] || ""}
                              placeholder="Boş bırakılabilir"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 shrink-0"
                              disabled={savingDefaults}
                              onClick={async () => {
                                const el = document.getElementById(`brief-default-${key}`) as HTMLInputElement;
                                if (!el) return;
                                setSavingDefaults(true);
                                try {
                                  await fetch("http://localhost:8000/api/admin/schemas/brief-defaults", {
                                    method: "PUT",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ [key]: el.value }),
                                  });
                                  toast.success(`${label} kaydedildi.`);
                                } catch { toast.error("Kaydedilemedi."); }
                                finally { setSavingDefaults(false); }
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

                {/* ── Default Interview Questions ── */}
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-sm font-bold">Varsayılan Mülakat Soruları</CardTitle>
                        <CardDescription className="mt-0.5">workflow.py DEFAULT_QUESTIONS — system_config'den override edilebilir.</CardDescription>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 h-8"
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
                            <span className="text-xs font-mono text-muted-foreground w-5 shrink-0 mt-2.5">{qi + 1}.</span>
                            <Textarea
                              className="text-xs min-h-0 h-auto resize-none"
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
                            className="gap-1.5"
                            onClick={() => setDraftQuestions(prev => [...prev, ""])}
                          >
                            <Plus size={12} /> Soru Ekle
                          </Button>
                          <Button
                            size="sm"
                            className="gap-1.5 bg-indigo-600 hover:bg-indigo-700"
                            disabled={savingDefaults}
                            onClick={async () => {
                              setSavingDefaults(true);
                              try {
                                await fetch("http://localhost:8000/api/admin/schemas/interview-questions", {
                                  method: "PUT",
                                  headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({ questions: draftQuestions.filter(Boolean) }),
                                });
                                setSchemas(prev => prev ? { ...prev, default_interview_questions: draftQuestions } : prev);
                                setEditingDefaultQ(false);
                                toast.success("Mülakat soruları güncellendi.");
                              } catch { toast.error("Kaydedilemedi."); }
                              finally { setSavingDefaults(false); }
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
                            <span className="text-slate-700 dark:text-slate-300">{q}</span>
                          </li>
                        ))}
                      </ol>
                    )}
                  </CardContent>
                </Card>

                {/* ── Concept Pools ── */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold">Kavram Havuzları (Concept Pools)</CardTitle>
                    <CardDescription>intake.py → CONCEPT_POOLS — Defne'nin ürün tipine göre seçtiği soru &amp; rol havuzları.</CardDescription>
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
                          {expandedPool === name ? <ChevronDown size={15} className="text-muted-foreground" /> : <ChevronRight size={15} className="text-muted-foreground" />}
                        </button>
                        {expandedPool === name && (
                          <div className="px-4 pb-4 space-y-3 border-t border-border bg-muted/20">
                            <div className="mt-3">
                              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1">Odak Alanları</div>
                              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{pool.focus_areas}</p>
                            </div>
                            <div>
                              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1.5">Soru Havuzu ({pool.questions.length})</div>
                              <ol className="space-y-1">
                                {pool.questions.map((q, qi) => (
                                  <li key={qi} className="flex gap-2 text-xs">
                                    <span className="font-mono text-muted-foreground shrink-0">{qi + 1}.</span>
                                    <span className="text-slate-700 dark:text-slate-300">{q}</span>
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
        </Tabs>
      </div>
    </div>
  );
}
