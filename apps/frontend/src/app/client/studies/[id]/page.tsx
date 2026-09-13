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
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  ListTodo,
  Lock,
  Trash2,
  Search,
  Globe,
  Send,
  Ship,
  GitBranch,
  AlertTriangle,
  Zap
} from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { PlanGate } from "@/components/plan-gate";
import { useClientPlan } from "@/hooks/use-client-plan";
import { getAuthHeaders } from "@/lib/auth";
import { trackEvent } from "@/lib/events";

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
  big_five?: Record<string, number>;
  attributes?: Record<string, string>;
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
    title: string;
    market?: string;
    category?: string;
    idea?: string;
    expected_price?: string;
    target_users?: string[];
    competitors?: string[];
    success_metric?: string;
    sales_channel?: string;
    discovery_channels?: string[];
    panel_size?: string;
    geography?: string;
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
  findings?: Array<{
    id: number;
    title: string;
    category: string;
    summary: string;
    confidence: number;
    implication: string;
    supporting_count: number;
    refuting_count: number;
    neutral_count: number;
    contradiction_score: number;
    decision_signal: string;
    evidence?: Array<{
      persona_id: string;
      persona_name: string;
      stance: string;
      question: string;
      quote: string;
      sentiment: string;
    }>;
  }>;
  recommendations?: string[];
  action_items?: string[];
  decision_items?: Array<{
    signal: string;
    title: string;
    confidence: number;
    supporting_count: number;
    refuting_count: number;
    evidence_summary: string;
    recommended_action: string;
  }>;
  external_evidence?: Array<{
    finding_title: string;
    source_title: string;
    source_url: string;
    snippet: string;
    relevance: string;
  }>;
  report_metrics?: {
    findings_total?: number;
    findings_with_evidence?: number;
    unsourced_findings?: number;
    evidence_total?: number;
    evidence_per_finding?: number;
    unique_personas_in_evidence?: number;
    refuting_ratio?: number;
    answer_completion_rate?: number;
    external_evidence_count?: number;
    decision_signals?: Record<string, number>;
  };
}

// ──────────────── Decision Signal Config ────────────────
const DECISION_CONFIG: Record<string, { icon: React.ComponentType<{ size?: number; className?: string }>; color: string; bg: string; label: string }> = {
  SHIP: { icon: Ship, color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200", label: "Yayınla" },
  ITERATE: { icon: GitBranch, color: "text-amber-700", bg: "bg-amber-50 border-amber-200", label: "İyileştir" },
  INVESTIGATE: { icon: AlertTriangle, color: "text-sky-700", bg: "bg-sky-50 border-sky-200", label: "Araştır" },
  KILL: { icon: Trash2, color: "text-red-700", bg: "bg-red-50 border-red-200", label: "Vazgeç" },
};

// Duruş (stance) etiketlerinin Türkçe karşılıkları
const STANCE_TR: Record<string, string> = {
  "Champion": "Öncü",
  "Pragmatist": "Pragmatist",
  "Observer": "Gözlemci",
  "Skeptic": "Şüpheci",
  "Blocker": "Engelleyici",
  "Innovator": "Öncü",
  "EarlyAdopter": "Erken Benimseyen",
  "Mainstream": "Ana Akım",
  "Laggard": "Geciken",
};

// ──────────────── Finding Card Component ────────────────
function FindingCard({ finding, dc, DcIcon, confPct, barColor }: {
  finding: NonNullable<StudyDetail["findings"]>[number];
  dc: typeof DECISION_CONFIG[string];
  DcIcon: React.ComponentType<{ size?: number; className?: string }>;
  confPct: number;
  barColor: string;
}) {
  const [showEvidence, setShowEvidence] = useState(false);

  return (
    <Card className="shadow-sm border-[#d9d9dd]/60 hover:border-[#003c33]/30 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <CardTitle className="text-base">{finding.title}</CardTitle>
              <Badge className={`text-[10px] font-bold ${dc.bg} ${dc.color}`}>
                <DcIcon size={12} className="mr-1 inline" />
                {dc.label}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground mt-1.5">{finding.summary}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        {/* Confidence Bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-[#616161]">Güven Skoru</span>
            <span className="font-bold text-[#212121]">%{confPct}</span>
          </div>
          <div className="h-2 w-full bg-[#eeece7] rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${barColor}`}
              style={{ width: `${confPct}%` }}
            />
          </div>
        </div>

        {/* Support / Refute counts */}
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-emerald-600 font-medium">
            <ThumbsUp size={12} />
            Destekleyen: {finding.supporting_count} persona
          </span>
          <span className="flex items-center gap-1 text-red-500 font-medium">
            <ThumbsDown size={12} />
            İtiraz: {finding.refuting_count}
          </span>
          {finding.neutral_count > 0 && (
            <span className="text-muted-foreground">
              Nötr: {finding.neutral_count}
            </span>
          )}
        </div>

        {/* Contradiction Score */}
        {finding.contradiction_score > 0 && (
          <div className="flex items-center gap-2 p-2 rounded-md bg-amber-50 border border-amber-200 text-xs text-amber-700">
            <AlertTriangle size={14} />
            <span>Çelişki Skoru: {(finding.contradiction_score * 100).toFixed(0)}% — bu bulgu persona grupları arasında görüş ayrılığı içeriyor.</span>
          </div>
        )}

        {/* Evidence Quotes (collapsible) */}
        {finding.evidence && finding.evidence.length > 0 && (
          <div className="border-t border-border pt-3">
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="flex items-center gap-1.5 text-xs font-semibold text-[#1863dc] hover:text-[#1863dc]/80 transition-colors"
            >
              <MessageSquare size={12} />
              Kanıt Alıntıları ({finding.evidence.length})
              <span className="text-[10px]">{showEvidence ? "▲" : "▼"}</span>
            </button>
            {showEvidence && (
              <div className="space-y-2 mt-2">
                {finding.evidence.slice(0, 3).map((ev, ei) => (
                  <div key={ei} className="flex gap-2 p-2.5 bg-[#f5f4f1] rounded-lg border border-border/60 text-xs">
                    <div className="shrink-0">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        (ev.stance === "Innovator" || ev.stance === "EarlyAdopter") ? "bg-emerald-100 text-emerald-700" :
                        ev.stance === "Skeptic" ? "bg-amber-100 text-amber-700" :
                        ev.stance === "Laggard" ? "bg-red-100 text-red-700" :
                        "bg-[#eeece7] text-[#616161]"
                      }`}>{STANCE_TR[ev.stance] || ev.stance}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="font-semibold text-[#212121]">{ev.persona_name}</span>
                      <span className="text-muted-foreground ml-1">({ev.sentiment})</span>
                      <p className="italic text-[#616161] mt-0.5 line-clamp-2">&ldquo;{ev.quote}&rdquo;</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Implication */}
        {finding.implication && (
          <div className="border-t border-border pt-3">
            <span className="text-[10px] font-bold text-muted-foreground uppercase block mb-1">Çıkarım</span>
            <p className="text-xs text-[#616161] leading-relaxed">{finding.implication}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
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
          <span className="text-xs font-medium text-[#616161] w-40 shrink-0 truncate">{row.channel}</span>
          <div className="flex-1 bg-[#eeece7] rounded-full h-2.5 overflow-hidden">
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

// ──────────────── Büyük Beşli Radar Grafiği ────────────────
function BigFiveRadar({ bigFive }: { bigFive: Record<string, number> }) {
  const W = 240, H = 240, cx = W / 2, cy = H / 2, R = 82;
  const axes = [
    { label: "Açıklık", value: bigFive?.Openness ?? bigFive?.openness ?? 50 },
    { label: "Sorumluluk", value: bigFive?.Conscientiousness ?? bigFive?.conscientiousness ?? 50 },
    { label: "Dışadönüklük", value: bigFive?.Extraversion ?? bigFive?.extraversion ?? 50 },
    { label: "Uyumluluk", value: bigFive?.Agreeableness ?? bigFive?.agreeableness ?? 50 },
    { label: "Denge", value: bigFive?.Neuroticism ?? bigFive?.neuroticism ?? 50 },
  ];
  const N = axes.length;
  const angle = (i: number) => (Math.PI * 2 * i) / N - Math.PI / 2;
  const pt = (i: number, r: number) => [cx + r * Math.cos(angle(i)), cy + r * Math.sin(angle(i))] as const;

  const rings = [0.34, 0.67, 1].map((f, ri) => {
    const pts = Array.from({ length: N }, (_, i) => pt(i, R * f).map(n => n.toFixed(1)).join(",")).join(" ");
    return <polygon key={ri} points={pts} fill="none" stroke="#d9d9dd" strokeWidth="1" />;
  });
  const spokes = Array.from({ length: N }, (_, i) => {
    const [x, y] = pt(i, R);
    return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#d9d9dd" strokeWidth="1" />;
  });
  const valuePts = Array.from(
    { length: N },
    (_, i) => pt(i, (R * Math.min(100, axes[i].value)) / 100).map(n => n.toFixed(1)).join(",")
  ).join(" ");
  const labels = Array.from({ length: N }, (_, i) => {
    const [x, y] = pt(i, R + 20);
    return (
      <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="9" fill="#616161">
        {axes[i].label}
      </text>
    );
  });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-[220px] mx-auto" role="img" aria-label="Büyük Beşli kişilik radarı">
      {rings}{spokes}
      <polygon points={valuePts} fill="#003c33" fillOpacity="0.22" stroke="#003c33" strokeWidth="2" />
      {labels}
    </svg>
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
              className="fill-[#93939f]" fontSize="10">{t}%</text>
          </g>
        ))}

        {/* X axis ticks */}
        {priceTicks.map(v => (
          <g key={v}>
            <line x1={xScale(v)} y1={PAD.top + innerH} x2={xScale(v)} y2={PAD.top + innerH + 4}
              stroke="#cbd5e1" strokeWidth="1" />
            <text x={xScale(v)} y={PAD.top + innerH + 16} textAnchor="middle"
              className="fill-[#93939f]" fontSize="10">{v.toLocaleString("tr-TR")} ₺</text>
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
            <span className="text-[#616161] ">{l.label}</span>
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
  const [activeTab, setActiveTab] = useState<"summary" | "personas" | "script" | "interviews" | "findings" | "report">("summary");
  const [, setSelectedPersonaIdx] = useState<number>(0);
  const [deleting, setDeleting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  const [followUpText, setFollowUpText] = useState("");
  const [sendingFollowUp, setSendingFollowUp] = useState(false);
  const [synthesizing, setSynthesizing] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [chatInput, setChatInput] = useState("");
  const [sendingChat, setSendingChat] = useState(false);
  const { plan: clientPlan } = useClientPlan();

  // Sprint 3 — Funnel ölçümü: çalışma detayı ve rapor sekmesi görüntüleme
  useEffect(() => {
    if (!studyId) return;
    trackEvent("study_detail_viewed", studyId);
  }, [studyId]);

  useEffect(() => {
    if (!studyId || activeTab !== "report") return;
    trackEvent("report_tab_viewed", studyId);
  }, [studyId, activeTab]);

  useEffect(() => {
    if (!studyId) return;

    const fetchStudy = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/client/studies/${studyId}`, { headers: getAuthHeaders() });
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error("Araştırma bulunamadı.");
          }
          throw new Error("Veriler yüklenirken bir hata oluştu.");
        }
        const data = await res.json();
        setStudy(data);
        
        // Fetch findings if report is available
        if (data.metadata?.has_report) {
          try {
            const findingsRes = await fetch(`/api/client/studies/${studyId}/findings`, { headers: getAuthHeaders() });
            if (findingsRes.ok) {
              const findingsData = await findingsRes.json();
              setStudy(prev => prev ? { ...prev, findings: findingsData.findings || [], decision_items: findingsData.decision_items || [] } : prev);
            }
          } catch { /* findings optional */ }
        }
        
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

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await fetch(`/api/client/studies/${studyId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || "Silme başarısız.");
      }
      toast.success("Araştırma kalıcı olarak silindi.");
      router.push("/client");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Araştırma silinemedi.");
      setDeleting(false);
      setDeleteModalOpen(false);
    }
  };


  const handleFollowUp = async (personaId: string) => {
    if (!followUpText.trim()) return;
    setSendingFollowUp(true);
    try {
      const res = await fetch(`/api/client/studies/${studyId}/follow-up`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
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
    } catch {
      toast.error("Soru sorulurken bir hata oluştu.");
    } finally {
      setSendingFollowUp(false);
    }
  };

  const sendChat = async () => {
    if (!chatInput.trim() || sendingChat) return;
    const question = chatInput.trim();
    setChatMessages(prev => [...prev, { role: "user", content: question }]);
    setChatInput("");
    setSendingChat(true);
    try {
      const res = await fetch(`/api/client/studies/${studyId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ question }),
      });
      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, { role: "assistant", content: data.answer || data.response || "" }]);
      } else {
        let errMsg = "Yanıt alınamadı. Lütfen tekrar deneyin.";
        try {
          const errData = await res.json();
          const d = errData?.detail;
          if (typeof d === "string") errMsg = d;
          else if (d?.message) errMsg = d.message;
          else if (d?.required_plan) errMsg = `Bu özellik ${d.required_plan} planı gerektirir.`;
        } catch {}
        setChatMessages(prev => [...prev, { role: "assistant", content: errMsg }]);
      }
    } catch {
      setChatMessages(prev => [...prev, { role: "assistant", content: "Bir hata oluştu. Lütfen tekrar deneyin." }]);
    } finally {
      setSendingChat(false);
    }
  };

  // Premium Markdown Parser to render synthesis report elegantly without dependencies
  const renderMarkdown = (mdText?: string) => {
    if (!mdText) return <p className="text-muted-foreground">Rapor içeriği bulunmamaktadır.</p>;

    const lines = mdText.split("\n");
    const out: React.ReactNode[] = [];
    let i = 0;

    const renderTable = (startIdx: number): number => {
      // startIdx bir tablo satırı ("| ... |") — ardışık satırları topla
      const rows: string[][] = [];
      let j = startIdx;
      while (j < lines.length && lines[j].trim().startsWith("|")) {
        const cells = lines[j].trim().split("|").slice(1, -1).map((c) => c.trim());
        // Ayraç satırını (|---|) atla
        if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) {
          rows.push(cells);
        }
        j++;
      }
      if (rows.length === 0) return j;
      const [head, ...body] = rows;
      out.push(
        <div key={`tbl-${startIdx}`} className="overflow-x-auto my-4 border border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)] rounded-lg">
          <table className="w-full text-sm">
            {head && (
              <thead>
                <tr className="bg-[#f5f4f1] dark:bg-[rgba(255,255,255,0.05)]">
                  {head.map((c, ci) => (
                    <th key={ci} className="text-left font-bold text-[#212121] dark:text-[#e5e7eb] px-3 py-2 border-b border-[#d9d9dd]">{c}</th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody>
              {body.map((row, ri) => (
                <tr key={ri} className="border-b border-[#eeece7] last:border-0">
                  {row.map((c, ci) => (
                    <td key={ci} className="px-3 py-2 text-[#616161] dark:text-[#a1a1aa]">{parseBoldText(c)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      return j;
    };

    while (i < lines.length) {
      const line = lines[i];
      const idx = i;

      // Tablo satırı — ardışık tablo satırlarını tek bileşene topla
      if (line.trim().startsWith("|")) {
        i = renderTable(i);
        continue;
      }

      // Headers
      if (line.startsWith("### ")) {
        out.push(<h4 key={idx} className="text-lg font-semibold text-[#212121] dark:text-[#e5e7eb] mt-5 mb-2">{line.replace("### ", "")}</h4>);
        i++;
        continue;
      }
      if (line.startsWith("## ")) {
        out.push(<h3 key={idx} className="text-xl font-bold text-[#212121] dark:text-[#e5e7eb] mt-6 mb-3 border-b pb-1 border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)]">{line.replace("## ", "")}</h3>);
        i++;
        continue;
      }
      if (line.startsWith("# ")) {
        out.push(<h2 key={idx} className="text-2xl font-black text-[#17171c] dark:text-white mt-8 mb-4">{line.replace("# ", "")}</h2>);
        i++;
        continue;
      }

      // Bullet points
      if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
        const cleanText = line.trim().replace(/^[-*]\s+/, "");
        out.push(
          <li key={idx} className="list-disc pl-2 ml-5 text-[#616161] leading-relaxed my-1">
            {parseBoldText(cleanText)}
          </li>
        );
        i++;
        continue;
      }

      // Blockquotes / Warnings
      if (line.startsWith("> ")) {
        out.push(
          <div key={idx} className="border-l-4 border-[#1863dc] pl-4 py-2 bg-[#f1f5ff]/40 dark:bg-[#071829]/20 rounded-r-md text-[#616161] italic my-4">
            {line.replace("> ", "")}
          </div>
        );
        i++;
        continue;
      }

      // Paragraph
      if (line.trim() === "") {
        i++;
        continue;
      }

      out.push(
        <p key={idx} className="text-[#616161] leading-relaxed my-3">
          {parseBoldText(line)}
        </p>
      );
      i++;
    }

    return out;
  };

  // Helper to parse bold markdown syntax (**text**) within a paragraph
  const parseBoldText = (text: string) => {
    const parts = text.split(/\*\*([^*]+)\*\*/g);
    return parts.map((part, index) => {
      // Every odd element is bold
      if (index % 2 === 1) {
        return <strong key={index} className="font-semibold text-[#17171c] dark:text-[#e5e7eb]">{part}</strong>;
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
              <Badge variant="outline" className="bg-[#eeece7] text-[#616161] text-xs font-semibold">
                {metadata?.category || "Genel"}
              </Badge>
              {isCompleted ? (
                <Badge className="bg-[#003c33] hover:bg-[#003c33]/85 text-white flex items-center gap-1 text-xs">
                  <CheckCircle2 size={12} />
                  Tamamlandı
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">Taslak</Badge>
              )}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-[#17171c] dark:text-white">
              {metadata?.title || "İsimsiz Simülasyon"}
            </h1>
            <p className="text-muted-foreground text-sm flex items-center gap-1.5">
              <Calendar size={14} />
              Son Güncelleme: {metadata?.updated_at ? new Date(metadata.updated_at).toLocaleDateString("tr-TR") : "-"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Raporu Olustur — sadece henüz tamamlanmamıs arastirmalarda */}
            {!isCompleted && interviews.length > 0 && (
              <Button
                className="w-full sm:w-auto gap-2 bg-[#003c33] hover:bg-[#003c33]/85 text-white font-semibold"
                disabled={synthesizing}
                onClick={async () => {
                  setSynthesizing(true);
                  try {
                    const res = await fetch(`/api/client/synthesize`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        ...getAuthHeaders(),
                      },
                      body: JSON.stringify({
                        brief: brief || { title: metadata?.title || "", market: "TR", category: metadata?.category || "genel", context: "" },
                        plan: plan || {},
                        interviews: interviews,
                        personas: personas,
                      }),
                    });
                    if (!res.ok) throw new Error("Rapor olusturulamadi.");
                    const report = await res.json();
                    
                    // Save report to study — spread report fields to top level
                    const reportPayload = {
                      brief, plan, personas, interviews,
                      report_json: report,
                      report_markdown: report.report_markdown || report.executive_summary?.join("\n") || "",
                      report_html: report.report_html || "",
                      findings: report.findings || [],
                      action_items: report.action_items || [],
                      recommendations: report.recommendations || [],
                      limitations: report.limitations || [],
                      pricing: report.pricing || null,
                      van_westendorp: report.van_westendorp || null,
                      brand_health: report.brand_health || null,
                      pain_point_matrix: report.pain_point_matrix || [],
                      ses_cross_tab: report.ses_cross_tab || [],
                      research_quality: report.research_quality || null,
                    };
                    await fetch(`/api/client/studies`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        ...getAuthHeaders(),
                      },
                      body: JSON.stringify({
                        metadata: {
                          ...metadata,
                          has_report: true,
                          quality_score: report.quality_score ?? metadata?.quality_score ?? 0,
                          quality_grade: report.quality_grade ?? metadata?.quality_grade ?? "N/A",
                        },
                        payload: reportPayload,
                      }),
                    });
                    
                    toast.success("Rapor olusturuldu!");
                    // Reload study data
                    const updated = await fetch(`/api/client/studies/${studyId}`, { headers: getAuthHeaders() });
                    if (updated.ok) setStudy(await updated.json());
                    setActiveTab("report");
                  } catch (err) {
                    toast.error(err instanceof Error ? err.message : "Rapor olusturulamadi.");
                  } finally {
                    setSynthesizing(false);
                  }
                }}
              >
                {synthesizing ? <Loader2 size={16} className="animate-spin" /> : <TrendingUp size={16} />}
                {synthesizing ? "Rapor Olusturuluyor..." : "Raporu Olustur"}
              </Button>
            )}

            {isCompleted && (
              !clientPlan?.features?.pdf_export ? (
                <Button
                  variant="outline"
                  className="w-full sm:w-auto gap-2 text-[#93939f] border-[#d9d9dd] cursor-not-allowed"
                  onClick={() =>
                    toast.error(
                      <div className="flex flex-col gap-1.5">
                        <span className="font-semibold text-[13px]">PDF İndirme · Flex+ planı gerektirir</span>
                        <span className="text-xs opacity-90">Bu özelliğe erişmek için planınızı yükseltin.</span>
                        <Link href="/client/upgrade" className="text-xs underline font-bold mt-1">Planı Yükselt →</Link>
                      </div>,
                      { duration: 5000 }
                    )
                  }
                >
                  <Lock size={14} />
                  PDF Raporu İndir
                </Button>
              ) : (
                <Button 
                  className="w-full sm:w-auto btn-pill-primary gap-2"
                  onClick={async () => {
                    try {
                      const res = await fetch(`/api/client/studies/${studyId}/pdf`, {
                        method: "GET",
                        headers: getAuthHeaders()
                      });
                      if (!res.ok) {
                        const errData = await res.json().catch(() => ({}));
                        if (errData?.detail?.code === "PLAN_GATE" || (typeof errData?.detail === "string" && errData.detail.includes("plan"))) {
                          const required = errData?.detail?.required_plan || "Flex";
                          toast.error(
                            <div className="flex flex-col gap-1.5">
                              <span className="font-semibold text-[13px]">PDF İndirme · {required}+ planı gerektirir</span>
                              <span className="text-xs opacity-90">Bu özelliğe erişmek için planınızı yükseltin.</span>
                              <Link href="/client/upgrade" className="text-xs underline font-bold mt-1">Planı Yükselt →</Link>
                            </div>,
                            { duration: 5000 }
                          );
                          return;
                        }
                        throw new Error(errData?.detail || "Rapor indirilemedi.");
                      }
                      const blob = await res.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${clientPlan.features.white_label ? "Research-Rapor" : "Clarere-Rapor"}-${studyId}.pdf`;
                      document.body.appendChild(a);
                      a.click();
                      a.remove();
                    } catch {
                      toast.error("İndirme işlemi başarısız oldu.");
                    }
                  }}
                >
                  <Download size={16} />
                  PDF Raporu İndir
                </Button>
              )
            )}



            {/* ── Sil Butonu + Onay Modalı ── */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteModalOpen(true)}
              className="gap-2 text-red-600 border-red-200 dark:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-950/30 hover:border-red-300 transition-colors"
            >
              <Trash2 size={14} />
              Sil
            </Button>

            <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <div className="flex items-center gap-3 mb-1">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-100 dark:bg-red-950/40 shrink-0">
                      <Trash2 size={18} className="text-red-600 dark:text-red-400" />
                    </div>
                    <DialogTitle className="text-lg font-bold text-[#17171c] dark:text-white">
                      Araştırmayı Sil
                    </DialogTitle>
                  </div>
                  <DialogDescription className="text-sm text-[#616161] dark:text-[#93939f] leading-relaxed pl-[52px]">
                    <span className="font-semibold text-[#212121] dark:text-[#e5e7eb]">&ldquo;{metadata?.title || "Bu araştırma"}&rdquo;</span>{" "}
                    listeden kaldırılacak ve bir daha göremeyeceksiniz.
                  </DialogDescription>
                </DialogHeader>

                <div className="my-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40">
                  <p className="text-xs text-amber-700 dark:text-amber-400 font-medium">
                    Araştırma listeden kaldırılır. Bu işlem geri alınamaz.
                  </p>
                </div>

                <DialogFooter className="gap-2 sm:gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setDeleteModalOpen(false)}
                    disabled={deleting}
                    className="flex-1"
                  >
                    Vazgeç
                  </Button>
                  <Button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white border-0 gap-2"
                  >
                    {deleting ? (
                      <><Loader2 size={14} className="animate-spin" /> Siliniyor...</>
                    ) : (
                      <><Trash2 size={14} /> Evet, Kalıcı Olarak Sil</>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

          </div>
        </div>
      </div>

      {/* 🔮 Interactive Tabs Grid */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 bg-[#eeece7] dark:bg-[#212121] p-1.5 rounded-xl border border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)]">
        <button 
          onClick={() => setActiveTab("summary")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "summary" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]" 
              : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
          }`}
        >
          <FileText size={16} />
          Özet & Hedefler
        </button>

        <button 
          onClick={() => setActiveTab("personas")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "personas" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]" 
              : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
          }`}
        >
          <Users size={16} />
          Personalar ({personas.length})
        </button>

        <button 
          onClick={() => setActiveTab("script")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "script" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]" 
              : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
          }`}
        >
          <ListTodo size={16} />
          Senaryo
        </button>

        <button 
          onClick={() => setActiveTab("interviews")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "interviews" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]" 
              : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
          }`}
        >
          <MessageSquare size={16} />
          Mülakat Kayıtları ({interviews.length})
        </button>

        <button 
          onClick={() => setActiveTab("findings")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "findings" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]" 
              : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
          }`}
        >
          <Search size={16} />
          Kanıt Zinciri
        </button>

        <button 
          onClick={() => setActiveTab("report")}
          className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
            activeTab === "report" 
              ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]" 
              : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
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
                    <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg">
                      <span className="text-xs font-semibold text-muted-foreground block uppercase">Marka / Ürün</span>
                      <span className="font-bold text-[#212121] dark:text-[#e5e7eb]">{brief?.title || metadata?.title || "Belirtilmemiş"}</span>
                    </div>
                    {(brief?.category || metadata?.category) && (
                      <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg">
                        <span className="text-xs font-semibold text-muted-foreground block uppercase">Kategori</span>
                        <span className="font-bold text-[#212121] dark:text-[#e5e7eb]">{brief?.category || metadata?.category}</span>
                      </div>
                    )}
                    <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg sm:col-span-2">
                      <span className="text-xs font-semibold text-muted-foreground block uppercase">Fiyat Modeli</span>
                      <span className="font-bold text-[#212121] dark:text-[#e5e7eb] leading-relaxed">{brief?.expected_price || "Belirtilmedi"}</span>
                    </div>
                    {brief?.target_users && brief.target_users.length > 0 && (
                      <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg sm:col-span-2">
                        <span className="text-xs font-semibold text-muted-foreground block uppercase">Hedef Kitle</span>
                        <span className="font-medium text-[#616161] dark:text-[#e5e7eb] text-sm leading-relaxed">{brief.target_users.join(" · ")}</span>
                      </div>
                    )}
                    {brief?.competitors && brief.competitors.length > 0 && (
                      <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg sm:col-span-2">
                        <span className="text-xs font-semibold text-muted-foreground block uppercase">Rakipler</span>
                        <span className="font-medium text-[#616161] dark:text-[#e5e7eb] text-sm leading-relaxed">{brief.competitors.join(" · ")}</span>
                      </div>
                    )}
                    {brief?.success_metric && (
                      <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg">
                        <span className="text-xs font-semibold text-muted-foreground block uppercase">Başarı Kriteri</span>
                        <span className="font-medium text-[#616161] dark:text-[#e5e7eb] text-sm leading-relaxed">{brief.success_metric}</span>
                      </div>
                    )}
                    {brief?.sales_channel && (
                      <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg">
                        <span className="text-xs font-semibold text-muted-foreground block uppercase">Satış Kanalı</span>
                        <span className="font-medium text-[#616161] dark:text-[#e5e7eb] text-sm leading-relaxed">{brief.sales_channel}</span>
                      </div>
                    )}
                    {(brief?.panel_size || brief?.geography) && (
                      <div className="p-3.5 bg-[#f5f4f1] border border-border rounded-lg sm:col-span-2">
                        <span className="text-xs font-semibold text-muted-foreground block uppercase">Panel & Coğrafya</span>
                        <span className="font-medium text-[#616161] dark:text-[#e5e7eb] text-sm leading-relaxed">{[brief?.panel_size, brief?.geography].filter(Boolean).join(" · ")}</span>
                      </div>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-muted-foreground uppercase block">Araştırma Problemi (Brief Context)</span>
                    <p className="text-[#616161] text-sm leading-relaxed bg-[#f5f4f1]/50 border border-border/60 p-4 rounded-xl">
                      {brief?.idea || "Brief bağlamı girilmemiş."}
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
                        <p className="text-[#212121] text-sm font-medium bg-[#f5f4f1] p-4 rounded-xl border border-border">
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
                              <span className="text-[#616161] ">{ass}</span>
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
                      <span className="text-[#93939f] font-semibold text-xl">/100</span>
                      <Badge className="ml-2 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 hover:bg-emerald-50 border border-emerald-200">
                        Sınıf: {metadata.quality_grade || "A"}
                      </Badge>
                    </div>
                    {metadata.quality_summary && (
                      <p className="text-[#616161] text-xs leading-relaxed border-t border-border pt-3">
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
                            label: "Tekdüze Yanıt Kalıbı",
                            count: rq.straight_lining_count || 0,
                            color: "text-red-600 dark:text-red-400",
                            bg: "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900/40",
                          },
                          (rq.acquiescence_count || 0) > 0 && {
                            icon: "🟠",
                            label: "Aşırı Uzlaşmacılık",
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

              {/* RFI Card — Research Fidelity Index (tüm planlarda açık) */}
              <PlanGate currentPlan={clientPlan.plan_type} requiredPlan="Free" featureName="Araştırma Bütünlüğü (RFI)">
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
                  const validity = rq.valid ?? (rfi !== null ? rfi >= 0.65 : null);
                  const warnings = rq.warning_count ?? 0;
                  const phasesPassed = rq.phases_passed ?? [];
                  const phasesFlagged = rq.phases_flagged ?? [];
                  const flags = rq.flags ?? [];
                  const adversarialSummary = rq.interpretation ?? rq.summary ?? "";

                  const rfiColor = rfi === null ? "text-[#93939f]" : rfi >= 0.80 ? "text-emerald-600 dark:text-emerald-400" : rfi >= 0.65 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400";
                  const borderColor = rfi === null ? "border-l-[#d9d9dd]" : rfi >= 0.80 ? "border-l-emerald-500" : rfi >= 0.65 ? "border-l-amber-500" : "border-l-red-500";
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
                            className={validity === null
                              ? "bg-[#f5f4f1] text-[#616161] border border-[#d9d9dd]"
                              : validity
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200"
                              : "bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400 border border-red-200 dark:border-red-900/40"}
                          >
                            {validity === null ? "Ölçülmedi" : validity ? "Geçerli" : "Eşik Altı"}
                          </Badge>
                        </CardTitle>
                        <CardDescription className="text-[10px]">Bilimsel simülasyon temelli bütünlük ölçütü — yanıt kalitesi ve tutarlılık denetimi.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {rfi !== null && (
                          <div className="flex items-baseline gap-2">
                            <span className={`text-4xl font-black ${rfiColor}`}>{(rfi * 100).toFixed(1)}</span>
                            <span className="text-[#93939f] font-semibold">/100</span>
                            <span className="text-xs text-muted-foreground">eşik ≥65</span>
                          </div>
                        )}

                        {/* RFI Component Bar Chart */}
                        {Object.keys(components).length > 0 && (
                          <div className="space-y-2 border-t border-border pt-3">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase">Bileşen Profili</p>
                            {Object.entries(components).map(([key, val]) => (
                              <div key={key} className="flex items-center gap-2">
                                <span className="text-[10px] font-semibold text-[#616161] w-28 shrink-0">{COMPONENT_LABELS[key] ?? key}</span>
                                <div className="flex-1 bg-[#eeece7] rounded-full h-2 overflow-hidden">
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
                                <Badge key={ph} className="text-[10px] bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400 border border-emerald-200">
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
                                {f.message}
                              </div>
                            ))}
                          </div>
                        )}

                        {adversarialSummary && (
                          <p className="text-[10px] text-[#616161] border-t border-border pt-2 leading-relaxed">
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
              <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Sentetik Kitle Paneli ({personas.length})</h2>
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
                      <div className="p-6 bg-[#f5f4f1]/50 border-b border-border/50 flex justify-between items-start gap-2">
                        <div className="space-y-0.5">
                          <h3 className="font-bold text-lg text-[#17171c] dark:text-white group-hover:text-[#1863dc] dark:group-hover:text-[#4c6ee6] transition-colors">
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
                          <span className="text-[10px] font-bold text-[#93939f] uppercase tracking-wider block">Biyografi & Karakteristik</span>
                          <p className="text-[#616161] text-xs leading-relaxed italic line-clamp-3">
                            &quot;{persona.bio || persona.context}&quot;
                          </p>
                        </div>

                        {/* Slider indicators */}
                        <div className="space-y-3 border-t border-border pt-4">
                          {persona.big_five ? (
                            <>
                              <span className="text-[10px] font-bold text-[#93939f] uppercase tracking-wider block mb-2">Kişilik Profili (Büyük Beşli)</span>
                              <BigFiveRadar bigFive={persona.big_five || {}} />
                              {[
                                { label: "Açıklık (Openness)",      value: persona.big_five?.Openness      ?? persona.big_five?.openness      ?? 50, color: "bg-sky-500" },
                                { label: "Sorumluluk (Conscientiousness)", value: persona.big_five?.Conscientiousness ?? persona.big_five?.conscientiousness ?? 50, color: "bg-blue-500" },
                                { label: "Dışadönüklük (Extraversion)",    value: persona.big_five?.Extraversion    ?? persona.big_five?.extraversion    ?? 50, color: "bg-orange-500" },
                                { label: "Uyumluluk (Agreeableness)",      value: persona.big_five?.Agreeableness   ?? persona.big_five?.agreeableness   ?? 50, color: "bg-teal-500" },
                                { label: "Duygusal Denge (Neuroticism)",   value: persona.big_five?.Neuroticism     ?? persona.big_five?.neuroticism     ?? 50, color: "bg-rose-500" },
                              ].map(trait => (
                                <div key={trait.label} className="space-y-1">
                                  <div className="flex justify-between text-[10px] font-semibold">
                                    <span className="text-muted-foreground">{trait.label}</span>
                                    <span className="text-[#212121] ">{trait.value}%</span>
                                  </div>
                                  <div className="h-1.5 w-full bg-[#eeece7] rounded-full overflow-hidden">
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
                                  <span className="text-[#212121] ">{persona.price_sensitivity}/5</span>
                                </div>
                                <div className="h-1.5 w-full bg-[#eeece7] rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-sky-500 rounded-full" 
                                    style={{ width: `${(persona.price_sensitivity / 5) * 100}%` }}
                                  />
                                </div>
                              </div>
                              <div className="space-y-1">
                                <div className="flex justify-between text-[10px] font-semibold">
                                  <span className="text-muted-foreground">Dijital Güven</span>
                                  <span className="text-[#212121] ">{persona.digital_confidence}/5</span>
                                </div>
                                <div className="h-1.5 w-full bg-[#eeece7] rounded-full overflow-hidden">
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
                            <Badge variant="outline" className="font-semibold text-[#616161] ">
                              {STANCE_TR[persona.stance] || persona.stance}
                            </Badge>
                          </div>
                          {(persona.ses_group || persona.respondent_type) && (
                            <div className="flex flex-wrap gap-1.5">
                              {persona.ses_group && (
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                  persona.ses_group === "AB" ? "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/20 dark:border-amber-800 dark:text-amber-400" :
                                  persona.ses_group === "C1" ? "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/20 dark:border-blue-800 " :
                                  persona.ses_group === "C2" ? "bg-[#f5f4f1] border-[#d9d9dd] text-[#616161] " :
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

                        {persona.attributes && ["Current workflow", "Decision trigger", "Buying friction"].some(k => persona.attributes?.[k]) && (
                          <div className="space-y-2 border-t border-border/50 pt-3">
                            {[
                              { key: "Current workflow", label: "Mevcut İş Akışı" },
                              { key: "Decision trigger", label: "Karar Tetikleyicisi" },
                              { key: "Buying friction", label: "Satın Alma Sürtünmesi" },
                            ].filter(a => persona.attributes?.[a.key]).map(a => (
                              <div key={a.key} className="text-[11px] leading-relaxed">
                                <span className="font-bold text-[#93939f] uppercase tracking-wider">{a.label}: </span>
                                <span className="text-[#616161] dark:text-[#93939f]">{persona.attributes?.[a.key]}</span>
                              </div>
                            ))}
                          </div>
                        )}
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
                  <CardTitle className="text-base">Sosyo-Ekonomik Grup × Duruş</CardTitle>
                  <CardDescription>Sosyo-ekonomik gruplara göre pazar yaklaşımı dağılımı.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left py-2 pr-4 text-xs font-semibold text-muted-foreground uppercase">SES</th>
                          {["Innovator","EarlyAdopter","Mainstream","Laggard","Skeptic"].map(s => (
                            <th key={s} className="text-center py-2 px-2 text-xs font-semibold text-muted-foreground uppercase">{STANCE_TR[s] || s}</th>
                          ))}
                          <th className="text-center py-2 pl-4 text-xs font-semibold text-muted-foreground uppercase">Toplam</th>
                          <th className="text-left py-2 pl-4 text-xs font-semibold text-muted-foreground uppercase">Baskın</th>
                        </tr>
                      </thead>
                      <tbody>
                        {study.ses_cross_tab.map(row => (
                          <tr key={row.ses_group} className="border-b border-border/50 hover:bg-[#f5f4f1] dark:hover:bg-[#212121]/30">
                            <td className="py-2 pr-4">
                              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                                row.ses_group === "AB" ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400" :
                                row.ses_group === "C1" ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 " :
                                row.ses_group === "C2" ? "bg-[#eeece7] text-[#616161] " :
                                "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400"
                              }`}>{row.ses_group}</span>
                            </td>
                            {["Innovator","EarlyAdopter","Mainstream","Laggard","Skeptic"].map(s => {
                              const sc = row.stance_counts as Record<string,number>;
                              const count = sc?.[s] ?? 0;
                              const max = sc ? Math.max(...Object.values(sc)) : 0;
                              return (
                                <td key={s} className="text-center py-2 px-2">
                                  {count > 0 ? (
                                    <span
                                      className="inline-flex w-8 h-8 rounded-md text-xs font-bold items-center justify-center transition-colors"
                                      style={{
                                        backgroundColor: count === max ? "#1863dc" : `rgba(24, 99, 220, ${0.15 + (count / max) * 0.55})`,
                                        color: count === max ? "#ffffff" : "#17171c",
                                      }}
                                    >{count}</span>
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
                          <span className="font-semibold text-sm text-[#212121] dark:text-[#e5e7eb]">{rt.label}</span>
                          <Badge variant="secondary" className="text-xs">{rt.count} kişi</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Ort. fiyat hassasiyeti: <strong className="text-[#616161] ">{rt.avg_price_sensitivity.toFixed(1)}/10</strong>
                        </div>
                        {rt.top_pain && (
                          <div className="text-xs bg-rose-50 dark:bg-rose-950/20 border border-rose-100 rounded-lg p-2 text-rose-700 dark:text-rose-400 italic line-clamp-2">
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
              <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Mülakat Transkriptleri</h2>
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
                        <Badge variant="outline" className="text-[10px] bg-[#f5f4f1] dark:bg-[#212121]">{item.turns?.length} Soru</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="p-5 pt-0 space-y-4">
                      <div className="text-xs text-muted-foreground flex items-center justify-between">
                        <span>Durum:</span>
                        <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-400">Mülakat Tamamlandı</Badge>
                      </div>
                      <Dialog>
                        <DialogTrigger render={
                          <Button variant="outline" className="w-full text-xs font-semibold gap-2 border-[#d9d9dd] hover:bg-[#f5f4f1] text-[#17171c] dark:border-[rgba(255,255,255,0.12)] dark:text-white dark:hover:bg-[#2c2c33]">
                            <MessageSquare size={14} />
                            Transkript Görüntüle
                          </Button>
                        } />
                        <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col p-0 overflow-hidden rounded-2xl">
                          <DialogHeader className="px-6 py-5 border-b border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)] bg-[#eeece7] dark:bg-[#212121]">
                            <DialogTitle className="text-lg">Mülakat Transkripti · {item.persona?.name}</DialogTitle>
                            <DialogDescription className="text-[#616161] dark:text-[#93939f]">
                              {item.persona?.role_title} · {item.persona?.age} Yaş · {item.persona?.city} · {STANCE_TR[item.persona?.stance || ""] || item.persona?.stance} Profil
                            </DialogDescription>
                          </DialogHeader>
                          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 bg-white dark:bg-[#17171c]">
                            {item.turns?.map((turn: InterviewTurn, turnIdx: number) => (
                              <div key={turnIdx} className="space-y-5 border-b border-[#f2f2f2] dark:border-[rgba(255,255,255,0.08)] pb-6 last:border-0 last:pb-0">
                                <div className="flex items-center gap-3">
                                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f]">Soru {turnIdx + 1}</span>
                                  <div className="h-px flex-1 bg-[#f2f2f2] dark:bg-[rgba(255,255,255,0.08)]" />
                                </div>

                                {/* Moderatör sorusu */}
                                <div className="flex items-start gap-3">
                                  <div className="h-8 w-8 rounded-full bg-[#003c33] dark:bg-[#edfce9] text-white dark:text-[#003c33] flex items-center justify-center shrink-0">
                                    <MessageSquare size={14} />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f] mb-1.5">Moderatör (AI)</p>
                                    <p className="text-[15px] leading-relaxed text-[#212121] dark:text-[#e5e7eb]">{turn.question}</p>
                                  </div>
                                </div>

                                {/* Persona yanıtı */}
                                <div className="flex items-start gap-3">
                                  <div className="h-8 w-8 rounded-full bg-[#ff7759] text-white flex items-center justify-center font-bold text-xs shrink-0">
                                    {item.persona?.name.charAt(0) || "P"}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f] mb-1.5">{item.persona?.name}</p>
                                    <p className="text-[15px] leading-relaxed text-[#212121] dark:text-[#e5e7eb]">{turn.answer}</p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          <DialogFooter className="px-6 py-4 border-t border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)] bg-[#f5f4f1]/60 dark:bg-[#212121] flex flex-col gap-3">
                            {(() => {
                              const followUpCount = (() => {
                                let count = 0;
                                study?.interviews?.forEach(inv => {
                                  inv.turns?.forEach(t => {
                                    if (t.tags?.includes("FOLLOW-UP")) {
                                      count++;
                                    }
                                  });
                                });
                                return count;
                              })();

                              const planType = clientPlan?.plan_type || "Free";
                              const isFree = planType === "Free";
                              const isLimited = planType === "Starter" || planType === "Flex";
                              const isLimitReached = isLimited && followUpCount >= 3;

                              let inputPlaceholder = `${item.persona?.name} isimli personaya ekstra bir soru sorun...`;
                              let isDisabled = sendingFollowUp;
                              let badgeText = "";
                              let badgeColor = "bg-[#eeece7] text-[#616161] dark:bg-[#2c2c33] dark:text-[#93939f]";

                              if (isFree) {
                                inputPlaceholder = "Takip sorusu · Flex+ planı gerektirir.";
                                isDisabled = true;
                                badgeText = "Takip Sorusu · Flex+ Gerekli";
                                badgeColor = "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/20 dark:text-red-400 dark:border-red-900/40";
                              } else if (isLimitReached) {
                                inputPlaceholder = "Takip sorusu limitine ulaştınız (3/3). Planınızı yükseltin.";
                                isDisabled = true;
                                badgeText = "Limit Doldu (3/3)";
                                badgeColor = "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-900/40";
                              } else if (isLimited) {
                                badgeText = `Takip Sorusu Limiti: ${followUpCount}/3`;
                                badgeColor = "bg-[#f1f5ff] text-[#1863dc] border-[#e5e7eb] dark:bg-[#071829] dark:text-[#4c6ee6] dark:border-[rgba(24,99,220,0.15)]";
                              } else {
                                badgeText = "Sınırsız Takip Sorusu";
                                badgeColor = "bg-[#edfce9] text-[#003c33] border-[#d9d9dd] dark:bg-[#003c33]/20 dark:text-[#edfce9] dark:border-[#003c33]/40";
                              }

                              return (
                                <div className="w-full space-y-3">
                                  <div className="flex items-center justify-between gap-3">
                                    <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f]">Persona ile Etkileşim (Probing)</span>
                                    <Badge variant="outline" className={`text-[11px] font-semibold ${badgeColor}`}>
                                      {badgeText}
                                    </Badge>
                                  </div>
                                  <div className="flex gap-2 w-full">
                                    <Textarea
                                      placeholder={inputPlaceholder}
                                      className="min-h-[60px] resize-none text-sm flex-1"
                                      value={followUpText}
                                      onChange={(e) => setFollowUpText(e.target.value)}
                                      disabled={isDisabled}
                                    />
                                    <Button
                                      onClick={() => handleFollowUp(item.persona.id)}
                                      disabled={isDisabled || !followUpText.trim()}
                                      className="h-auto px-6 font-semibold bg-[#17171c] hover:opacity-85 text-white"
                                    >
                                      {sendingFollowUp ? <Loader2 className="animate-spin w-4 h-4" /> : "Sor"}
                                    </Button>
                                  </div>
                                  <span className="text-[11px] text-[#93939f]">Bu özellik ile personaya mülakat sonrası ek soru yöneltip daha derin içgörü elde edebilirsiniz.</span>
                                </div>
                              );
                            })()}
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
              <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Mülakat Senaryosu</h2>
              <p className="text-muted-foreground text-sm">Yapay zeka moderatörünün personalara yönelttiği ana sorular.</p>
            </div>

            {(!plan?.interview_questions || plan.interview_questions.length === 0) ? (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
                Bu araştırmaya ait senaryo kaydı bulunamadı.
              </div>
            ) : (
              <Card className="shadow-sm border-[#e5e7eb] dark:border-[rgba(24,99,220,0.15)] overflow-hidden">
                <CardHeader className="bg-[#f5f4f1]/50 dark:bg-[#212121]/50 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base">Mülakat Akışı</CardTitle>
                      <CardDescription>Toplam {plan.interview_questions.length} soru kalıbı kullanıldı.</CardDescription>
                    </div>
                    <Badge variant="outline" className="bg-white dark:bg-[#17171c]">
                      Salt Okunur (Read-Only)
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="divide-y divide-border/60">
                    {plan.interview_questions.map((q: string, i: number) => (
                      <div key={i} className="flex gap-4 p-5 hover:bg-[#f5f4f1] dark:hover:bg-[#212121]/30 transition-colors">
                        <div className="h-6 w-6 rounded-full bg-[#f1f5ff] dark:bg-[#071829] text-[#1863dc] dark:text-[#4c6ee6] flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                          {i + 1}
                        </div>
                        <div className="space-y-2 flex-1">
                          <p className="text-sm font-medium text-[#212121] dark:text-[#e5e7eb] leading-relaxed">{q}</p>
                          <div className="flex gap-2">
                            <Badge variant="secondary" className="text-[10px] bg-[#eeece7] dark:bg-[#2c2c33] text-[#616161]">Açık Uçlu Soru</Badge>
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

        {/* ==================== Tab: Findings (Kanıt Zinciri) ==================== */}
        {activeTab === "findings" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Kanıt Zinciri ve Karar Katmanı</h2>
              <p className="text-muted-foreground text-sm">Mülakatlardan çıkarılan bulgular, kanıt alıntıları ve karar sinyalleri.</p>
            </div>

            {(!study?.findings || study.findings.length === 0) ? (
              <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
                <p>Bu araştırmaya ait kanıt zinciri verisi bulunamadı.</p>
                <p className="text-xs mt-2 text-muted-foreground/70">Sentez raporu oluşturulduktan sonra bulgular ve kanıt zinciri burada görüntülenecektir.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Decision Items Summary */}
                {study?.decision_items && study.decision_items.length > 0 && (
                  <Card className="shadow-sm border-[#003c33]/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Zap size={18} className="text-amber-500" />
                        Karar Önerileri
                      </CardTitle>
                      <CardDescription>Kanıt zincirinden türetilen aksiyon önerileri.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {study.decision_items.map((di, i) => {
                        const dc = DECISION_CONFIG[di.signal] || DECISION_CONFIG.INVESTIGATE;
                        const DcIcon = dc.icon;
                        return (
                          <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${dc.bg}`}>
                            <DcIcon size={16} className={`shrink-0 mt-0.5 ${dc.color}`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-semibold text-sm text-[#212121]">{di.title}</span>
                                <Badge className={`text-[10px] ${dc.bg} ${dc.color}`}>{dc.label}</Badge>
                              </div>
                              <p className="text-xs text-muted-foreground mt-1">{di.recommended_action}</p>
                              <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground">
                                <span>Güven: %{Math.round(di.confidence * 100)}</span>
                                <span className="text-emerald-600">Destekleyen: {di.supporting_count}</span>
                                <span className="text-red-500">İtiraz: {di.refuting_count}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </CardContent>
                  </Card>
                )}

                {/* Findings List */}
                {study.findings.map((finding) => {
                  const dc = DECISION_CONFIG[finding.decision_signal] || DECISION_CONFIG.INVESTIGATE;
                  const DcIcon = dc.icon;
                  const confPct = Math.round(finding.confidence * 100);
                  const barColor = confPct >= 75 ? "bg-emerald-500" : confPct >= 50 ? "bg-amber-500" : "bg-red-500";

                  return (
                    <FindingCard key={finding.id} finding={finding} dc={dc} DcIcon={DcIcon} confPct={confPct} barColor={barColor} />
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ==================== Tab 4: Synthesis Report ==================== */}
        {activeTab === "report" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div>
              <h2 className="text-xl font-bold text-[#17171c] dark:text-white">Yapay Zeka Sentez Raporu</h2>
              <p className="text-muted-foreground text-sm">Sentetik mülakatlardan elde edilen pazar analizleri, itirazlar ve ürün geliştirme tavsiyeleri.</p>
            </div>

            {/* Öne çıkan sayılar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Persona", value: personas.length },
                { label: "Mülakat Yanıtı", value: interviews.reduce((acc, iv) => acc + (iv.turns?.length || 0), 0) },
                { label: "Bulgu", value: study?.findings?.length ?? 0 },
                { label: "Öneri", value: study?.recommendations?.length ?? 0 },
              ].map(s => (
                <div key={s.label} className="rounded-xl border border-[#d9d9dd] bg-white dark:bg-[#212121] p-4 text-center">
                  <div className="text-3xl font-black text-[#003c33] dark:text-[#edfce9]">{s.value}</div>
                  <div className="text-[11px] font-mono uppercase tracking-wider text-[#93939f] mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Rapor metrikleri + veri kökeni (S3) */}
            {study?.report_metrics && (study.report_metrics.findings_total ?? 0) > 0 && (
              <div className="rounded-xl border border-[#d9d9dd] bg-[#f5f4f1]/40 dark:bg-[#212121]/40 p-4 space-y-3">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#93939f]">Rapor Metrikleri</span>
                  <span className="text-[10px] text-[#93939f]">Yönlendirici hipotez — istatistiksel temsil iddiası taşımaz</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "Kanıtlı Bulgu", value: `${study.report_metrics.findings_with_evidence ?? 0}/${study.report_metrics.findings_total ?? 0}` },
                    { label: "Bulgu Başına Kanıt", value: study.report_metrics.evidence_per_finding ?? 0 },
                    { label: "Kanıtta Persona", value: study.report_metrics.unique_personas_in_evidence ?? 0 },
                    { label: "Karşı Kanıt Oranı", value: study.report_metrics.refuting_ratio ?? 0 },
                    { label: "Yanıt Tamamlama", value: study.report_metrics.answer_completion_rate ?? 0 },
                    { label: "Harici Kaynak", value: study.report_metrics.external_evidence_count ?? 0 },
                    { label: "Kaynaksız Bulgu", value: study.report_metrics.unsourced_findings ?? 0 },
                  ].map(m => (
                    <div key={m.label} className="rounded-lg border border-[#d9d9dd]/70 bg-white dark:bg-[#17171c] px-3 py-2">
                      <div className="text-lg font-black text-[#003c33] dark:text-[#edfce9]">{m.value}</div>
                      <div className="text-[10px] font-mono uppercase tracking-wider text-[#93939f]">{m.label}</div>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2 text-[10px]">
                  <span className="px-2 py-0.5 rounded-full border border-[#d9d9dd] text-[#616161] dark:text-[#93939f]">Sentetik: persona mülakatları</span>
                  <span className="px-2 py-0.5 rounded-full border border-[#d9d9dd] text-[#616161] dark:text-[#93939f]">Algoritmik: PSM / SES / kalite</span>
                  <span className="px-2 py-0.5 rounded-full border border-[#d9d9dd] text-[#616161] dark:text-[#93939f]">Harici: web doğrulama</span>
                </div>
              </div>
            )}

            {!isCompleted ? (
              <div className="text-center py-16 text-muted-foreground border border-dashed border-border rounded-xl bg-[#f5f4f1]/50">
                Bu araştırma henüz tamamlanmamış veya nihai sentez raporu üretilmemiş.
              </div>
            ) : clientPlan.plan_type === "Free" ? (
              <div className="space-y-4">
                {/* Teaser: Executive Summary clearly visible */}
                {study.report_markdown && (
                  <Card className="shadow-sm border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/30 dark:bg-emerald-950/10">
                    <CardContent className="p-5">
                      <p className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase mb-2">Önizleme</p>
                      <div className="text-sm text-[#616161] dark:text-[#e5e7eb] leading-relaxed line-clamp-4">
                        {study.report_markdown.split('\n').slice(0, 8).map((line, i) => <p key={i} className="my-1">{line}</p>)}
                      </div>
                    </CardContent>
                  </Card>
                )}
                {/* Blurred full report + gradient CTA */}
                <div className="relative rounded-2xl overflow-hidden border border-[#d9d9dd]">
                  <div className="filter blur-md pointer-events-none select-none opacity-20 p-6 space-y-4">
                    {study.report_markdown && study.report_markdown.split('\n').slice(8, 30).map((line, i) => (
                      <div key={i} className="h-3 bg-[#93939f] rounded" style={{width: `${70 + ((i * 13) % 30)}%`}} />
                    ))}
                  </div>
                  <div className="absolute inset-x-0 bottom-0 flex flex-col items-center pb-6 pt-24"
                    style={{background: "linear-gradient(to top, white 0%, white 50%, transparent 100%)"}}>
                    <div className="text-center space-y-3 max-w-sm px-4">
                      <Lock className="mx-auto text-amber-600" size={18} />
                      <h3 className="text-base font-black text-[#212121]">Raporun Tamamını Gör</h3>
                      <p className="text-xs text-muted-foreground">Fiyat analizi, kanıt zinciri ve karar önerileri seni bekliyor.</p>
                      <Link href="/client/upgrade" className="inline-flex w-full">
                        <Button className="w-full bg-[#003c33] hover:bg-[#003c33]/90 text-white font-semibold rounded-xl py-2.5 text-sm">
                          Planı Yükselt →
                        </Button>
                      </Link>
                      <p className="text-[10px] text-muted-foreground">2 araştırma hakkı veya 1 ay · Tam rapor için plan gerekir</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Van Westendorp PSM Card (Tüm planlar) */}
                <PlanGate currentPlan={clientPlan.plan_type} requiredPlan="Free" featureName="Van Westendorp Fiyat Analizi">
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
                              <span className="text-xs font-bold text-[#616161] w-24 shrink-0">{brand}</span>
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
                  <Card className="shadow-sm border-emerald-100/30">
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

                {/* External Evidence Verification */}
                {study?.external_evidence && study.external_evidence.length > 0 && (
                  <Card className="shadow-sm border-[#003c33]/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Globe size={16} className="text-[#1863dc]" />
                        Harici Kanıt Doğrulaması
                      </CardTitle>
                      <CardDescription>Açık web ve literatür taraması ile bulguların teyit edilmesi.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {study.external_evidence.map((ev, i) => (
                        <div key={i} className="flex gap-3 items-start p-3 bg-[#f5f4f1] rounded-lg border border-border/60">
                          <Globe size={14} className="shrink-0 mt-0.5 text-[#93939f]" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-sm text-[#212121]">{ev.source_title}</span>
                              <Badge variant="outline" className="text-[10px]">{ev.relevance}</Badge>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{ev.snippet}</p>
                            {ev.source_url && (
                              <a href={ev.source_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-[#1863dc] hover:underline mt-1 inline-block">
                                Kaynağa Git →
                              </a>
                            )}
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Research Copilot Chat */}
                <Card className="shadow-sm border-[#003c33]/20">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <MessageSquare size={16} className="text-[#1863dc]" />
                      Araştırma Asistanı
                    </CardTitle>
                    <CardDescription>Raporla ilgili sorular sorun</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 max-h-60 overflow-y-auto mb-3">
                      {chatMessages.length === 0 && (
                        <p className="text-xs text-muted-foreground text-center py-3">
                          Rapordaki bulgular, personalar veya öneriler hakkında soru sorabilirsiniz.
                        </p>
                      )}
                      {chatMessages.map((msg, i) => (
                        <div
                          key={i}
                          className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-[85%] p-2.5 rounded-xl text-xs leading-relaxed ${
                              msg.role === "user"
                                ? "bg-[#1863dc] text-white rounded-br-sm"
                                : "bg-[#eeece7] text-[#616161] rounded-bl-sm"
                            }`}
                          >
                            {msg.content}
                          </div>
                        </div>
                      ))}
                      {sendingChat && (
                        <div className="flex justify-start">
                          <div className="bg-[#eeece7] text-[#93939f] p-2.5 rounded-xl rounded-bl-sm text-xs">
                            <Loader2 size={14} className="animate-spin inline mr-1.5" />
                            Düşünüyor...
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") sendChat(); }}
                        placeholder="Örn: Şüpheciler neden reddetti?"
                        className="text-sm"
                        disabled={sendingChat}
                      />
                      <Button
                        onClick={sendChat}
                        disabled={!chatInput.trim() || sendingChat}
                        size="sm"
                        className="shrink-0 bg-[#17171c] text-white hover:opacity-85 dark:bg-[#ffffff] dark:text-[#17171c]"
                      >
                        {sendingChat ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                        <span className="ml-1.5 hidden sm:inline">Gönder</span>
                      </Button>
                    </div>
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
