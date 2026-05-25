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
  Plus, Save, Loader2, Pencil, Check, X, Code, ChevronDown, ChevronRight,
  BarChart3, Cpu, Zap, Database, ThumbsUp, ThumbsDown, Eye
} from "lucide-react";
import Logo from "@/components/logo";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";

// ─── Feedback Table with Filters (E2) ───────────────────────────────────────

function FeedbackTable({ feedbacks }: { feedbacks: Array<{
  id: number; username?: string; study_id?: string; item_type?: string;
  vote: number; comment?: string; created_at?: string;
}> }) {
  const [voteFilter, setVoteFilter] = useState<"all" | "like" | "dislike">("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const itemTypes = ["all", ...Array.from(new Set(feedbacks.map(f => f.item_type || "genel")))];

  const filtered = feedbacks.filter(f => {
    const voteOk = voteFilter === "all" || (voteFilter === "like" ? f.vote === 1 : f.vote === -1);
    const typeOk = typeFilter === "all" || (f.item_type || "genel") === typeFilter;
    return voteOk && typeOk;
  });

  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base">
              Kullanıcı Geri Bildirimleri{" "}
              <span className="text-muted-foreground font-normal text-sm">
                ({filtered.length} / {feedbacks.length} kayıt)
              </span>
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Araştırma mülakat yanıtlarına verilen oylar ve yorumlar.
            </CardDescription>
          </div>

          {/* Filtreler */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Oy Yönü Toggle */}
            <div className="flex rounded-lg border border-border overflow-hidden text-xs font-semibold">
              {(["all", "like", "dislike"] as const).map(v => (
                <button
                  key={v}
                  onClick={() => setVoteFilter(v)}
                  className={`px-3 py-1.5 transition-colors ${
                    voteFilter === v
                      ? v === "like"
                        ? "bg-emerald-600 text-white"
                        : v === "dislike"
                        ? "bg-red-500 text-white"
                        : "bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900"
                      : "bg-card text-muted-foreground hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  {v === "all" ? "Tümü" : v === "like" ? <span className="flex items-center gap-1"><ThumbsUp className="w-3.5 h-3.5" /> Beğeni</span> : <span className="flex items-center gap-1"><ThumbsDown className="w-3.5 h-3.5" /> Beğenmedi</span>}
                </button>
              ))}
            </div>

            {/* Tür Filtresi */}
            {itemTypes.length > 2 && (
              <select
                value={typeFilter}
                onChange={e => setTypeFilter(e.target.value)}
                className="text-xs border border-border rounded-lg px-2.5 py-1.5 bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-[#4c6ee6] cursor-pointer"
              >
                {itemTypes.map(t => (
                  <option key={t} value={t}>
                    {t === "all" ? "Tüm Türler" : t}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground border-t border-border text-sm">
            {feedbacks.length === 0 ? "Henüz geri bildirim bulunmuyor." : "Seçili filtreye uygun kayıt yok."}
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[11px] uppercase tracking-wide">Tarih</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wide">Kullanıcı</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wide">Araştırma</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wide">Tür</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wide">Oy</TableHead>
                  <TableHead className="text-[11px] uppercase tracking-wide">Yorum</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(fb => {
                  const hasComment = fb.comment && fb.comment.trim().length > 0;
                  return (
                    <TableRow
                      key={fb.id}
                      className={hasComment ? "bg-amber-50/40 dark:bg-amber-950/10 hover:bg-amber-50/80 dark:hover:bg-amber-950/20" : undefined}
                    >
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                        {fb.created_at ? new Date(fb.created_at).toLocaleString("tr-TR") : "—"}
                      </TableCell>
                      <TableCell className="font-medium text-sm">{fb.username || "—"}</TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">
                        {fb.study_id ? fb.study_id.slice(0, 10) + "…" : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-[10px] font-semibold">
                          {fb.item_type || "genel"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {fb.vote === 1 ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold text-sm">
                            <ThumbsUp className="w-3.5 h-3.5 mr-1" /> Beğendi
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-500 dark:text-red-400 font-bold text-sm">
                            <ThumbsDown className="w-3.5 h-3.5 mr-1" /> Beğenmedi
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="max-w-xs">
                        {hasComment ? (
                          <span className="inline-block text-xs bg-amber-100 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40 rounded-md px-2 py-0.5 max-w-[200px] truncate" title={fb.comment}>
                            {fb.comment}
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-xs">—</span>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
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
  clients: { username: string; plan_type: string; tokens_used: number; max_tokens: number; total_simulations: number; max_simulations: number; period_simulations: number }[];
  study_stats: { total: number; avg_quality: number; with_report: number; archived: number; error_count: number };
  categories: { category: string; count: number }[];
  models: { b2c: string; b2b: string; orchestrator: string };
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
  Free: { max_simulations: 2, max_tokens: 50_000 },
  Starter: { max_simulations: 10, max_tokens: 200_000 },
  Pro: { max_simulations: 50, max_tokens: 1_000_000 },
  Enterprise: { max_simulations: 9999, max_tokens: 50_000_000 },
};

// ─── Predefined Persona Packages ─────────────────────────────────────────────

const PREDEFINED_PACKAGES = [
  {
    name: "Teknoloji Meraklısı Gençler",
    description: "Genç, dijital okuryazarlığı yüksek, yenilikçi 3 adet persona.",
    personas: [
      {
        name: "Can Yılmaz", age: 24, city: "İstanbul", segment: "Yazılımcı",
        stance: "Champion", price_sensitivity: 4, digital_confidence: 9,
        ses_group: "AB", respondent_type: "potential_customer", settlement_type: "kentsel",
        context: "SaaS araçlarını yakından takip ediyor, verimlilik araçlarına bütçe ayırıyor.",
        goals: ["En son teknolojileri kullanmak", "İş akışlarını otomatikleştirmek"],
        objections: ["Destek yetersizliği", "Dokümantasyon eksikliği"],
        knowledge_boundary: "İleri düzey teknik bilgiye sahip",
        bio: "İTÜ mezunu yazılım mühendisi. Yeni çıkan tüm üretken yapay zeka araçlarını beta aşamasında dener."
      },
      {
        name: "Melis Kaya", age: 22, city: "Ankara", segment: "Tasarımcı",
        stance: "Pragmatist", price_sensitivity: 6, digital_confidence: 8,
        ses_group: "C1", respondent_type: "potential_customer", settlement_type: "kentsel",
        context: "Tasarım programlarını aktif kullanıyor, arayüz kalitesine aşırı önem veriyor.",
        goals: ["Hızlı prototip üretmek", "Kullanıcı deneyimini mükemmelleştirmek"],
        objections: ["Yüksek abonelik ücretleri", "Karmaşık arayüzler"],
        knowledge_boundary: "Tasarım ve dijital ürünler konusunda uzman",
        bio: "Güzel Sanatlar Fakültesi mezunu UI/UX tasarımcısı. İşinde pratiklik ve görsellik arıyor."
      },
      {
        name: "Arda Demir", age: 20, city: "İzmir", segment: "Öğrenci",
        stance: "Skeptic", price_sensitivity: 9, digital_confidence: 8,
        ses_group: "C2", respondent_type: "potential_customer", settlement_type: "kentsel",
        context: "Öğrenci bütçesiyle hareket ediyor, ücretsiz veya indirimli alternatifleri arıyor.",
        goals: ["Akademik projelerini tamamlamak", "Düşük maliyetli çözümler bulmak"],
        objections: ["Öğrenci indiriminin olmaması", "Uzun taahhüt süreleri"],
        knowledge_boundary: "Genel teknoloji bilgisi",
        bio: "Ege Üniversitesi Bilgisayar Mühendisliği öğrencisi. Kısıtlı bütçeyle en yüksek verimi almaya çalışır."
      }
    ]
  },
  {
    name: "KOBİ ve Geleneksel Esnaf",
    description: "Dijitalleşmeye çalışan, maliyet odaklı, geleneksel 2 adet persona.",
    personas: [
      {
        name: "Mustafa Şahin", age: 48, city: "Bursa", segment: "Esnaf",
        stance: "Blocker", price_sensitivity: 8, digital_confidence: 4,
        ses_group: "C2", respondent_type: "competitor_user", settlement_type: "banliyö",
        context: "Geleneksel defter tutma yöntemlerini kullanıyor, dijitalleşmeye şüpheyle yaklaşıyor.",
        goals: ["Maliyetleri düşürmek", "Müşteri takibini kolaylaştırmak"],
        objections: ["Veri güvenliği endişesi", "Kullanım zorluğu"],
        knowledge_boundary: "Sadece temel akıllı telefon ve sosyal medya bilgisi",
        bio: "Bursa'da 20 yıllık tekstil atölyesi sahibi. İşleri hala büyük oranda kağıt üzerinde yürütüyor."
      },
      {
        name: "Hülya Öztürk", age: 39, city: "Konya", segment: "Perakendeci",
        stance: "Pragmatist", price_sensitivity: 7, digital_confidence: 6,
        ses_group: "C1", respondent_type: "potential_customer", settlement_type: "kentsel",
        context: "E-ticarete yeni adım atmış, sipariş takibinde pratik çözümler arıyor.",
        goals: ["Satışları artırmak", "Kargo süreçlerini kolaylaştırmak"],
        objections: ["Karmaşık entegrasyonlar", "Ekstra gizli komisyonlar"],
        knowledge_boundary: "Orta düzey bilgisayar ve e-ticaret paneli bilgisi",
        bio: "Ev dekorasyonu üzerine butik mağaza sahibi. Sosyal medyadan gelen siparişleri yönetmekte zorlanıyor."
      }
    ]
  },
  {
    name: "Premium B2B Karar Vericiler",
    description: "Kurumsal yöneticiler, verimlilik ve ROI odaklı 2 adet üst segment B2B persona.",
    personas: [
      {
        name: "Zeynep Akar", age: 42, city: "İstanbul", segment: "C-Level Yönetici",
        stance: "Champion", price_sensitivity: 3, digital_confidence: 9,
        ses_group: "AB", respondent_type: "decision_maker", settlement_type: "kentsel",
        context: "Büyük ölçekli ekipleri yönetiyor, kurumsal güvenlik ve KVKK uyumuna bakıyor.",
        goals: ["Ekip verimliliğini artırmak", "Yatırım getirisini (ROI) maksimize etmek"],
        objections: ["KVKK ve güvenlik uyumsuzluğu", "Entegrasyon ve onboarding süresi"],
        knowledge_boundary: "Üst düzey kurumsal yazılım ve strateji bilgisi",
        bio: "Özel bir holdingde CTO olarak görev yapıyor. Ekibinin hızlanmasını sağlayacak yenilikçi araçlara yatırım yapmaya açık."
      },
      {
        name: "Levent Tandoğan", age: 50, city: "İstanbul", segment: "Pazarlama Müdürü",
        stance: "Skeptic", price_sensitivity: 5, digital_confidence: 7,
        ses_group: "AB", respondent_type: "decision_maker", settlement_type: "kentsel",
        context: "Pazarlama bütçelerini yönetiyor, veri analitiği ve raporlama kalitesine bakıyor.",
        goals: ["Müşteri edinme maliyetini (CAC) düşürmek", "Veriye dayalı kararlar almak"],
        objections: ["Verilerin doğruluğu ve sapma payı", "Karmaşık raporlama ekranları"],
        knowledge_boundary: "Pazarlama teknolojileri ve veri analitiği uzmanı",
        bio: "Hızlı tüketim sektöründe 15 yıllık pazarlama direktörü. Reklam bütçelerinin etkinliğini ölçmek en büyük önceliği."
      }
    ]
  }
];

const parseJsonField = (field: any, fallback: any) => {
  if (!field) return fallback;
  if (typeof field === "object") return field;
  try {
    return JSON.parse(field);
  } catch {
    return fallback;
  }
};

const getBigFive = (p: PersonaInfo) => {
  const traits = parseJsonField(p.traits, {});
  if (traits && typeof traits === "object") {
    const o = traits.openness ?? traits.Openness;
    const c = traits.conscientiousness ?? traits.Conscientiousness;
    const e = traits.extroversion ?? traits.Extroversion;
    const a = traits.agreeableness ?? traits.Agreeableness;
    const n = traits.neuroticism ?? traits.Neuroticism;
    if (o !== undefined) {
      return {
        openness: typeof o === "number" ? o : parseInt(o) || 50,
        conscientiousness: typeof c === "number" ? c : parseInt(c) || 50,
        extroversion: typeof e === "number" ? e : parseInt(e) || 50,
        agreeableness: typeof a === "number" ? a : parseInt(a) || 50,
        neuroticism: typeof n === "number" ? n : parseInt(n) || 50,
      };
    }
  }
  
  const attrs = parseJsonField(p.attributes, {});
  if (attrs && attrs.personality) {
    const o = attrs.personality.openness ?? attrs.personality.Openness;
    const c = attrs.personality.conscientiousness ?? attrs.personality.Conscientiousness;
    const e = attrs.personality.extroversion ?? attrs.personality.Extroversion;
    const a = attrs.personality.agreeableness ?? attrs.personality.Agreeableness;
    const n = attrs.personality.neuroticism ?? attrs.personality.Neuroticism;
    if (o !== undefined) {
      return {
        openness: o, conscientiousness: c, extroversion: e, agreeableness: a, neuroticism: n
      };
    }
  }

  const s = p.stance || "";
  const openness = s === "Innovator" ? 90 : s === "EarlyAdopter" ? 75 : s === "Laggard" ? 25 : 50;
  const conscientiousness = p.ses_group === "AB" || p.ses_group === "C1" ? 80 : 45;
  const agreeableness = s === "Skeptic" ? 20 : s === "Innovator" ? 40 : 60;
  const neuroticism = s === "Skeptic" ? 85 : s === "Innovator" && p.ses_group === "AB" ? 20 : 50;
  const extroversion = s === "EarlyAdopter" || s === "Innovator" ? 85 : 50;

  return { openness, conscientiousness, extroversion, agreeableness, neuroticism };
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
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  // Persona Generation State
  const [generatingPersonas, setGeneratingPersonas] = useState(false);
  const [addingBulk, setAddingBulk] = useState<string | null>(null);
  const [genForm, setGenForm] = useState({
    role_title: "",
    count: 3,
    category: "genel",
    market: "Türkiye",
    target_users: "genel tüketici",
    why: "Hedef kitle temsilcisi",
    save_to_pool: true
  });

  const handleGeneratePersonas = async () => {
    if (!genForm.role_title.trim()) {
      toast.error("Lütfen bir rol başlığı girin.");
      return;
    }
    setGeneratingPersonas(true);
    try {
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/personas/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(genForm)
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      toast.success(`${data.generated_count || genForm.count} adet yapay zeka personası üretildi ve havuza eklendi.`);
      setGenForm(f => ({ ...f, role_title: "" }));
      fetchAll();
    } catch {
      toast.error("Yapay zeka ile persona üretimi başarısız oldu.");
    } finally {
      setGeneratingPersonas(false);
    }
  };

  const handleBulkAddPackage = async (packageName: string, packagePersonas: Array<any>) => {
    setAddingBulk(packageName);
    try {
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/personas/bulk-add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ personas: packagePersonas })
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      toast.success(`"${packageName}" paketinden ${data.saved_count || packagePersonas.length} persona havuza yüklendi.`);
      fetchAll();
    } catch {
      toast.error("Paket yüklemesi başarısız oldu.");
    } finally {
      setAddingBulk(null);
    }
  };

  const [deletingPersona, setDeletingPersona] = useState<string | null>(null);

  const handleDeletePersona = async (personaId: string) => {
    if (!confirm("Bu personayı silmek istediğinizden emin misiniz?")) {
      return;
    }
    setDeletingPersona(personaId);
    try {
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + `/api/admin/personas/${personaId}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Silme işlemi başarısız oldu.");
      }
      toast.success("Persona havuzdan silindi.");
      fetchAll();
    } catch (err: any) {
      toast.error(err.message || "Persona silinemedi.");
    } finally {
      setDeletingPersona(null);
    }
  };

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
      fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/config").then(r => r.json()),
      fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/clients").then(r => r.json()),
      fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/personas").then(r => r.json()),
      fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/audit_logs").then(r => r.json()),
      fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/questions").then(r => r.json()),
      fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/feedbacks").then(r => r.json()),
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
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/config", {
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
      const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/clients", {
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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"}/api/admin/clients/${username}`, {
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
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"}/api/admin/clients/${username}`, { method: "DELETE" });
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
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"}/api/admin/questions/${id}/like?is_liked=${!current}`, { method: "PUT" });
      setQuestions(prev => prev.map(q => q.id === id ? { ...q, is_liked: !current } : q));
      toast.success("Beğeni güncellendi.");
    } catch {
      toast.error("İşlem başarısız.");
    }
  };

  const savePurpose = async (id: number) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"}/api/admin/questions/${id}/purpose?purpose=${encodeURIComponent(editPurpose)}`, { method: "PUT" });
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
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"}/api/admin/questions/${id}`, { method: "DELETE" });
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
              <p className="text-sm text-muted-foreground">Sistem, Model ve Limit Yönetimi</p>
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
            <TabsTrigger value="schemas" className="justify-start px-4 py-2.5 w-full" onClick={() => {
              if (!schemas) {
                setSchemasLoading(true);
                fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/schemas")
                  .then(r => r.json())
                  .then(d => { setSchemas(d); setBriefDefaults(d.brief_schema.defaults); setDraftQuestions(d.default_interview_questions); })
                  .catch(() => toast.error("Şemalar yüklenemedi."))
                  .finally(() => setSchemasLoading(false));
              }
            }}>
              <Code size={16} className="mr-3" />
              <span>Ajan Şablonları</span>
            </TabsTrigger>
            <TabsTrigger value="metrics" className="justify-start px-4 py-2.5 w-full" onClick={() => {
              if (!metrics && !metricsLoading) {
                setMetricsLoading(true);
                fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/metrics")
                  .then(r => r.json())
                  .then(d => setMetrics(d))
                  .catch(() => toast.error("Metrikler yüklenemedi."))
                  .finally(() => setMetricsLoading(false));
              }
            }}>
              <BarChart3 size={16} className="mr-3" />
              <span>Metrikler</span>
            </TabsTrigger>
          </TabsList>
          
          <div className="flex-1 w-full min-w-0">

          {/* ══════════════ TAB: CLIENTS ══════════════ */}
          <TabsContent value="clients" className="mt-6 space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold">Danışan Yönetimi</h2>
                <p className="text-sm text-muted-foreground">Sisteme kayıtlı kurumsal müşteriler ve simülasyon limitleri.</p>
              </div>
              <Button onClick={() => setShowClientForm(!showClientForm)} className="gap-2 bg-[#17171c] text-white hover:opacity-85">
                <Plus size={16} />
                Yeni Danışan
              </Button>
            </div>

            {/* Add Client Form */}
            {showClientForm && (
              <Card className="border-[#d9d9dd]  bg-[#edfce9]/30  animate-in fade-in slide-in-from-top-2 duration-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base text-[#003c33] ">Yeni Danışan Ekle</CardTitle>
                </CardHeader>
                <CardContent>
                  {/* Plan Template Quick-Select */}
                  <div className="mb-4 p-3 bg-white  border border-border rounded-lg space-y-2">
                    <Label className="text-xs font-bold text-muted-foreground uppercase">Plan Şablonu Seç (Limitler Otomatik Dolar)</Label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(PLAN_TEMPLATES).map(([name, tpl]) => (
                        <button
                          key={name}
                          type="button"
                          onClick={() => applyTemplate(name)}
                          className={`flex flex-col items-start px-3 py-2 rounded-lg border-2 transition-all text-left ${clientForm.plan_type === name
                              ? "border-[#17171c] bg-[#edfce9] "
                              : "border-border hover:border-[#17171c] dark:hover:border-[#17171c]"
                            }`}
                        >
                          <span className={`font-bold text-sm ${clientForm.plan_type === name ? "text-[#003c33] " : ""}`}>{name}</span>
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
                    <Button onClick={createClient} disabled={savingClient || !clientForm.username} className="gap-2 bg-[#17171c] text-white hover:opacity-85">
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
                              ? <Badge className="bg-[#003c33] hover:bg-[#003c33]/85 text-white text-xs">Aktif</Badge>
                              : <Badge variant="secondary" className="text-xs">{cli.status}</Badge>}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1.5 justify-end">
                              {editingClient === cli.username ? (
                                <>
                                  <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-emerald-600 hover:text-[#003c33]" onClick={() => updateClient(cli.username)}>
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
                      <Badge className={config.pii_active === "true" ? "bg-[#003c33] hover:bg-[#003c33]/85 text-white" : "bg-[#eeece7] text-[#212121]"}>
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
              <CardContent className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[
                  { key: "wizard_prompt", label: "Araştırma Sihirbazı Promptu (Defne)" },
                  { key: "persona_interview_prompt", label: "Persona Mülakat Promptu" },
                  { key: "synthesis_prompt", label: "Sentez Raporu Promptu" },
                ].map(({ key, label }) => (
                  <div key={key} className="flex flex-col space-y-2 border border-border/50 rounded-lg p-4 bg-muted/20">
                    <Label className="font-semibold">{label}</Label>
                    <Textarea
                      id={`prompt-${key}`}
                      defaultValue={(config as Record<string, string>)[key] || ""}
                      rows={8}
                      className="text-sm font-mono bg-[#f5f4f1] flex-1 resize-none"
                    />
                    <div className="flex justify-end pt-2">
                      <Button
                        size="sm"
                        disabled={savingConfig === key}
                        onClick={() => {
                          const el = document.getElementById(`prompt-${key}`) as HTMLTextAreaElement;
                          if (el) saveConfig(key, el.value);
                        }}
                        className="gap-2 bg-[#ff7759] text-[#edfce9] hover:bg-[#ff7759]/90 w-full"
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
          <TabsContent value="personas" className="mt-6 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Left Column: Generator & Packages */}
              <div className="lg:col-span-1 space-y-6">
                
                {/* Compact Persona Creation & Ekleme Panel */}
                <Card className="border-[#d9d9dd] shadow-sm">
                  <Tabs defaultValue="ai" className="w-full">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-bold flex items-center gap-2">
                          <Plus size={15} className="text-[#003c33]" />
                          Persona Paneli
                        </CardTitle>
                        <TabsList className="bg-muted p-0.5 h-8 rounded-lg">
                          <TabsTrigger value="ai" className="text-[10px] px-2.5 py-1">AI ile Üret</TabsTrigger>
                          <TabsTrigger value="packages" className="text-[10px] px-2.5 py-1">Hazır Paketler</TabsTrigger>
                        </TabsList>
                      </div>
                      <CardDescription className="text-[11px] mt-1">
                        Havuza yapay zeka ile veya hazır şablonlarla toplu persona ekleyin.
                      </CardDescription>
                    </CardHeader>
                    
                    <CardContent className="pt-2">
                      
                      {/* AI Generator Tab */}
                      <TabsContent value="ai" className="space-y-3 mt-0">
                        <div className="space-y-1">
                          <Label className="text-[10px] font-bold text-muted-foreground uppercase">Rol Başlığı / Segment</Label>
                          <Input
                            value={genForm.role_title}
                            onChange={e => setGenForm(f => ({ ...f, role_title: e.target.value }))}
                            placeholder="Örn: Ev Hanımı, Yazılımcı, Emekli"
                            className="h-8 text-xs"
                          />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label className="text-[10px] font-bold text-muted-foreground uppercase">Kategori</Label>
                            <Input
                              value={genForm.category}
                              onChange={e => setGenForm(f => ({ ...f, category: e.target.value }))}
                              placeholder="Örn: E-ticaret, Bankacılık"
                              className="h-8 text-xs"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px] font-bold text-muted-foreground uppercase">Hedef Tüketici Tanımı</Label>
                            <Input
                              value={genForm.target_users}
                              onChange={e => setGenForm(f => ({ ...f, target_users: e.target.value }))}
                              placeholder="Örn: genel tüketici"
                              className="h-8 text-xs"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-1">
                            <Label className="text-[10px] font-bold text-muted-foreground uppercase">Miktar (1-10)</Label>
                            <select
                              value={genForm.count}
                              onChange={e => setGenForm(f => ({ ...f, count: +e.target.value }))}
                              className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background cursor-pointer focus:ring-1 focus:ring-primary"
                            >
                              {[1, 2, 3, 5, 10].map(n => (
                                <option key={n} value={n}>{n} Persona</option>
                              ))}
                            </select>
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[10px] font-bold text-muted-foreground uppercase">Hedef Pazar</Label>
                            <Input
                              value={genForm.market}
                              onChange={e => setGenForm(f => ({ ...f, market: e.target.value }))}
                              className="h-8 text-xs"
                            />
                          </div>
                        </div>

                        <Button
                          onClick={handleGeneratePersonas}
                          disabled={generatingPersonas || !genForm.role_title}
                          className="w-full gap-1.5 bg-[#17171c] hover:opacity-85 text-white h-8 text-xs font-semibold mt-2"
                        >
                          {generatingPersonas ? (
                            <>
                              <Loader2 size={12} className="animate-spin" />
                              Üretiliyor...
                            </>
                          ) : (
                            <>
                              <Zap size={12} className="text-amber-400 fill-amber-400" />
                              Toplu Persona Üret
                            </>
                          )}
                        </Button>
                      </TabsContent>

                      {/* Ready Packages Tab */}
                      <TabsContent value="packages" className="space-y-2 mt-0">
                        {PREDEFINED_PACKAGES.map(pkg => (
                          <div key={pkg.name} className="p-2 border border-border rounded-lg bg-muted/10 flex items-center justify-between gap-3 text-left">
                            <div className="min-w-0 flex-1">
                              <h4 className="font-bold text-[11px] text-primary truncate">{pkg.name}</h4>
                              <p className="text-[9px] text-muted-foreground truncate max-w-[160px]">{pkg.description}</p>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <Badge variant="outline" className="text-[9px] font-semibold bg-[#edfce9] text-[#003c33] border-[#d9d9dd] py-0.5 px-1.5">{pkg.personas.length} P</Badge>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={addingBulk !== null}
                                onClick={() => handleBulkAddPackage(pkg.name, pkg.personas)}
                                className="h-7 text-[10px] font-semibold px-2 hover:bg-slate-100"
                              >
                                {addingBulk === pkg.name ? (
                                  <Loader2 size={10} className="animate-spin" />
                                ) : (
                                  <Plus size={10} />
                                )}
                              </Button>
                            </div>
                          </div>
                        ))}
                      </TabsContent>
                      
                    </CardContent>
                  </Tabs>
                </Card>

              </div>

              {/* Right Column: Persona Pool List */}
              <div className="lg:col-span-2">
                <Card className="border-[#d9d9dd] shadow-sm h-full">
                  <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <CardTitle className="text-base">Sentetik Tüketici Havuzu <span className="text-muted-foreground font-normal text-sm">({personas.length} persona)</span></CardTitle>
                      <CardDescription className="text-xs">Global ve müşteri özel durumlar için sisteme yüklenmiş tüm sentetik kullanıcılar.</CardDescription>
                    </div>
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
                            <TableHead className="text-right">Aksiyonlar</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {personas.map(p => (
                            <TableRow key={p.id} className="hover:bg-muted/30 transition-colors">
                              <TableCell className="font-medium text-sm">{p.name}, {p.age}</TableCell>
                              <TableCell className="text-muted-foreground text-xs">{p.city}</TableCell>
                              <TableCell className="text-xs font-semibold">{p.role_title || p.segment}</TableCell>
                              <TableCell>
                                {p.ses_group ? (
                                  <Badge variant="outline" className={
                                    p.ses_group === "AB" ? "border-amber-300 text-amber-700 bg-amber-50/50" :
                                      p.ses_group === "C1" ? "border-[#1863dc]/30 text-[#1863dc] bg-blue-50/50" :
                                        p.ses_group === "C2" ? "border-[#d9d9dd] text-[#616161] bg-slate-50/50" :
                                          "border-rose-300 text-rose-700 bg-rose-50/50"
                                  }>{p.ses_group}</Badge>
                                ) : <span className="text-muted-foreground text-xs">—</span>}
                              </TableCell>
                              <TableCell>
                                <Badge variant="secondary" className="text-[10px] font-semibold bg-slate-100 text-slate-800">
                                  {({
                                    potential_customer: "Potansiyel",
                                    competitor_user: "Rakip Kullanıcı",
                                    churned_user: "Kaybedilmiş",
                                    decision_maker: "Karar Verici",
                                    individual_user: "Bireysel",
                                  } as Record<string, string>)[p.respondent_type ?? ""] ?? "—"}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                {p.is_global ? <Badge variant="secondary" className="text-[10px]">Global</Badge> : <Badge variant="outline" className="text-[10px] border-[#d9d9dd] text-[#003c33] bg-[#edfce9]/50">Özel</Badge>}
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-1.5">
                                  {/* Articos-like Detay Gör Dialog */}
                                  <Dialog>
                                    <DialogTrigger render={<Button variant="ghost" size="icon-sm" className="hover:bg-slate-100 dark:hover:bg-slate-800" />} title="Detayları Gör">
                                      <Eye className="w-4 h-4 text-slate-500" />
                                    </DialogTrigger>
                                    <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
                                      <DialogHeader className="pb-3 border-b border-border">
                                        <div className="flex flex-wrap items-center gap-2">
                                          <DialogTitle className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                            {p.name}, {p.age}
                                          </DialogTitle>
                                          {p.is_global ? (
                                            <Badge variant="secondary" className="text-[10px]">Global</Badge>
                                          ) : (
                                            <Badge variant="outline" className="text-[10px] border-[#d9d9dd] text-[#003c33] bg-[#edfce9]/50">Özel</Badge>
                                          )}
                                        </div>
                                        <DialogDescription className="text-xs text-muted-foreground mt-1">
                                          {p.city} • {p.role_title || p.segment}
                                        </DialogDescription>
                                      </DialogHeader>

                                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                                        {/* Sol Sütun: Demografi, Bio ve Nüanslar */}
                                        <div className="space-y-4 text-left">
                                          <div>
                                            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Biyografi & Yaşam Konsepti</h4>
                                            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-900 rounded-xl p-3 border border-border/40">
                                              {p.bio || "Bu persona için henüz biyografi hikayesi eklenmemiş."}
                                            </p>
                                          </div>

                                          <div className="grid grid-cols-2 gap-3">
                                            <div className="p-3 border border-border/50 rounded-xl bg-card">
                                              <span className="text-[10px] text-muted-foreground block mb-0.5">Sosyoeonomik Statü (SES)</span>
                                              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{p.ses_group || "C1"}</span>
                                            </div>
                                            <div className="p-3 border border-border/50 rounded-xl bg-card">
                                              <span className="text-[10px] text-muted-foreground block mb-0.5">Rogers İnovasyon Arketipi</span>
                                              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                                                {({
                                                  Innovator: "Yenilikçi (Innovator)",
                                                  EarlyAdopter: "Erken Benimseyen",
                                                  Mainstream: "Çoğunluk (Mainstream)",
                                                  Laggard: "Gelenekçi (Laggard)",
                                                  Skeptic: "Şüpheci (Skeptic)",
                                                } as Record<string, string>)[p.stance ?? ""] ?? p.stance ?? "Belirsiz"}
                                              </span>
                                            </div>
                                            <div className="p-3 border border-border/50 rounded-xl bg-card">
                                              <span className="text-[10px] text-muted-foreground block mb-0.5">Yerleşim Tipi</span>
                                              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                                                {({ kentsel: "Kentsel (Metropol)", kirsal: "Kırsal (Taşra)" } as Record<string, string>)[p.settlement_type ?? ""] ?? "Kentsel"}
                                              </span>
                                            </div>
                                            <div className="p-3 border border-border/50 rounded-xl bg-card">
                                              <span className="text-[10px] text-muted-foreground block mb-0.5">Katılımcı Tipi</span>
                                              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                                                {({
                                                  potential_customer: "Potansiyel",
                                                  competitor_user: "Rakip Kullanıcı",
                                                  churned_user: "Kaybedilmiş",
                                                  decision_maker: "Karar Verici",
                                                  individual_user: "Bireysel",
                                                } as Record<string, string>)[p.respondent_type ?? ""] ?? "Standart"}
                                              </span>
                                            </div>
                                          </div>

                                          <div className="space-y-2 border border-border/50 rounded-xl p-3 bg-muted/10">
                                            <h4 className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Tüketici Davranış Endeksleri</h4>
                                            <div className="space-y-1.5 text-xs">
                                              <div className="flex justify-between items-center">
                                                <span className="text-slate-600 dark:text-slate-400">Fiyat Hassasiyeti</span>
                                                <span className="font-semibold text-slate-800 dark:text-slate-200">{(p.price_sensitivity ?? 3)} / 5</span>
                                              </div>
                                              <div className="flex justify-between items-center">
                                                <span className="text-slate-600 dark:text-slate-400">Dijital Güven & Yetkinlik</span>
                                                <span className="font-semibold text-slate-800 dark:text-slate-200">{(p.digital_confidence ?? 3)} / 5</span>
                                              </div>
                                            </div>
                                          </div>
                                        </div>

                                        {/* Sağ Sütun: OCEAN Psikometrisi, Hedefler ve İtirazlar */}
                                        <div className="space-y-4 text-left">
                                          <div>
                                            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Beş Büyük Kişilik Özelliği (OCEAN)</h4>
                                            <div className="space-y-2 bg-slate-50 dark:bg-slate-900 border border-border/40 p-3 rounded-xl">
                                              {(() => {
                                                const ocean = getBigFive(p);
                                                return [
                                                  { name: "Openness (Deneyime Açıklık)", val: ocean.openness, color: "bg-blue-500" },
                                                  { name: "Conscientiousness (Sorumluluk)", val: ocean.conscientiousness, color: "bg-emerald-500" },
                                                  { name: "Extroversion (Dışadönüklük)", val: ocean.extroversion, color: "bg-amber-500" },
                                                  { name: "Agreeableness (Geçimlilik)", val: ocean.agreeableness, color: "bg-rose-500" },
                                                  { name: "Neuroticism (Duygusal Dengesizlik)", val: ocean.neuroticism, color: "bg-red-500" },
                                                ].map(item => (
                                                  <div key={item.name} className="space-y-1">
                                                    <div className="flex justify-between text-[11px] font-medium text-slate-600 dark:text-slate-400">
                                                      <span>{item.name}</span>
                                                      <span>%{item.val}</span>
                                                    </div>
                                                    <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                                                      <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.val}%` }} />
                                                    </div>
                                                  </div>
                                                ));
                                              })()}
                                            </div>
                                          </div>

                                          <div>
                                            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Kullanıcı Hedefleri & Amaçları</h4>
                                            <div className="flex flex-wrap gap-1.5">
                                              {(() => {
                                                const goals = parseJsonField(p.goals, []);
                                                const goalList = Array.isArray(goals) ? goals : [];
                                                if (goalList.length === 0) return <span className="text-xs text-muted-foreground">Hedef belirtilmemiş.</span>;
                                                return goalList.map((g: string, idx: number) => (
                                                  <span key={idx} className="text-xs bg-emerald-50 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-300 border border-emerald-100 dark:border-emerald-900/40 rounded-lg px-2.5 py-1">
                                                    {g}
                                                  </span>
                                                ));
                                              })()}
                                            </div>
                                          </div>

                                          <div>
                                            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Satın Alma İtirazları & Kaygıları</h4>
                                            <div className="flex flex-wrap gap-1.5">
                                              {(() => {
                                                const objections = parseJsonField(p.objections, []);
                                                const objList = Array.isArray(objections) ? objections : [];
                                                if (objList.length === 0) return <span className="text-xs text-muted-foreground">İtiraz belirtilmemiş.</span>;
                                                return objList.map((obj: string, idx: number) => (
                                                  <span key={idx} className="text-xs bg-red-50 text-red-800 dark:bg-red-950/20 dark:text-red-300 border border-red-100 dark:border-red-900/40 rounded-lg px-2.5 py-1">
                                                    {obj}
                                                  </span>
                                                ));
                                              })()}
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    </DialogContent>
                                  </Dialog>

                                  {/* Persona Silme Aksiyonu (Lock Korumalı) */}
                                  {p.is_locked ? (
                                    <Button variant="ghost" size="icon-sm" disabled title="Bu persona bir araştırmaya katıldığı için silinemez (Kilitli)" className="text-slate-300 dark:text-slate-700 cursor-not-allowed">
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  ) : (
                                    <Button
                                      variant="ghost"
                                      size="icon-sm"
                                      onClick={() => handleDeletePersona(p.id)}
                                      title="Havuzdan Sil"
                                      disabled={deletingPersona === p.id}
                                      className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20"
                                    >
                                      {deletingPersona === p.id ? (
                                        <Loader2 className="w-4 h-4 animate-spin text-red-500" />
                                      ) : (
                                        <Trash2 className="w-4 h-4" />
                                      )}
                                    </Button>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                          {personas.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={7} className="text-center py-10 text-muted-foreground text-xs">
                                Havuzda kayıtlı persona bulunmuyor. AI veya hazır paketler ile ekleyin.
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              </div>

            </div>
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
                      <div key={q.id} className="p-4 border border-border rounded-xl hover:border-[#d9d9dd]  transition-colors space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <p className="text-sm text-[#212121]  font-medium leading-relaxed flex-1">{q.question}</p>
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
                          {q.research_title && <span>&quot;{q.research_title}&quot;</span>}
                          {!q.is_liked && <Badge variant="secondary" className="text-[10px] text-[#93939f]">Pasif (simülasyonda kullanılmıyor)</Badge>}
                        </div>

                        {editingQuestion === q.id && (
                          <div className="flex gap-2 mt-2 animate-in fade-in slide-in-from-top-1 duration-200">
                            <Input
                              value={editPurpose}
                              onChange={e => setEditPurpose(e.target.value)}
                              placeholder="Bu sorunun amacı / bağlamı..."
                              className="text-xs h-8 flex-1"
                            />
                            <Button size="sm" className="h-8 gap-1.5 text-xs bg-[#17171c] text-white hover:opacity-85" onClick={() => savePurpose(q.id)}>
                              <Check size={13} />
                              Kaydet
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8" onClick={() => setEditingQuestion(null)}>
                              <X size={13} />
                            </Button>
                          </div>
                        )}
                        {q.purpose_context && editingQuestion !== q.id && (
                          <p className="text-xs text-[#ff7759] /80 italic">Amaç: {q.purpose_context}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ══════════════ TAB: FEEDBACKS ══════════════ */}
          <TabsContent value="feedbacks" className="mt-6 space-y-6">

            {/* ── Aggregate Özet Kartları ── */}
            {(() => {
              const total = feedbacks.length;
              const likes = feedbacks.filter(f => f.vote === 1).length;
              const dislikes = feedbacks.filter(f => f.vote === -1).length;
              const withComment = feedbacks.filter(f => f.comment && f.comment.trim().length > 0).length;
              const likeRate = total > 0 ? Math.round((likes / total) * 100) : 0;
              const commentRate = total > 0 ? Math.round((withComment / total) * 100) : 0;

              // En çok değerlendirilen item_type
              const typeCounts: Record<string, number> = {};
              feedbacks.forEach(f => {
                const t = f.item_type || "genel";
                typeCounts[t] = (typeCounts[t] || 0) + 1;
              });
              const topType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";

              return (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Toplam */}
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

                  {/* Beğeni Oranı */}
                  <Card className={`border-l-4 shadow-sm ${likeRate >= 70 ? "border-l-emerald-500" : likeRate >= 40 ? "border-l-amber-500" : "border-l-red-500"}`}>
                    <CardContent className="pt-5 pb-4">
                      <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">Beğeni Oranı</p>
                      <p className={`text-4xl font-black mt-1 ${likeRate >= 70 ? "text-emerald-600 dark:text-emerald-400" : likeRate >= 40 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400"}`}>
                        %{likeRate}
                      </p>
                      {/* Mini bar */}
                      <div className="mt-2 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${likeRate >= 70 ? "bg-emerald-500" : likeRate >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                          style={{ width: `${likeRate}%` }}
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Yorum Oranı */}
                  <Card className="border-l-4 border-l-sky-400 shadow-sm">
                    <CardContent className="pt-5 pb-4">
                      <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">Yorum İçeren</p>
                      <p className="text-4xl font-black text-sky-600 dark:text-sky-400 mt-1">%{commentRate}</p>
                      <p className="text-xs text-muted-foreground mt-1">{withComment} kayıtta yorum var</p>
                    </CardContent>
                  </Card>

                  {/* En Çok Değerlendirilen Tür */}
                  <Card className="border-l-4 border-l-indigo-400 shadow-sm">
                    <CardContent className="pt-5 pb-4">
                      <p className="text-[11px] font-bold uppercase text-muted-foreground tracking-wide">En Çok Değerlendirilen</p>
                      <p className="text-lg font-black text-[#1863dc] dark:text-[#4c6ee6] mt-1 truncate">{topType}</p>
                      <p className="text-xs text-muted-foreground mt-1">{typeCounts[topType] ?? 0} kayıt</p>
                    </CardContent>
                  </Card>
                </div>
              );
            })()}

            {/* ── Detay Tablo + Filtreler ── */}
            <FeedbackTable feedbacks={feedbacks} />
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
                <Card className="border-[#d9d9dd]  bg-[#edfce9]/20 ">
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
                      badgeColor: "border-[#d9d9dd] text-[#003c33]  ",
                      rows: (schemas.brief_schema?.fields ?? []).map(f => [
                        f.key, f.type, f.required ? "Zorunlu" : "Opsiyonel", f.desc,
                      ]),
                      headers: ["Alan", "Tip", "Durum", "Açıklama"],
                    },
                    {
                      title: "Persona Şeması",
                      desc: schemas.persona_schema?.description ?? "",
                      badge: "workflow.py → LLM",
                      badgeColor: "border-[#003c33]/30 text-[#003c33] dark:border-emerald-800 ",
                      rows: (schemas.persona_schema?.fields ?? []).map(f => ([f.key, f.type, "", f.desc])),
                      headers: ["Alan", "Tip", "", "Açıklama"],
                    },
                    {
                      title: "Mülakat Turu Çıktısı",
                      desc: schemas.interview_schema?.description ?? "",
                      badge: "interview turn → LLM",
                      badgeColor: "border-amber-200 text-amber-700 dark:border-amber-800 ",
                      rows: Object.entries(schemas.interview_schema?.output ?? {}).map(([k, v]) => ([k, "", "", v])),
                      headers: ["Alan", "", "", "Açıklama"],
                    },
                    {
                      title: "Sentez Raporu Çıktısı",
                      desc: schemas.synthesis_schema?.description ?? "",
                      badge: "analytics.py",
                      badgeColor: "border-rose-200 text-rose-700 dark:border-rose-800 ",
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
                                    <td key={ci} className={`py-1.5 px-3 ${ci === 0 ? "font-mono font-bold text-[#003c33] " : "text-muted-foreground"
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
                        <Badge key={v} variant="outline" className="text-[10px] font-mono bg-[#f5f4f1] ">{v}</Badge>
                      ))}

                    </div>
                  </CardContent>
                </Card>

                {/* ── Brief Defaults Editor ── */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold">Brief Varsayılan Değerleri</CardTitle>
                    <CardDescription>Yeni araştırma oluşturulduğunda Defne&apos;ye iletilecek varsayılan brief değerleri.</CardDescription>
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
                                  await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/schemas/brief-defaults", {
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
                        <CardDescription className="mt-0.5">workflow.py DEFAULT_QUESTIONS — system_config&apos;den override edilebilir.</CardDescription>
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
                            className="gap-1.5 bg-[#17171c] hover:bg-[#17171c] text-white"
                            disabled={savingDefaults}
                            onClick={async () => {
                              setSavingDefaults(true);
                              try {
                                await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000") + "/api/admin/schemas/interview-questions", {
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
                            <span className="text-[#212121] ">{q}</span>
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
                    <CardDescription>intake.py → CONCEPT_POOLS — Defne&apos;nin ürün tipine göre seçtiği soru &amp; rol havuzları.</CardDescription>
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
                              <p className="text-xs text-[#616161] leading-relaxed">{pool.focus_areas}</p>
                            </div>
                            <div>
                              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide mb-1.5">Soru Havuzu ({pool.questions.length})</div>
                              <ol className="space-y-1">
                                {pool.questions.map((q, qi) => (
                                  <li key={qi} className="flex gap-2 text-xs">
                                    <span className="font-mono text-muted-foreground shrink-0">{qi + 1}.</span>
                                    <span className="text-[#212121] ">{q}</span>
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

          {/* ══════════════ TAB: METRİKLER ══════════════ */}
          <TabsContent value="metrics" className="mt-6 space-y-6">
            <div>
              <h2 className="text-xl font-bold">Sistem Metrikleri</h2>
              <p className="text-sm text-muted-foreground">Token kullanımı, model durumu ve araştırma istatistikleri.</p>
            </div>

            {metricsLoading && (
              <div className="flex items-center gap-3 py-16 justify-center text-muted-foreground">
                <Loader2 size={22} className="animate-spin text-[#ff7759]" />
                Metrikler yükleniyor...
              </div>
            )}

            {metrics && (
              <>
                {/* ── KPI Kartlar ── */}
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
                          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{kpi.label}</span>
                          {kpi.icon}
                        </div>
                        <div className="text-3xl font-bold text-[#17171c]">{kpi.value}</div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* ── Aktif Modeller ── */}
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
                        { label: "Orkestratör (Kızıgan e4b)", value: metrics.models.orchestrator, color: "text-[#ff7759]", bg: "bg-orange-50" },
                        { label: "Aktör (Trendyol-7B)", value: metrics.models.b2c, color: "text-[#003c33]", bg: "bg-[#edfce9]" },
                        { label: "Analist (Asure-12B)", value: metrics.models.b2b, color: "text-[#1863dc]", bg: "bg-[#f1f5ff]" },
                      ].map(m => (
                        <div key={m.label} className={`rounded-lg px-4 py-3 ${m.bg}`}>
                          <div className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground mb-0.5">{m.label}</div>
                          <div className={`font-mono text-sm font-semibold ${m.color}`}>{m.value}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* ── Token Kullanımı — Per User ── */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold">Danışan Token Kullanımı</CardTitle>
                    <CardDescription>Her danışanın plan limitine göre token doluluk oranı.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {metrics.clients.map(cli => {
                      const pct = cli.max_tokens > 0 ? Math.min(100, (cli.tokens_used / cli.max_tokens) * 100) : 0;
                      const isWarning = pct >= 70 && pct < 90;
                      const isDanger  = pct >= 90;
                      const barColor  = isDanger ? "bg-red-500" : isWarning ? "bg-amber-400" : "bg-[#003c33]";
                      const fmtToken  = (n: number) => n >= 1_000_000 ? `${(n/1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n/1_000).toFixed(0)}K` : String(n);

                      return (
                        <div key={cli.username} className="space-y-1.5">
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-[#17171c]">{cli.username}</span>
                              <Badge variant="outline" className="text-[10px] px-1.5 py-0">{cli.plan_type}</Badge>
                              {isDanger  && <Badge className="text-[10px] px-1.5 py-0 bg-red-100 text-red-700 border border-red-200">Limit Dolmak Üzere</Badge>}
                              {isWarning && <Badge className="text-[10px] px-1.5 py-0 bg-amber-50 text-amber-700 border border-amber-200">Uyarı</Badge>}
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
                              <th key={h} className="text-left py-2 px-4 text-[10px] font-bold uppercase text-muted-foreground">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {metrics.plan_distribution.map(row => (
                            <tr key={row.plan_type} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                              <td className="py-2 px-4 font-semibold text-[#17171c]">{row.plan_type}</td>
                              <td className="py-2 px-4 text-muted-foreground">{row.count}</td>
                              <td className="py-2 px-4 text-muted-foreground tabular-nums">
                                {row.total_tokens >= 1_000_000
                                  ? `${(row.total_tokens/1_000_000).toFixed(1)}M`
                                  : row.total_tokens >= 1_000
                                  ? `${(row.total_tokens/1_000).toFixed(0)}K`
                                  : row.total_tokens ?? 0}
                              </td>
                              <td className="py-2 px-4 text-muted-foreground">{row.total_sims ?? 0}</td>
                            </tr>
                          ))}
                          {metrics.plan_distribution.length === 0 && (
                            <tr><td colSpan={4} className="text-center py-6 text-muted-foreground text-sm">Veri yok.</td></tr>
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
                        { label: "Toplam Araştırma",  value: metrics.study_stats.total },
                        { label: "Raporu Olan",       value: metrics.study_stats.with_report },
                        { label: "Arşivlenen",        value: metrics.study_stats.archived },
                        { label: "Ort. Kalite Skoru", value: metrics.study_stats.avg_quality > 0 ? `${metrics.study_stats.avg_quality}/100` : "—" },
                        { label: "Denetim Hataları",  value: metrics.study_stats.error_count },
                      ].map(item => (
                        <div key={item.label} className="flex items-center justify-between py-1 border-b border-border/40 last:border-0">
                          <span className="text-sm text-muted-foreground">{item.label}</span>
                          <span className={`font-semibold text-sm ${item.label === "Denetim Hataları" && Number(item.value) > 0 ? "text-red-600" : "text-[#17171c]"}`}>
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
                              <span className="text-sm text-muted-foreground w-40 shrink-0 truncate">{cat.category}</span>
                              <div className="flex-1 h-2 rounded-full bg-[#eeece7] overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-[#1863dc]/70 transition-all duration-500"
                                  style={{ width: `${(cat.count / maxCount) * 100}%` }}
                                />
                              </div>
                              <span className="text-xs font-semibold text-muted-foreground w-6 text-right">{cat.count}</span>
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
    </div>
  );
}