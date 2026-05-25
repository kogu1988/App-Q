"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Download, 
  FileText, 
  Users, 
  MessageSquare, 
  TrendingUp, 
  Loader2, 
  Calendar, 
  Compass, 
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  Archive,
  ThumbsUp,
  ThumbsDown,
  ListTodo
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { PlanGate } from "@/components/plan-gate";
import { useClientPlan } from "@/hooks/use-client-plan";

// Interface definitions matching the backend Pydantic models
interface Persona {
  id: string;
  name: string;
  age: number;
  city: string;
  segment: string;
  stance: string;
  price_sensitivity: number;
  digital_confidence: number;
  context: string;
  goals: string[];
  objections: string[];
  bio: string;
  role_title?: string;
  ses_group?: string;
  respondent_type?: string;
  settlement_type?: string;
  big_five?: {
    openness: number;
    conscientiousness: number;
    extroversion: number;
    agreeableness: number;
    neuroticism: number;
  };
}

interface InterviewTurn {
  question: string;
  answer: string;
  tags?: string[];
}

interface PersonaInterview {
  persona: Persona;
  turns: InterviewTurn[];
  consistency_notes?: string[];
}

interface ResearchPlan {
  objective?: string;
  assumptions?: string[];
  interview_questions?: string[];
  recommended_panel_size?: number;
}

interface StudyDetail {
  metadata?: {
    id: string;
    title: string;
    market: string;
    category: string;
    created_at: string;
    updated_at: string;
    has_report: boolean;
    quality_score?: number;
    quality_grade?: string;
    quality_summary?: string;
  };
  brief?: {
    category: string;
    title: string;
    context: string;
    brand: string;
    budget: string;
  };
  plan?: ResearchPlan;
  personas?: Persona[];
  interviews?: PersonaInterview[];
  report_markdown?: string;
  report_html?: string;
  ses_cross_tab?: Array<{
    ses_group: string;
    total: number;
    dominant_stance: string;
    stance_counts: Record<string, number>;
  }>;
  respondent_type_summary?: Array<{
    respondent_type: string;
    label: string;
    count: number;
    avg_price_sensitivity: number;
    top_pain: string | null;
    top_objection: string | null;
  }>;
  van_westendorp?: {
    too_cheap_values: number[];
    cheap_values: number[];
    expensive_values: number[];
    too_expensive_values: number[];
    opp: number;
    ipp: number;
    pmc: number;
    pme: number;
    acceptable_range: [number, number];
    currency: string;
    methodology_note: string;
  };
  brand_health?: {
    unaided_recall: Record<string, number>;
    associations: Record<string, string[]>;
    top_of_mind: string | null;
    total_mentions: number;
  };
  channel_map?: Array<{ channel: string; count: number; pct: number }>;
  research_quality?: {
    // Eski format (backward compat)
    overall_score?: number;
    grade?: string;
    bias_flags?: Record<string, string[]>;
    straight_lining_count?: number;
    acquiescence_count?: number;
    social_desirability_count?: number;
    summary?: string;
    // Yeni adversarial review format (Grounded Simulation)
    flags?: Array<{ phase: string; severity: string; code: string; message: string; finding?: string; suggested_confidence?: number; suggested_step?: string }>;
    flag_count?: number;
    warning_count?: number;
    phases_passed?: string[];
    phases_flagged?: string[];
    // RFI
    rfi?: number;
    components?: Record<string, number>;
    valid?: boolean;
    validity_threshold?: number;
    interpretation?: string;
  };
}

// ──────────────── Channel Discovery Bar Chart ────────────────
function ChannelBarChart({ data }: { data: NonNullable<StudyDetail["channel_map"]> }) {
  if (!data.length) return null;
  const maxCount = Math.max(...data.map(d => d.count));
  const COLORS = ["#6366f1","#14b8a6","#0ea5e9","#22c55e","#f97316","#ec4899","#f59e0b"];
  return (
    <div className="space-y-2.5">
      {data.map((row, i) => (
        <div key={row.channel} className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-600 w-40 shrink-0 truncate">{row.channel}</span>
          <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${(row.count / maxCount) * 100}%`, backgroundColor: COLORS[i % COLORS.length] }}
            />
          </div>
          <span className="text-xs font-bold tabular-nums w-10 text-right" style={{ color: COLORS[i % COLORS.length] }}>
            %{row.pct}
          </span>
        </div>
      ))}
    </div>
  );
}

// ──────────────── Van Westendorp PSM Chart ────────────────
function PSMChart({ data }: { data: NonNullable<StudyDetail["van_westendorp"]> }) {
  const W = 600, H = 260, PAD = { left: 56, right: 24, top: 16, bottom: 40 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;

  // Tüm fiyat değerlerini birleştir ve X eksenini belirle
  const allVals = [
    ...data.too_cheap_values,
    ...data.cheap_values,
    ...data.expensive_values,
    ...data.too_expensive_values,
  ];
  const xMin = Math.min(...allVals) * 0.8;
  const xMax = Math.max(...allVals) * 1.15;

  const xScale = (v: number) => PAD.left + ((v - xMin) / (xMax - xMin)) * innerW;

  // Kümülatif dağılım (CDF) hesapla
  function buildCDF(values: number[]): Array<[number, number]> {
    if (!values.length) return [];
    const sorted = [...values].sort((a, b) => a - b);
    const pts: Array<[number, number]> = [];
    // Eksen genişliğinde eşit aralıklı örnek nokta
    const steps = 60;
    for (let i = 0; i <= steps; i++) {
      const x = xMin + (i / steps) * (xMax - xMin);
      const pct = sorted.filter(v => v <= x).length / sorted.length;
      pts.push([x, pct]);
    }
    return pts;
  }

  const cdfTooExpensive = buildCDF(data.too_expensive_values); // Azalan (1 - ...)
  const cdfCheap        = buildCDF(data.cheap_values);
  const cdfExpensive    = buildCDF(data.expensive_values);
  const cdfTooCheap     = buildCDF(data.too_cheap_values);     // Azalan

  function toPolyline(pts: Array<[number, number]>, invert = false): string {
    return pts
      .map(([x, y]) => `${xScale(x).toFixed(1)},${(PAD.top + innerH * (1 - (invert ? 1 - y : y))).toFixed(1)}`)
      .join(" ");
  }

  const yTicks = [0, 25, 50, 75, 100];
  const priceTicks = Array.from({ length: 6 }, (_, i) =>
    Math.round(xMin + (i / 5) * (xMax - xMin))
  );

  const LINES = [
    { pts: toPolyline(cdfTooCheap, true),     color: "#f59e0b", label: "Çok Ucuz",  dash: "4 2" },
    { pts: toPolyline(cdfCheap),               color: "#22c55e", label: "Makul",     dash: "" },
    { pts: toPolyline(cdfExpensive),            color: "#f97316", label: "Pahalı",   dash: "" },
    { pts: toPolyline(cdfTooExpensive, true),  color: "#ef4444", label: "Çok Pahalı", dash: "4 2" },
  ];

  const markers = [
    { x: data.pmc, label: "PMC", color: "#6366f1" },
    { x: data.opp, label: "OPP", color: "#0d9488" },
    { x: data.ipp, label: "IPP", color: "#0ea5e9" },
    { x: data.pme, label: "PME", color: "#ec4899" },
  ];

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-2xl" style={{ fontFamily: "inherit" }}>
        {/* Grid lines */}
        {yTicks.map(t => (
          <g key={t}>
            <line
              x1={PAD.left} y1={PAD.top + innerH * (1 - t / 100)}
              x2={PAD.left + innerW} y2={PAD.top + innerH * (1 - t / 100)}
              stroke="#e2e8f0" strokeWidth="1"
            />
            <text x={PAD.left - 6} y={PAD.top + innerH * (1 - t / 100) + 4} textAnchor="end"
              className="fill-slate-400" fontSize="10">{t}%</text>
          </g>
        ))}

        {/* X axis ticks */}
        {priceTicks.map(v => (
          <g key={v}>
            <line x1={xScale(v)} y1={PAD.top + innerH} x2={xScale(v)} y2={PAD.top + innerH + 4}
              stroke="#cbd5e1" strokeWidth="1" />
            <text x={xScale(v)} y={PAD.top + innerH + 16} textAnchor="middle"
              className="fill-slate-400" fontSize="10">{v.toLocaleString("tr-TR")} ₺</text>
          </g>
        ))}

        {/* Acceptable range band */}
        <rect
          x={xScale(data.pmc)} y={PAD.top}
          width={xScale(data.pme) - xScale(data.pmc)}
          height={innerH}
          fill="#6366f1" fillOpacity="0.06"
        />

        {/* PSM Curves */}
        {LINES.map(l => (
          <polyline key={l.label} points={l.pts}
            fill="none" stroke={l.color} strokeWidth="2"
            strokeDasharray={l.dash || undefined}
            strokeLinecap="round" strokeLinejoin="round" />
        ))}

        {/* Vertical markers */}
        {markers.map(m => (
          <g key={m.label}>
            <line x1={xScale(m.x)} y1={PAD.top} x2={xScale(m.x)} y2={PAD.top + innerH}
              stroke={m.color} strokeWidth="1.5" strokeDasharray="3 3" />
            <rect x={xScale(m.x) - 14} y={PAD.top} width={28} height={16} rx="3"
              fill={m.color} fillOpacity="0.9" />
            <text x={xScale(m.x)} y={PAD.top + 11} textAnchor="middle"
              fill="white" fontSize="9" fontWeight="bold">{m.label}</text>
          </g>
        ))}

        {/* Axes */}
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + innerH}
          stroke="#94a3b8" strokeWidth="1" />
        <line x1={PAD.left} y1={PAD.top + innerH} x2={PAD.left + innerW} y2={PAD.top + innerH}
          stroke="#94a3b8" strokeWidth="1" />
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-2 text-xs">
        {LINES.map(l => (
          <div key={l.label} className="flex items-center gap-1.5">
            <svg width="24" height="10">
              <line x1="0" y1="5" x2="24" y2="5" stroke={l.color} strokeWidth="2"
                strokeDasharray={l.dash || undefined} />
            </svg>
            <span className="text-slate-600 ">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function StudyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const studyId = params.id as string;

  const [study, setStudy] = useState<StudyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"summary" | "personas" | "interviews" | "report">("summary");
  const [selectedPersonaIdx, setSelectedPersonaIdx] = useState<number>(0);
  const [archiving, setArchiving] = useState(false);
  const [isArchived, setIsArchived] = useState(false);
  // Map of turn votes: { "personaIdx-turnIdx": { vote: 1|-1, comment?: string } }
  const [votes, setVotes] = useState<Record<string, { vote: number; comment: string }>>({});
  // Track which turn has the comment box open
  const [pendingComment, setPendingComment] = useState<{ key: string; vote: number; text: string } | null>(null);
  const [followUpText, setFollowUpText] = useState("");
  const [sendingFollowUp, setSendingFollowUp] = useState(false);
  const { plan: clientPlan } = useClientPlan();

  useEffect(() => {
    if (!studyId) return;

    const fetchStudy = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/client/studies/${studyId}`);
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error("Araştırma bulunamadı.");
          }
          throw new Error("Veriler yüklenirken bir hata oluştu.");
        }
        const data = await res.json();
        setStudy(data);
        
        // Default to report tab if it's already generated and completed
        if (data.metadata?.has_report) {
          setActiveTab("report");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Bir hata oluştu.");
      } finally {
        setLoading(false);
      }
    };

    fetchStudy();
  }, [studyId]);

  const handleArchive = async () => {
    if (!confirm("Bu araştırmayı arşivlemek istediğinize emin misiniz? Arşivlenen araştırmalar listede görünmez.")) return;
    setArchiving(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/client/studies/${studyId}/archive`, { method: "PUT" });
      if (!res.ok) throw new Error();
      setIsArchived(true);
      toast.success("Araştırma arşivlendi.");
    } catch {
      toast.error("Arşivleme başarısız.");
    } finally {
      setArchiving(false);
    }
  };

  const handleFeedback = (personaIdx: number, turnIdx: number, vote: number) => {
    const key = `${personaIdx}-${turnIdx}`;
    if (votes[key]?.vote === vote) return; // already voted same
    // Open inline comment box
    setPendingComment({ key, vote, text: "" });
  };

  const submitFeedback = async (key: string, vote: number, comment: string) => {
    const [pIdx, tIdx] = key.split("-").map(Number);
    const personaName = study?.interviews?.[pIdx]?.persona?.name || "unknown";
    try {
      await fetch((process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/client/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "anonymous",
          study_id: studyId,
          item_type: "interview_turn",
          item_id: `${personaName}-turn-${tIdx}`,
          vote,
          comment: comment.trim()
        })
      });
      setVotes(prev => ({ ...prev, [key]: { vote, comment: comment.trim() } }));
      setPendingComment(null);
      toast.success(vote === 1 ? "Olumlu oy verildi." : "Olumsuz oy verildi.");
    } catch {
      toast.error("Oy gönderilemedi.");
    }
  };

  const handleFollowUp = async (personaId: string) => {
    if (!followUpText.trim()) return;
    setSendingFollowUp(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/client/studies/${studyId}/follow-up`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ persona_id: personaId, question: followUpText })
      });
      if (!res.ok) throw new Error("API hatası");
      const data = await res.json();
      
      // Update local state to show the new turn immediately
      setStudy(prev => {
        if (!prev) return prev;
        const newInterviews = [...(prev.interviews || [])];
        const idx = newInterviews.findIndex(i => i.persona.id === personaId);
        if (idx !== -1) {
          newInterviews[idx].turns.push(data.turn);
        }
        return { ...prev, interviews: newInterviews };
      });
      
      setFollowUpText("");
      toast.success("Soru soruldu!");
    } catch (err) {
      toast.error("Soru sorulurken bir hata oluştu.");
    } finally {
      setSendingFollowUp(false);
    }
  };

  // Premium Markdown Parser to render synthesis report elegantly without dependencies
  const renderMarkdown = (mdText?: string) => {
    if (!mdText) return <p className="text-muted-foreground">Rapor içeriği bulunmamaktadır.</p>;

    const lines = mdText.split("\n");
    return lines.map((line, idx) => {
      // Headers
      if (line.startsWith("### ")) {
        return <h4 key={idx} className="text-lg font-semibold text-slate-800 dark:text-slate-100 mt-5 mb-2">{line.replace("### ", "")}</h4>;
      }
      if (line.startsWith("## ")) {
        return <h3 key={idx} className="text-xl font-bold text-slate-800 dark:text-slate-100 mt-6 mb-3 border-b pb-1 border-slate-200 dark:border-slate-800">{line.replace("## ", "")}</h3>;
      }
      if (line.startsWith("# ")) {
        return <h2 key={idx} className="text-2xl font-black text-slate-900 dark:text-white mt-8 mb-4">{line.replace("# ", "")}</h2>;
      }

      // Bullet points
      if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
        const cleanText = line.trim().replace(/^[-*]\s+/, "");
        // Highlight bold elements inside bullet points
        return (
          <li key={idx} className="list-disc pl-2 ml-5 text-slate-600 leading-relaxed my-1">
            {parseBoldText(cleanText)}
          </li>
        );
      }

      // Blockquotes / Warnings
      if (line.startsWith("> ")) {
        return (
          <div key={idx} className="border-l-4 border-[#1863dc] pl-4 py-2 bg-[#f1f5ff]/40 dark:bg-[#071829]/20 rounded-r-md text-slate-700 italic my-4">
            {line.replace("> ", "")}
          </div>
        );
      }

      // Paragraph
      if (line.trim() === "") return <div key={idx} className="h-2" />;

      return (
        <p key={idx} className="text-slate-600 leading-relaxed my-3">
          {parseBoldText(line)}
        </p>
      );
    });
  };

  // Helper to parse bold markdown syntax (**text**) within a paragraph
  const parseBoldText = (text: string) => {
    const parts = text.split(/\*\*([^*]+)\*\*/g);
    return parts.map((part, index) => {
      // Every odd element is bold
      if (index % 2 === 1) {
        return <strong key={index} className="font-semibold text-slate-900 dark:text-slate-100">{part}</strong>;
      }
      return part;
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="h-10 w-10 animate-spin text-[#1863dc]" />
        <p className="text-muted-foreground text-sm font-medium">Veriler yükleniyor, lütfen bekleyin...</p>
      </div>
    );
  }

  if (error || !study) {
    return (
      <div className="max-w-md mx-auto my-16 text-center space-y-6">
        <div className="inline-flex p-3 bg-red-100 dark:bg-red-950/30 text-red-600 rounded-full">
          <AlertCircle size={40} />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight">Veri Yüklenemedi</h2>
          <p className="text-muted-foreground text-sm">{error || "Geçersiz araştırma kaydı."}</p>
        </div>
        <Button onClick={() => router.push("/client")} className="w-full">
          Dashboard&apos;a Dön
        </Button>
      </div>
    );
  }

  const { metadata, brief, plan, personas = [], interviews = [] } = study;
  const isCompleted = metadata?.has_report ?? false;

  return (
    <div className="p-4 sm:p-8 space-y-6 sm:space-y-8 animate-in fade-in duration-300">
      
      {/* 🚀 Header & Navigation */}
      <div className="flex flex-col gap-4">
        <Link href="/client" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors w-fit">
          <ArrowLeft size={16} />
          Panel Geçmişine Dön
        </Link>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-border pb-6">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="bg-slate-100 text-slate-600 text-xs font-semibold">
                {metadata?.category || "Genel"}
              </Badge>
              {isCompleted ? (
                <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1 text-xs">
                  <CheckCircle2 size={12} />
                  Tamamlandı
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">Taslak</Badge>
              )}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              {metadata?.title || "İsimsiz Simülasyon"}
            </h1>
            <p className="text-muted-foreground text-sm flex items-center gap-1.5">
              <Calendar size={14} />
              Son Güncelleme: {metadata?.updated_at ? new Date(metadata.updated_at).toLocaleDateString("tr-TR") : "-"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {isCompleted && (
              <Button 
                className="w-full sm:w-auto btn-pill-primary gap-2"
                onClick={async () => {
                  const username = localStorage.getItem("appq_username");
                  try {
                    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/client/studies/${studyId}/pdf`, {
                      headers: username ? { "X-Username": username } : {}
                    });
                    if (!res.ok) {
                      const errData = await res.json().catch(() => ({}));
                      if (errData?.detail?.code === "PLAN_GATE" || errData?.detail?.includes("plan")) {
                        toast.error(
                          <div className="flex flex-col gap-1.5">
                            <span className="font-semibold text-[13px]">Bu özellik üst paket gerektirir.</span>
                            <span className="text-xs opacity-90">{errData?.detail?.message || "PDF çıktısı almak için planınızı yükseltmelisiniz."}</span>
                            <Link href="/client/upgrade" className="text-xs underline font-bold mt-1">Hemen Yükselt</Link>
                          </div>
                        );
                        return;
                      }
                      throw new Error(errData?.detail || "Rapor indirilemedi.");
                    }
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `AppQ-Rapor-${studyId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                  } catch (e) {
                    toast.error("İndirme işlemi başarısız oldu.");
                  }
                }}
              >
                <Download size={16} />
                PDF Raporu İndir
              </Button>
            )}
            {!isArchived ? (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleArchive}
                disabled={archiving}
                className="gap-2 text-slate-600 border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                {archiving ? <Loader2 size={14} className="animate-spin" /> : <Archive size={14} />}
                Arşivle
              </Button>
            ) : (
              <Badge variant="secondary" className="text-xs gap-1">
                <Archive size={12} />
                Arşivlendi
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* 🔮 Interactive Tabs Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 bg-slate-100/80 /60 p-1.5 rounded-xl border border-border">
        <button 
          onClick={() => setActiveTab("summary")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "summary" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-slate-200/50 /50" 
              : "text-muted-foreground hover:text-foreground hover:bg-slate-200/40 dark:hover:bg-slate-800/40"
          }`}
        >
          <FileText size={16} />
          Özet & Hedefler
        </button>

        <button 
          onClick={() => setActiveTab("personas")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "personas" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-slate-200/50 /50" 
              : "text-muted-foreground hover:text-foreground hover:bg-slate-200/40 dark:hover:bg-slate-800/40"
          }`}
        >
          <Users size={16} />
          Personalar ({personas.length})
        </button>

        <button 
          onClick={() => setActiveTab("script")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "script" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-slate-200/50 /50" 
              : "text-muted-foreground hover:text-foreground hover:bg-slate-200/40 dark:hover:bg-slate-800/40"
          }`}
        >
          <ListTodo size={16} />
          Senaryo
        </button>

        <button 
          onClick={() => setActiveTab("interviews")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "interviews" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-slate-200/50 /50" 
              : "text-muted-foreground hover:text-foreground hover:bg-slate-200/40 dark:hover:bg-slate-800/40"
          }`}
        >
          <MessageSquare size={16} />
          Mülakat Kayıtları ({interviews.length})
        </button>

        <button 
          onClick={() => setActiveTab("report")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "report" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-slate-200/50 /50" 
              : "text-muted-foreground hover:text-foreground hover:bg-slate-200/40 dark:hover:bg-slate-800/40"
          }`}
        >
          <TrendingUp size={16} />
          Sentez Raporu
        </button>
      </div>

      {/* 💼 Tab View Content */}
      <div className="space-y-6">

        {/* ==================== Tab 1: Summary ==================== */}
        {activeTab === "summary" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="lg:col-span-2 space-y-6">
              <Card className="shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-[#1863dc] dark:text-[#4c6ee6] text-lg">
                    <Compass size={20} />
                    Araştırma Brief&apos;i ve Bağlam
                  </CardTitle>
                  <CardDescription>Başlangıçta tanımlanan araştırma problemi.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3.5 bg-slate-50 border border-border rounded-lg">
                      <span className="text-xs font-semibold text-muted-foreground block uppercase">Marka / Ürün</span>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{brief?.brand || "Belirtilmemiş"}</span>
                    </div>
                    <div className="p-3.5 bg-slate-50 border border-border rounded-lg">
                      <span className="text-xs font-semibold text-muted-foreground block uppercase">Bütçe / Panel</span>
                      <span className="font-bold text-slate-800 dark:text-slate-100">{brief?.budget || "Standart"}</span>
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-muted-foreground uppercase block">Araştırma Problemi (Brief Context)</span>
                    <p className="text-slate-700 text-sm leading-relaxed bg-slate-50/50 /50 border border-border/60 p-4 rounded-xl">
                      {brief?.context || "Brief bağlamı girilmemiş."}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {plan && (
                <Card className="shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-lg">Araştırma Hedefleri ve Varsayımlar</CardTitle>
                    <CardDescription>Brief doğrultusunda simüle edilen hedefler.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {plan.objective && (
                      <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-muted-foreground uppercase block">Ana Araştırma Hedefi</span>
                        <p className="text-slate-800 text-sm font-medium bg-slate-50 /50 p-4 rounded-xl border border-border">
                          {plan.objective}
                        </p>
                      </div>
                    )}

                    {plan.assumptions && plan.assumptions.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-xs font-semibold text-muted-foreground uppercase block">Test Edilen Varsayımlar (Assumptions)</span>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {plan.assumptions.map((ass: string, i: number) => (
                            <div key={i} className="flex gap-2 p-3 bg-[#f1f5ff]/30 dark:bg-[#071829]/10 border border-[#e5e7eb]/50 dark:border-[rgba(24,99,220,0.1)] rounded-lg text-sm">
                              <span className="font-bold text-[#1863dc] dark:text-[#4c6ee6]">#{i + 1}</span>
                              <span className="text-slate-700 ">{ass}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>

            <div className="space-y-6">
              {/* Quality summary widget */}
              {metadata?.quality_score && (
                <Card className="shadow-sm border-l-4 border-l-emerald-500 overflow-hidden">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-bold uppercase text-muted-foreground">Araştırma Kalite Skoru</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-black text-emerald-600 dark:text-emerald-400">{metadata.quality_score}</span>
                      <span className="text-slate-400 font-semibold text-xl">/100</span>
                      <Badge className="ml-2 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 hover:bg-emerald-50 border border-emerald-200 /40">
                        Sınıf: {metadata.quality_grade || "A"}
                      </Badge>
                    </div>
                    {metadata.quality_summary && (
                      <p className="text-slate-600 text-xs leading-relaxed border-t border-border pt-3">
                        {metadata.quality_summary}
                      </p>
                    )}
                    {/* Bias Detection Flags */}
                    {study?.research_quality && (
                      (() => {
                        const rq = study.research_quality;
                        const flags = [
                          (rq.straight_lining_count || 0) > 0 && {
                            icon: "🔁",
                            label: "Tekdüze Yanıt Kalıbı (Straight-Lining)",
                            count: rq.straight_lining_count || 0,
                            color: "text-red-600 dark:text-red-400",
                            bg: "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/40",
                          },
                          (rq.acquiescence_count || 0) > 0 && {
                            icon: "🟠",
                            label: "Beklenmedik Uzlaşmacılık (Acquiescence)",
                            count: rq.acquiescence_count || 0,
                            color: "text-orange-600 dark:text-orange-400",
                            bg: "bg-orange-50 dark:bg-orange-950/20 border-orange-200 dark:border-orange-900/40",
                          },
                          (rq.social_desirability_count || 0) > 0 && {
                            icon: "💬",
                            label: "Sosyal Beğeni Etkisi",
                            count: rq.social_desirability_count || 0,
                            color: "text-amber-600 dark:text-amber-400",
                            bg: "bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/40",
                          },
                        ].filter(Boolean) as Array<{ icon: string; label: string; count: number; color: string; bg: string }>;

                        return flags.length > 0 ? (
                          <div className="space-y-2 border-t border-border pt-3">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase">Yanıt Sapması Uyarıları</p>
                            {flags.map(f => (
                              <div key={f.label} className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium ${f.bg}`}>
                                <span>{f.icon}</span>
                                <span className={f.color}>{f.label}</span>
                                <Badge variant="outline" className="ml-auto text-[10px]">{f.count} persona</Badge>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 border-t border-border pt-3">
                            <CheckCircle2 size={14} />
                            <span>Yanıt sapması tespit edilmedi.</span>
                          </div>
                        );
                      })()
                    )}
                  </CardContent>
                </Card>
              )}

              {/* RFI Card — Adversarial Review + Research Fidelity Index (Pro+) */}
              <PlanGate currentPlan={clientPlan.plan_type} requiredPlan="Pro" featureName="Araştırma Bütünlüğü (RFI)">
              {study?.research_quality && (
                study.research_quality.warning_count !== undefined ||
                study.research_quality.rfi !== undefined ||
                (study.research_quality.flags && study.research_quality.flags.length >= 0) ||
                study.research_quality.summary !== undefined ||
                (study.research_quality.phases_passed && study.research_quality.phases_passed.length >= 0)
              ) && (
                (() => {
                  const rq = study.research_quality!;
                  const rfi = rq.rfi ?? null;
                  const components = rq.components ?? {};
                  const valid = rq.valid ?? (rfi !== null ? rfi >= 0.65 : false);
                  const warnings = rq.warning_count ?? 0;
                  const phasesPassed = rq.phases_passed ?? [];
                  const phasesFlagged = rq.phases_flagged ?? [];
                  const flags = rq.flags ?? [];
                  const adversarialSummary = rq.interpretation ?? rq.summary ?? "";

                  const rfiColor = rfi === null ? "text-slate-400" : rfi >= 0.80 ? "text-emerald-600 dark:text-emerald-400" : rfi >= 0.65 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400";
                  const borderColor = rfi === null ? "border-l-slate-300" : rfi >= 0.80 ? "border-l-emerald-500" : rfi >= 0.65 ? "border-l-amber-500" : "border-l-red-500";
                  const COMPONENT_COLORS: Record<string, string> = {
                    PGR: "#6366f1", CNS: "#0ea5e9", AC: "#22c55e",
                    PR: "#f97316", PCal: "#ec4899", CRA: "#f59e0b",
                  };
                  const COMPONENT_LABELS: Record<string, string> = {
                    PGR: "Kapsam (PGR)", CNS: "Yenilik (CNS)", AC: "Tutarlılık (AC)",
                    PR: "Temsil (PR)", PCal: "Kalibrasyon", CRA: "Uyum (CRA)",
                  };

                  return (
                    <Card className={`shadow-sm border-l-4 ${borderColor} overflow-hidden`}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-bold uppercase text-muted-foreground flex items-center gap-2">
                          Araştırma Bütünlüğü (RFI)
                          <Badge
                            className={valid
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200 /40"
                              : "bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400 border border-red-200 dark:border-red-900/40"}
                          >
                            {valid ? "Geçerli" : "Eşik Altı"}
                          </Badge>
                        </CardTitle>
                        <CardDescription className="text-[10px]">Grounded Simulation RFI — Bilal (2026) §6.4</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {rfi !== null && (
                          <div className="flex items-baseline gap-2">
                            <span className={`text-4xl font-black ${rfiColor}`}>{(rfi * 100).toFixed(1)}</span>
                            <span className="text-slate-400 font-semibold">/100</span>
                            <span className="text-xs text-muted-foreground">eşik ≥65</span>
                          </div>
                        )}

                        {/* RFI Component Bar Chart */}
                        {Object.keys(components).length > 0 && (
                          <div className="space-y-2 border-t border-border pt-3">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase">Bileşen Profili</p>
                            {Object.entries(components).map(([key, val]) => (
                              <div key={key} className="flex items-center gap-2">
                                <span className="text-[10px] font-semibold text-slate-500 w-28 shrink-0">{COMPONENT_LABELS[key] ?? key}</span>
                                <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
                                  <div
                                    className="h-full rounded-full transition-all duration-700"
                                    style={{ width: `${(val as number) * 100}%`, backgroundColor: COMPONENT_COLORS[key] ?? "#94a3b8" }}
                                  />
                                </div>
                                <span className="text-[10px] font-bold tabular-nums w-8 text-right" style={{ color: COMPONENT_COLORS[key] ?? "#94a3b8" }}>
                                  {((val as number) * 100).toFixed(0)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Adversarial Review özeti */}
                        {(phasesPassed.length > 0 || phasesFlagged.length > 0) && (
                          <div className="space-y-1.5 border-t border-border pt-3">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase">Adversarial Review Aşamaları</p>
                            <div className="flex flex-wrap gap-1.5">
                              {phasesPassed.map(ph => (
                                <Badge key={ph} className="text-[10px] bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200 /40">
                                  ✓ {ph}
                                </Badge>
                              ))}
                              {phasesFlagged.map(ph => (
                                <Badge key={ph} className="text-[10px] bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400 border border-amber-200 dark:border-amber-900/40">
                                  ⚠ {ph}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Uyarı listesi */}
                        {flags.filter(f => f.severity === "warning" || f.severity === "fail").slice(0, 3).length > 0 && (
                          <div className="space-y-1.5 border-t border-border pt-3">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase">Dikkat Gerektiren Noktalar ({warnings})</p>
                            {flags.filter(f => f.severity === "warning" || f.severity === "fail").slice(0, 3).map((f, i) => (
                              <div key={i} className="text-[10px] text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-md px-2.5 py-1.5 leading-relaxed">
                                {f.message.slice(0, 140)}{f.message.length > 140 ? "..." : ""}
                              </div>
                            ))}
                          </div>
                        )}

                        {adversarialSummary && (
                          <p className="text-[10px] text-slate-500 border-t border-border pt-2 leading-relaxed">
                            {adversarialSummary}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  );
                })()
              )}
              </PlanGate>
            </div>
          </div>
        )}

        {/* ==================== Tab 2: Personas ==================== */}
        {activeTab === "personas" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Sentetik Kitle Paneli ({personas.length})</h2>
              <p className="text-muted-foreground text-sm">Araştırmada simüle edilen ve mülakat gerçekleştirilen hedef kitle profilleri.</p>
            </div>

            {personas.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
                Bu araştırmaya ait persona kaydı bulunamadı.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {personas.map((persona: Persona, index: number) => (
                  <Card key={persona.id || index} className="shadow-sm border hover:border-[#e5e7eb] dark:hover:border-[rgba(24,99,220,0.35)]/50 hover:shadow-md transition-all duration-300 group flex flex-col justify-between overflow-hidden">
                    <div>
                      <div className="p-6 bg-slate-50/50 /30 border-b border-border/50 flex justify-between items-start gap-2">
                        <div className="space-y-0.5">
                          <h3 className="font-bold text-lg text-slate-950 dark:text-white group-hover:text-[#1863dc] dark:group-hover:text-[#4c6ee6] transition-colors">
                            {persona.name}
                          </h3>
                          <p className="text-xs text-muted-foreground font-semibold">
                            {persona.role_title || "Sentetik Tüketici"} • {persona.age} Yaşında
                          </p>
                        </div>
                        <Badge className="bg-[#f1f5ff] text-[#1863dc] dark:bg-[#071829]/20 dark:text-[#4c6ee6] hover:bg-[#f1f5ff] border border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] text-xs">
                          {persona.segment}
                        </Badge>
                      </div>

                      <CardContent className="p-6 space-y-4">
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Biyografi & Karakteristik</span>
                          <p className="text-slate-600 text-xs leading-relaxed italic line-clamp-3">
                            &quot;{persona.bio || persona.context}&quot;
                          </p>
                        </div>

                        {/* Slider indicators */}
                        <div className="space-y-3 border-t border-border pt-4">
                          {persona.big_five ? (
                            <>
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">Büyük Beşli (Big Five)</span>
                              {[
                                { label: "Açıklık (Openness)", value: persona.big_five.openness, color: "bg-purple-500" },
                                { label: "Sorumluluk (Conscientiousness)", value: persona.big_five.conscientiousness, color: "bg-blue-500" },
                                { label: "Dışadönüklük (Extroversion)", value: persona.big_five.extroversion, color: "bg-orange-500" },
                                { label: "Uyumluluk (Agreeableness)", value: persona.big_five.agreeableness, color: "bg-teal-500" },
                                { label: "Duygusal Denge (Neuroticism)", value: persona.big_five.neuroticism, color: "bg-rose-500" },
                              ].map(trait => (
                                <div key={trait.label} className="space-y-1">
                                  <div className="flex justify-between text-[10px] font-semibold">
                                    <span className="text-muted-foreground">{trait.label}</span>
                                    <span className="text-slate-800 ">{trait.value}%</span>
                                  </div>
                                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                    <div 
                                      className={`h-full ${trait.color} rounded-full`} 
                                      style={{ width: `${trait.value}%` }}
                                    />
                                  </div>
                                </div>
                              ))}
                            </>
                          ) : (
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-1">
                                <div className="flex justify-between text-[10px] font-semibold">
                                  <span className="text-muted-foreground">Fiyat Hassasiyeti</span>
                                  <span className="text-slate-800 ">{persona.price_sensitivity}/5</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-[#f1f5ff]0 rounded-full" 
                                    style={{ width: `${(persona.price_sensitivity / 5) * 100}%` }}
                                  />
                                </div>
                              </div>
                              <div className="space-y-1">
                                <div className="flex justify-between text-[10px] font-semibold">
                                  <span className="text-muted-foreground">Dijital Güven</span>
                                  <span className="text-slate-800 ">{persona.digital_confidence}/5</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-blue-500 rounded-full" 
                                    style={{ width: `${(persona.digital_confidence / 5) * 100}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Stance + SES details */}
                        <div className="space-y-2 border-t border-border/50 pt-3">
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-muted-foreground">Pazar Yaklaşımı:</span>
                            <Badge variant="outline" className="font-semibold text-slate-700 ">
                              {persona.stance}
                            </Badge>
                          </div>
                          {(persona.ses_group || persona.respondent_type) && (
                            <div className="flex flex-wrap gap-1.5">
                              {persona.ses_group && (
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                  persona.ses_group === "AB" ? "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/20 dark:border-amber-800 dark:text-amber-400" :
                                  persona.ses_group === "C1" ? "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/20 dark:border-blue-800 " :
                                  persona.ses_group === "C2" ? "bg-slate-50 border-slate-200 text-slate-600 " :
                                  "bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/20 dark:border-rose-800 dark:text-rose-400"
                                }`}>SES {persona.ses_group}</span>
                              )}
                              {persona.respondent_type && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#f1f5ff] border border-[#e5e7eb] text-[#1863dc] dark:bg-[#071829]/20 dark:border-[#1863dc]/60 dark:text-[#4c6ee6]">
                                  {({
                                    potential_customer: "Potansiyel",
                                    competitor_user: "Rakip",
                                    churned_user: "Kaybedilmiş",
                                    decision_maker: "Karar Verici",
                                    individual_user: "Bireysel",
                                  } as Record<string, string>)[persona.respondent_type] ?? persona.respondent_type}
                                </span>
                              )}
                              {persona.settlement_type && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 border border-emerald-200 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-800 dark:text-emerald-400">
                                  {persona.settlement_type}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </CardContent>
</div>

                    <div className="px-6 pb-6 pt-0 flex justify-end border-t border-border/40 mt-auto">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="text-xs text-[#1863dc] dark:text-[#4c6ee6] hover:text-[#1863dc] dark:hover:text-[#4c6ee6] font-semibold gap-1.5 p-0 hover:bg-transparent"
                        onClick={() => {
                          // Find index in interviews list
                          const intIdx = interviews.findIndex((i: PersonaInterview) => i.persona?.name === persona.name);
                          if (intIdx !== -1) {
                            setSelectedPersonaIdx(intIdx);
                            setActiveTab("interviews");
                          }
                        }}
                      >
                        <MessageSquare size={14} />
                        Mülakat Kayıtlarını İncele
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}

            {/* SES x Stance Cross-Tab */}
            {study?.ses_cross_tab && study.ses_cross_tab.length > 0 && (
              <Card className="shadow-sm border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)]">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">SES × Duruş Çapraz Tablosu</CardTitle>
                  <CardDescription>TÜAD 2025 sosyo-ekonomik gruplara göre pazar yaklaşımı dağılımı.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left py-2 pr-4 text-xs font-semibold text-muted-foreground uppercase">SES</th>
                          {["Champion","Pragmatist","Observer","Skeptic","Blocker"].map(s => (
                            <th key={s} className="text-center py-2 px-2 text-xs font-semibold text-muted-foreground uppercase">{s}</th>
                          ))}
                          <th className="text-center py-2 pl-4 text-xs font-semibold text-muted-foreground uppercase">Toplam</th>
                          <th className="text-left py-2 pl-4 text-xs font-semibold text-muted-foreground uppercase">Baskın</th>
                        </tr>
                      </thead>
                      <tbody>
                        {study.ses_cross_tab.map(row => (
                          <tr key={row.ses_group} className="border-b border-border/50 hover:bg-slate-50 dark:hover:bg-slate-900/30">
                            <td className="py-2 pr-4">
                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                row.ses_group === "AB" ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400" :
                                row.ses_group === "C1" ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 " :
                                row.ses_group === "C2" ? "bg-slate-100 text-slate-700 " :
                                "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400"
                              }`}>{row.ses_group}</span>
                            </td>
                            {["Champion","Pragmatist","Observer","Skeptic","Blocker"].map(s => {
                              const sc = row.stance_counts as Record<string,number>;
                              const count = sc?.[s] ?? 0;
                              const max = sc ? Math.max(...Object.values(sc)) : 0;
                              return (
                                <td key={s} className="text-center py-2 px-2">
                                  {count > 0 ? (
                                    <span className={`inline-flex w-7 h-7 rounded-full text-xs font-bold items-center justify-center ${
                                      count === max ? "bg-[#1863dc] text-white" : "bg-slate-100 text-slate-600 "
                                    }`}>{count}</span>
                                  ) : <span className="text-muted-foreground">—</span>}
                                </td>
                              );
                            })}
                            <td className="text-center py-2 pl-4 font-semibold">{row.total}</td>
                            <td className="py-2 pl-4"><Badge variant="outline" className="text-xs">{row.dominant_stance}</Badge></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Respondent Type Summary */}
            {study?.respondent_type_summary && study.respondent_type_summary.length > 0 && (
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Katılımcı Tipi Bazında Özet</CardTitle>
                  <CardDescription>Her katılımcı tipi için öne çıkan ağrı noktası ve itiraz.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {study.respondent_type_summary.map(rt => (
                      <div key={rt.respondent_type} className="p-4 border border-border rounded-xl space-y-2 hover:border-[#e5e7eb] dark:hover:border-[rgba(24,99,220,0.35)]/40 transition-colors">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-sm text-slate-800 dark:text-slate-100">{rt.label}</span>
                          <Badge variant="secondary" className="text-xs">{rt.count} kişi</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Ort. fiyat hassasiyeti: <strong className="text-slate-700 ">{rt.avg_price_sensitivity.toFixed(1)}/10</strong>
                        </div>
                        {rt.top_pain && (
                          <div className="text-xs bg-rose-50 dark:bg-rose-950/20 border border-rose-100 /30 rounded-lg p-2 text-rose-700 dark:text-rose-400 italic line-clamp-2">
                            &ldquo;{rt.top_pain}&rdquo;
                          </div>
                        )}
                        {rt.top_objection && (
                          <div className="text-xs bg-amber-50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30 rounded-lg p-2 text-amber-700 dark:text-amber-400 italic line-clamp-2">
                            &ldquo;{rt.top_objection}&rdquo;
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* ==================== Tab 3: Interviews & Transcripts ==================== */}
        {activeTab === "interviews" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Mülakat Transcriptleri</h2>
              <p className="text-muted-foreground text-sm">Yapay zeka moderatörü ve sentetik personalar arasında geçen tüm diyaloglar.</p>
            </div>

            {interviews.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
                Bu araştırmaya ait mülakat kaydı bulunamadı.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {interviews.map((item: PersonaInterview, idx: number) => (
                  <Card key={idx} className="shadow-sm border hover:border-[#e5e7eb] dark:hover:border-[rgba(24,99,220,0.35)]/50 hover:shadow-md transition-all duration-300">
                    <CardHeader className="p-5 pb-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-base">{item.persona?.name}</CardTitle>
                          <CardDescription className="text-xs">{item.persona?.role_title || "Sentetik Tüketici"} • {item.persona?.age} Yaş</CardDescription>
                        </div>
                        <Badge variant="outline" className="text-[10px] bg-slate-50 dark:bg-slate-900">{item.turns?.length} Soru</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-0 space-y-4">
                      <div className="text-xs text-muted-foreground flex items-center justify-between">
                        <span>Durum:</span>
                        <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400">Mülakat Tamamlandı</Badge>
                      </div>
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" className="w-full text-xs font-semibold gap-2 border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900">
                            <MessageSquare size={14} />
                            Transcript Görüntüle
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col p-0 overflow-hidden">
                          <DialogHeader className="p-6 pb-4 border-b border-border/80 bg-slate-50 dark:bg-slate-900/50">
                            <DialogTitle>Mülakat Transkripti: {item.persona?.name}</DialogTitle>
                            <DialogDescription>
                              {item.persona?.role_title} • {item.persona?.age} Yaş • {item.persona?.city} • {item.persona?.stance} Profil
                            </DialogDescription>
                          </DialogHeader>
                          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30 dark:bg-slate-950/10">
                            {item.turns?.map((turn: InterviewTurn, turnIdx: number) => (
                              <div key={turnIdx} className="space-y-4">
                                {/* AI Interviewer Bubble */}
                                <div className="flex gap-3 max-w-[85%]">
                                  <div className="h-8 w-8 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-xs shrink-0 select-none">
                                    Q
                                  </div>
                                  <div className="p-3.5 bg-white dark:bg-[#1c1c21] border border-slate-200/60 dark:border-slate-800 rounded-2xl rounded-tl-none shadow-sm text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                                    {turn.question}
                                  </div>
                                </div>
                                {/* Persona Bubble */}
                                <div className="flex gap-3 max-w-[90%] ml-auto justify-end">
                                  <div className="p-3.5 bg-primary dark:bg-[#2c2c33] text-white rounded-2xl rounded-tr-none shadow-sm text-sm leading-relaxed">
                                    {turn.answer}
                                  </div>
                                  <div className="h-8 w-8 rounded-full bg-[#f1f5ff] dark:bg-[#071829] text-[#1863dc] dark:text-[#4c6ee6] border border-[#e5e7eb]/50 dark:border-[rgba(24,99,220,0.15)] flex items-center justify-center font-bold text-xs shrink-0 select-none">
                                    {item.persona?.name.charAt(0) || "P"}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          <DialogFooter className="p-4 border-t border-border bg-white dark:bg-[#0c0c0f] flex flex-col gap-3 sm:justify-start">
                            <div className="flex gap-2 w-full">
                              <Textarea 
                                placeholder={`${item.persona?.name} isimli personaya ekstra bir soru sorun...`}
                                className="min-h-[60px] resize-none text-sm"
                                value={followUpText}
                                onChange={(e) => setFollowUpText(e.target.value)}
                                disabled={sendingFollowUp}
                              />
                              <Button 
                                onClick={() => handleFollowUp(item.persona.id)} 
                                disabled={sendingFollowUp || !followUpText.trim()}
                                className="h-auto px-6 font-semibold"
                              >
                                {sendingFollowUp ? <Loader2 className="animate-spin w-4 h-4" /> : "Sor"}
                              </Button>
                            </div>
                            <span className="text-[10px] text-muted-foreground text-center">Follow-up özelliği ile personayı daha derinlemesine analiz edebilirsiniz.</span>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ==================== Tab: Script ==================== */}
        {activeTab === "script" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Mülakat Senaryosu</h2>
              <p className="text-muted-foreground text-sm">Yapay zeka moderatörünün personalara yönelttiği ana sorular.</p>
            </div>

            {(!plan?.interview_questions || plan.interview_questions.length === 0) ? (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
                Bu araştırmaya ait senaryo kaydı bulunamadı.
              </div>
            ) : (
              <Card className="shadow-sm border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] overflow-hidden">
                <CardHeader className="bg-slate-50/50 dark:bg-slate-900/50 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">Mülakat Akışı</CardTitle>
                      <CardDescription>Toplam {plan.interview_questions.length} soru kalıbı kullanıldı.</CardDescription>
                    </div>
                    <Badge variant="outline" className="bg-white dark:bg-slate-950">
                      Salt Okunur (Read-Only)
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="divide-y divide-border/60">
                    {plan.interview_questions.map((q: string, i: number) => (
                      <div key={i} className="flex gap-4 p-5 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors">
                        <div className="h-6 w-6 rounded-full bg-[#f1f5ff] dark:bg-[#071829] text-[#1863dc] dark:text-[#4c6ee6] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                          {i + 1}
                        </div>
                        <div className="space-y-2 flex-1">
                          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 leading-relaxed">{q}</p>
                          <div className="flex gap-2">
                            <Badge variant="secondary" className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500">Açık Uçlu Soru</Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* ==================== Tab 4: Synthesis Report ==================== */}
        {activeTab === "report" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Yapay Zeka Sentez Raporu</h2>
              <p className="text-muted-foreground text-sm">Sentetik mülakatlardan elde edilen pazar analizleri, itirazlar ve ürün geliştirme tavsiyeleri.</p>
            </div>

            {!isCompleted ? (
              <div className="text-center py-16 text-muted-foreground border border-dashed border-border rounded-xl bg-slate-50/50 /30">
                Bu araştırma henüz tamamlanmamış veya nihai sentez raporu üretilmemiş.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Van Westendorp PSM Card (Starter+) */}
                <PlanGate currentPlan={clientPlan.plan_type} requiredPlan="Starter" featureName="Van Westendorp Fiyat Analizi">
                {study?.van_westendorp && (
                  <Card className="shadow-sm border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] overflow-hidden">
                    <CardHeader className="pb-3 bg-[#f1f5ff]/60 dark:bg-[#071829]/20">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <CardTitle className="text-base text-[#1863dc] dark:text-[#4c6ee6]">
                            Van Westendorp Fiyat Hassasiyet Ölçeri (PSM)
                          </CardTitle>
                          <CardDescription className="mt-0.5">
                            Sentetik mülakat yanıtlarından çıkarılan kabul edilebilir fiyat aralığı.
                          </CardDescription>
                        </div>
                        <Badge className="bg-[#1863dc] text-white text-xs shrink-0">
                          {study.van_westendorp.currency}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="p-6 space-y-6">
                      {/* Key metrics */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {[
                          { label: "PMC", sublabel: "Alt Kabul Sınırı", value: study.van_westendorp.pmc, color: "text-[#1863dc] dark:text-[#4c6ee6]", bg: "bg-[#f1f5ff] dark:bg-[#071829]/20 border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)]" },
                          { label: "OPP", sublabel: "Optimal Fiyat", value: study.van_westendorp.opp, color: "text-teal-700 dark:text-teal-400", bg: "bg-teal-50 dark:bg-teal-950/20 border-teal-100 dark:border-teal-900/30" },
                          { label: "IPP", sublabel: "Beklenti Noktası", value: study.van_westendorp.ipp, color: "text-sky-600 dark:text-sky-400", bg: "bg-sky-50 dark:bg-sky-950/20 border-sky-100 dark:border-sky-900/30" },
                          { label: "PME", sublabel: "Üst Kabul Sınırı", value: study.van_westendorp.pme, color: "text-pink-600 dark:text-pink-400", bg: "bg-pink-50 dark:bg-pink-950/20 border-pink-100 dark:border-pink-900/30" },
                        ].map(m => (
                          <div key={m.label} className={`p-3 rounded-xl border ${m.bg} text-center`}>
                            <div className={`text-2xl font-black ${m.color}`}>
                              {m.value.toLocaleString("tr-TR")} ₺
                            </div>
                            <div className="text-[10px] font-bold text-muted-foreground uppercase mt-1">{m.label}</div>
                            <div className="text-[10px] text-muted-foreground">{m.sublabel}</div>
                          </div>
                        ))}
                      </div>

                      {/* Acceptable range banner */}
                      <div className="flex items-center gap-3 p-3 bg-[#f1f5ff] dark:bg-[#071829]/20 border border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] rounded-xl text-sm">
                        <div className="w-3 h-3 rounded-sm bg-[#e5e7eb] dark:bg-[rgba(24,99,220,0.25)] shrink-0" />
                        <span className="text-muted-foreground">Kabul edilebilir fiyat aralığı:</span>
                        <span className="font-bold text-[#1863dc] dark:text-[#4c6ee6]">
                          {study.van_westendorp.acceptable_range[0].toLocaleString("tr-TR")} ₺
                          {" — "}
                          {study.van_westendorp.acceptable_range[1].toLocaleString("tr-TR")} ₺
                        </span>
                      </div>

                      {/* SVG Chart */}
                      <PSMChart data={study.van_westendorp} />

                      {/* Methodology note */}
                      <p className="text-xs text-muted-foreground italic border-t border-border/50 pt-3">
                        {study.van_westendorp.methodology_note}
                      </p>
                    </CardContent>
                  </Card>
                )}
                </PlanGate>

                {/* Brand Health Card (Pro+) */}
                <PlanGate currentPlan={clientPlan.plan_type} requiredPlan="Pro" featureName="Marka Sağlığı Analizi">
                {study?.brand_health && (
                  <Card className="shadow-sm border-sky-100 dark:border-sky-900/30">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base text-sky-700 dark:text-sky-400">Marka Sağlığı — Yardımsız Bilinirlik</CardTitle>
                      <CardDescription>
                        {study.brand_health.top_of_mind
                          ? `"${study.brand_health.top_of_mind}" en çok akla gelen rakip (${study.brand_health.total_mentions} toplam anma).`
                          : "Rakip marka anma verisi bulunamadı."}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Unaided recall counts */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        {Object.entries(study.brand_health.unaided_recall)
                          .filter(([k]) => k !== "diğer")
                          .sort(([,a],[,b]) => b - a)
                          .map(([brand, count]) => (
                            <div key={brand} className="p-3 border border-border rounded-xl text-center">
                              <div className="text-xl font-black text-sky-600 dark:text-sky-400">{count}</div>
                              <div className="text-xs text-muted-foreground mt-1 truncate">{brand}</div>
                            </div>
                          ))}
                      </div>
                      {/* Associations */}
                      {Object.keys(study.brand_health.associations).length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs font-semibold text-muted-foreground uppercase">Çağrışım Haritası</p>
                          {Object.entries(study.brand_health.associations).map(([brand, words]) => (
                            <div key={brand} className="flex flex-wrap items-center gap-2">
                              <span className="text-xs font-bold text-slate-700 w-24 shrink-0">{brand}</span>
                              {words.map(w => (
                                <Badge key={w} variant="outline" className="text-[10px] font-medium">{w}</Badge>
                              ))}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
                </PlanGate>

                {/* Channel Discovery Card */}
                {study?.channel_map && study.channel_map.length > 0 && (
                  <Card className="shadow-sm border-emerald-100 /30">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base text-emerald-700 dark:text-emerald-400">Keşif Kanalı Haritası</CardTitle>
                      <CardDescription>Sentetik personaların ürünü keşfetmek için tercih ettiği kanallar.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ChannelBarChart data={study.channel_map} />
                    </CardContent>
                  </Card>
                )}

                {/* Synthesis markdown report */}
                <Card className="shadow-sm">
                  <CardContent className="p-6 sm:p-10 prose prose-slate max-w-none dark:prose-invert">
                    {renderMarkdown(study.report_markdown)}
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
