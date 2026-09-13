"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { getAuthHeaders } from "@/lib/auth";
import {
  Loader2, Send, User, ChevronRight,
  FileText, Target, Users, DollarSign, Layers,
  FlaskConical, BarChart2, CheckCircle2, Lock
} from "lucide-react";
import { useClientPlan } from "@/hooks/use-client-plan";
import Link from "next/link";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface Brief {
  title?: string;
  market?: string;
  category?: string;
  idea?: string;
  target_users?: string | string[];
  questions?: string | string[];
  competitors?: string | string[];
  expected_price?: string;
  sales_channel?: string;
  success_metric?: string;
  variant_a?: string;
  variant_b?: string;
}

/** Backend bazen string, bazen string[] döner — her ikisini de handle eder */
const toArray = (val: string | string[] | undefined): string[] => {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  return [val];
};

// ─── Brief Preview Card ───────────────────────────────────────────────────────

function renderBriefValue(value: unknown) {
  if (!value) return null;
  const strValue = Array.isArray(value) ? value.join(", ") : typeof value === "string" ? value : JSON.stringify(value);
  // Numbered list detection: "1. xxx 2. xxx" or newline-separated
  const numbered = strValue.split(/(?=\d+\.\s)/).map(s => s.replace(/^\d+\.\s*/, "").trim()).filter(Boolean);
  if (numbered.length > 1) {
    return (
      <ul className="space-y-1 mt-0.5">
        {numbered.map((item, i) => (
          <li key={i} className="flex gap-1.5 text-xs text-[#212121] font-medium leading-relaxed">
            <span className="text-[#ff7759] shrink-0 mt-px">·</span>
            <span className="break-words">{item}</span>
          </li>
        ))}
      </ul>
    );
  }
  return <div className="text-xs text-[#212121] font-medium leading-relaxed break-words whitespace-pre-wrap">{strValue}</div>;
}

function BriefPreview({ brief, mode, onToggleMobile }: { brief: Brief; mode: "research" | "ab_test"; onToggleMobile?: () => void }) {
  const fields = mode === "ab_test"
    ? [
      { icon: FileText, label: "Başlık", value: brief.title },
      { icon: Target, label: "Ürün Fikri", value: brief.idea },
      { icon: Layers, label: "Varyant A", value: brief.variant_a },
      { icon: Layers, label: "Varyant B", value: brief.variant_b },
      { icon: Users, label: "Hedef Kitle", value: toArray(brief.target_users).join(", ") || undefined },
      { icon: CheckCircle2, label: "Başarı Kriteri", value: brief.success_metric },
    ]
    : [
      { icon: FileText, label: "Başlık", value: brief.title },
      { icon: Target, label: "Ürün Fikri", value: brief.idea },
      { icon: Users, label: "Hedef Kitle", value: toArray(brief.target_users).join(", ") || undefined },
      { icon: DollarSign, label: "Fiyat Modeli", value: brief.expected_price },
      { icon: Layers, label: "Rakipler", value: toArray(brief.competitors).join(", ") || undefined },
      { icon: CheckCircle2, label: "Başarı Kriteri", value: brief.success_metric },
    ];

  const filled = fields.filter(f => f.value && f.value.length > 0).length;
  const total = fields.length;
  const pct = Math.round((filled / total) * 100);

  return (
    <Card className="sticky top-6 shadow-sm border-[#d9d9dd] ">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold text-[#003c33] flex items-center gap-2">
            <FileText size={14} />
            Canlı Brief Özeti
          </CardTitle>
          {onToggleMobile && (
            <button onClick={onToggleMobile} className="lg:hidden text-xs text-[#003c33] font-bold flex items-center gap-1 bg-[#edfce9] px-2 py-1 rounded-md">
              Sohbete Dön
            </button>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1.5 bg-[#eeece7]  rounded-full overflow-hidden">
            <div
              className="h-full bg-[#003c33] rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs font-bold text-[#ff7759]/80 tabular-nums">{pct}%</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {fields.map(({ icon: Icon, label, value }) => (
          <div key={label} className={`flex gap-2 p-2 rounded-lg transition-colors ${value ? "bg-[#edfce9]/50 " : "bg-transparent grayscale"}`}>
            <Icon size={13} className={value ? "text-[#ff7759] shrink-0 mt-0.5" : "text-[#93939f] shrink-0 mt-0.5"} />
            <div className="min-w-0 flex-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide">{label}</div>
              {value
                ? renderBriefValue(value)
                : <div className="text-xs text-[#93939f] italic">Henüz doldurulmadı</div>
              }
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

// ── Araştırma isteği: async job (tercih) → senkron fallback ──

const RESEARCH_POLL_INTERVAL_MS = 2000;
const RESEARCH_POLL_TIMEOUT_MS = 6 * 60 * 1000;

type ResearchResult = {
  plan?: unknown;
  personas?: unknown[];
  interviews?: unknown[];
};

async function pollResearchJob(
  jobId: string,
  apiBase: string,
  headers: Record<string, string>,
): Promise<ResearchResult> {
  const startedAt = Date.now();
  while (Date.now() - startedAt < RESEARCH_POLL_TIMEOUT_MS) {
    await new Promise((resolve) => setTimeout(resolve, RESEARCH_POLL_INTERVAL_MS));
    const res = await fetch(`${apiBase}/api/client/research/jobs/${jobId}`, { headers });
    if (!res.ok) continue;

    const data = await res.json();
    if (data.status === "completed") return data.result as ResearchResult;
    if (data.status === "failed") {
      throw new Error(data.error || "Araştırma tamamlanamadı.");
    }
  }
  throw new Error("Araştırma zaman aşımına uğradı. Lütfen tekrar deneyin.");
}

/**
 * Araştırmayı önce async job olarak dener (API threadpool'unu meşgul etmez);
 * arka plan işleyicisi yoksa (yerel geliştirme) senkron endpoint'e düşer.
 */
async function requestResearch(payload: Record<string, unknown>): Promise<ResearchResult> {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
  const headers = { "Content-Type": "application/json", ...getAuthHeaders() };

  const jobRes = await fetch(`${apiBase}/api/client/research/jobs`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (jobRes.ok) {
    const jobData = await jobRes.json().catch(() => ({}));
    if (jobData?.job_id) {
      return pollResearchJob(jobData.job_id, apiBase, headers);
    }
    if (jobData?.plan) return jobData as ResearchResult;
  } else if (![503, 404, 405].includes(jobRes.status)) {
    const errData = await jobRes.json().catch(() => ({}));
    const detail = errData?.detail;
    throw new Error(
      typeof detail === "string" ? detail : detail?.message || `Sunucu hatası: ${jobRes.status}`,
    );
  }

  // Senkron fallback
  const res = await fetch(`${apiBase}/api/client/research`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    const detail = errData?.detail;
    throw new Error(
      typeof detail === "string" ? detail : detail?.message || `Sunucu hatası: ${res.status}`,
    );
  }
  return (await res.json()) as ResearchResult;
}

export default function NewResearchWizard() {
  const router = useRouter();
  const { plan } = useClientPlan();
  const abTestLocked = !plan?.features?.ab_test;

  const [researchMode, setResearchMode] = useState<"research" | "ab_test">("research");
  const [stage, setStage] = useState<"mode" | "chat" | "simulating">("mode");
  const [showMobileBrief, setShowMobileBrief] = useState(false);

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [brief, setBrief] = useState<Brief>({});
  const [isReady, setIsReady] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (plan?.trial_expired) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] p-4 text-center max-w-md mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div className="h-16 w-16 rounded-full bg-amber-50 flex items-center justify-center shadow-sm border border-amber-200">
          <Lock size={32} className="text-amber-800" />
        </div>
        <div className="space-y-3">
          <h1 className="text-2xl font-black tracking-tight text-[#17171c]">Trial Expired (Deneme Süreniz Doldu)</h1>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Every plan comes with a 1-month free trial and 2 free researches — no credit card required. You get access to the platform so you can run real research and see the output before committing.
          </p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            After 3 days or 2 researches (whichever comes first), you’ll be asked to choose a plan. Your research reports and data stay accessible for 30 days — after that, access is limited. Pick a plan to keep everything unlocked.
          </p>
        </div>
        <Link href="/client/upgrade" className="w-full">
          <Button className="w-full bg-[#17171c] hover:opacity-85 text-white font-semibold rounded-xl h-12 text-sm">
            Upgrade Now / Plan Seçin →
          </Button>
        </Link>
      </div>
    );
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: userMsg }];
    setMessages(nextMessages);
    setLoading(true);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
    try {
      const res = await fetch(`${API_BASE}/api/client/intake`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          current_brief: brief,
          chat_history: nextMessages.map(m => ({ role: m.role, content: m.content })),
          user_message: userMsg,
          app_mode: researchMode,
        }),
      });

      if (!res.ok) {
        let errorMsg = "Defne yanıt vermedi.";
        try {
          const errData = await res.json();
          if (errData.detail) errorMsg = errData.detail;
        } catch (e) {}
        throw new Error(errorMsg);
      }
      const data = await res.json();

      const reply: string = data.assistant_reply || "Anladım, devam edebiliriz.";
      const updatedBrief: Brief = data.updated_brief || brief;

      setBrief(updatedBrief);
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);

      // Detect ready signal
      if (data.is_complete || reply.includes("butona tıklayarak") || reply.includes("başlatmaya hazırız") || reply.includes("butona basabilirsin") || reply.includes("başlatmaya hazırım")) {
        setIsReady(true);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Bir hata oluştu.";
      toast.error(msg);
      setMessages(prev => [...prev, { role: "assistant", content: `⚠️ ${msg}` }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleStartResearch = async () => {
    if (!brief.idea && !brief.title) {
      toast.error("Brief henüz tamamlanmadı.");
      return;
    }
    
    setStage("simulating");
    const username = typeof window !== "undefined" ? localStorage.getItem("clarere_username") : null;
    
    try {
      const data = await requestResearch({
        category: brief.category || "genel",
        title: brief.title || "Araştırma",
        context: brief.idea || brief.title || "",
        brand: "",
        budget: "",
        target_users: toArray(brief.target_users),
        competitors: toArray(brief.competitors),
        expected_price: brief.expected_price || undefined,
        success_metric: brief.success_metric || undefined,
        respondent_types: [],
        discovery_channels: [],
        intake_brief: brief,
        panel_size: 5,
      });

      // Save as study
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
      const studyRes = await fetch(`${API_BASE}/api/client/studies`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          metadata: {
            id: `study_${Date.now()}`,
            title: brief.title || "Araştırma",
            market: "Türkiye",
            category: brief.category || "Genel",
            has_report: false,
            quality_score: 0,
            quality_grade: "N/A",
          },
          payload: {
            brief: brief,
            plan: data.plan,
            personas: data.personas,
            interviews: data.interviews,
          },
        }),
      });

      if (!studyRes.ok) {
        console.warn("Study save failed, redirecting anyway");
      } else {
        const study = await studyRes.json();
        toast.success("Araştırma tamamlandı!");
        router.push(`/client/studies/${study.id || `study_${Date.now()}`}`);
        return;
      }
      
      toast.success("Araştırma tamamlandı!");
      router.push("/client");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Araştırma başlatılamadı.";
      toast.error(msg);
      setStage("chat");
    }
  };

  // ── STEP 0: Mode Selection ──────────────────────────────────────────────────
  if (stage === "mode") {
    return (
      <div className="p-4 sm:p-8 max-w-2xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Yeni Araştırma</h1>
          <p className="text-muted-foreground mt-1">Araştırma türünü seçin — Defne sizi yönlendirecek.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => setResearchMode("research")}
            className={`flex flex-col gap-3 p-6 rounded-2xl border-2 transition-all text-left ${
              researchMode === "research"
                ? "border-[#17171c] bg-[#edfce9]/60  shadow-md"
                : "border-border hover:border-[#17171c] dark:hover:border-[#17171c] hover:shadow-sm"
            }`}
          >
            <div className={`p-2.5 rounded-xl w-fit ${researchMode === "research" ? "bg-[#edfce9] " : "bg-[#eeece7] "}`}>
              <BarChart2 size={22} className={researchMode === "research" ? "text-[#ff7759]" : "text-muted-foreground"} />
            </div>
            <div>
              <div className="font-bold text-base">Pazar Araştırması</div>
              <div className="text-sm text-muted-foreground mt-0.5">Ürün/hizmet fikri doğrulama, hedef kitle ve fiyat araştırması</div>
            </div>
            {researchMode === "research" && (
                            <Badge className="w-fit bg-[#17171c] hover:bg-[#17171c] text-white text-xs">Seçildi</Badge>
            )}
          </button>

          <button
            type="button"
            onClick={() => {
              if (abTestLocked) {
                toast.error(
                  "A/B Test Modu Flex planında kullanılabilir.",
                  { action: { label: "Planı Yükselt", onClick: () => router.push("/client/upgrade") } }
                );
                return;
              }
              setResearchMode("ab_test");
            }}
            className={`relative flex flex-col gap-3 p-6 rounded-2xl border-2 transition-all text-left ${
              abTestLocked
                ? "border-border opacity-60 cursor-not-allowed"
                : researchMode === "ab_test"
                ? "border-[#17171c] bg-[#edfce9]/60  shadow-md"
                : "border-border hover:border-[#17171c] dark:hover:border-[#17171c] hover:shadow-sm"
            }`}
          >
            {abTestLocked && (
              <span className="absolute top-3 right-3 inline-flex items-center gap-1 text-[10px] font-bold tracking-wider uppercase bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                <Lock size={9} /> Flex
              </span>
            )}
            <div className={`p-2.5 rounded-xl w-fit ${researchMode === "ab_test" && !abTestLocked ? "bg-[#edfce9] " : "bg-[#eeece7] "}`}>
              <FlaskConical size={22} className={researchMode === "ab_test" && !abTestLocked ? "text-[#ff7759]" : "text-muted-foreground"} />
            </div>
            <div>
              <div className="font-bold text-base">A/B Test Simülasyonu</div>
              <div className="text-sm text-muted-foreground mt-0.5">İki farklı mesaj, fiyat veya özellik varyantını karşılaştır</div>
            </div>
            {researchMode === "ab_test" && !abTestLocked && (
                            <Badge className="w-fit bg-[#17171c] hover:bg-[#17171c] text-white text-xs">Seçildi</Badge>
            )}
          </button>
        </div>

        <Button
          size="lg"
          disabled={researchMode === "ab_test" && abTestLocked}
          onClick={() => {
            setStage("chat");
            const greeting = researchMode === "ab_test"
              ? "Merhaba! Ben Defne. A/B test simülasyonu için buradayım. Hangi iki varyantı karşılaştırmak istiyorsunuz? Önce ürün/hizmet fikrinizi kısaca anlatın."
              : "Merhaba! Ben Defne — kıdemli pazar araştırması mimarınız. Ürün veya hizmet fikrinizi anlatın. Adım adım ihtiyacınız olan tüm araştırma verisini birlikte çıkaralım.";
            setMessages([{ role: "assistant", content: greeting }]);
          }}
          className="w-full gap-2 bg-[#17171c] hover:opacity-85 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Defne ile Başla
          <ChevronRight size={18} />
        </Button>

        {abTestLocked && researchMode === "ab_test" && (
          <p className="text-center text-xs text-muted-foreground">
            A/B Test modu{" "}
            <Link href="/client/upgrade" className="text-accent underline underline-offset-2 font-medium">Flex planında</Link>
            {" "}kullanılabilir.
          </p>
        )}
      </div>
    );
  }

  // ── STEP 2: Simulating ────────────────────────────────────────────────────
  if (stage === "simulating") {
    return (
      <div className="p-4 sm:p-8 max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Araştırma Başlatılıyor</h1>
          <p className="text-muted-foreground mt-1">Sentetik personalar oluşturuluyor ve mülakatlar yapılıyor...</p>
        </div>
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <Loader2 size={40} className="animate-spin text-[#ff7759]" />
          <div className="text-[#003c33] font-medium text-lg">Araştırma devam ediyor</div>
          <div className="text-sm text-muted-foreground max-w-md text-center">
            Defne brief&apos;inizi analiz ediyor, personalar oluşturuluyor ve her biriyle mülakat yapılıyor. Bu işlem birkaç saniye sürebilir.
          </div>
        </div>
      </div>
    );
  }

  // ── STEP 1: Defne Chat ──────────────────────────────────────────────────────
  return (
    <div className="p-4 sm:p-6 animate-in fade-in duration-300 flex-1 min-h-0 w-full flex flex-col">
      <div className="flex flex-col lg:flex-row gap-6 max-w-7xl w-full mx-auto flex-1 min-h-0">

        {/* ── LEFT: Chat Panel ── */}
        <div className={`flex-1 flex-col min-h-0 ${showMobileBrief ? 'hidden lg:flex' : 'flex'}`}>
          <div className="mb-4 shrink-0">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs gap-1 border-[#d9d9dd] ">
                {researchMode === "ab_test" ? <FlaskConical size={11} /> : <BarChart2 size={11} />}
                {researchMode === "ab_test" ? "A/B Test Modu" : "Pazar Araştırması"}
              </Badge>
              <button onClick={() => setStage("mode")} className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2">
                Modu değiştir
              </button>
              <div className="flex-1" />
              <button 
                onClick={() => setShowMobileBrief(!showMobileBrief)} 
                className="lg:hidden text-xs text-[#003c33] font-bold flex items-center gap-1 bg-[#edfce9] px-2 py-1 rounded-md"
              >
                <FileText size={12} />
                {showMobileBrief ? "Sohbete Dön" : "Briefi Gör"}
              </button>
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight mt-2">Defne ile Araştırma Sihirbazı</h1>
            <p className="text-sm text-muted-foreground">Sorularını yanıtla — Defne brief&apos;ini otomatik dolduruyor.</p>
          </div>

          {/* Chat bubbles */}
          <Card className="flex flex-col flex-1 min-h-0 shadow-sm overflow-hidden">
            <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-4 bg-[#f5f4f1]/30 ">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-200`}>
                  {msg.role === "assistant" && (
                    <div className="h-9 w-9 rounded-full overflow-hidden shrink-0 ring-2 ring-[#d9d9dd] ring-[#003c33]/40 shadow-sm mt-0.5">
                      <img src="/agent.svg" alt="Defne" className="object-cover w-full h-full" />
                    </div>
                  )}
                  <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    msg.role === "assistant"
                      ? "bg-white  border border-[#d9d9dd]/60  text-[#212121]  rounded-tl-none"
                      : "bg-[#17171c] text-white rounded-tr-none"
                  }`}>
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div className="h-8 w-8 rounded-full bg-[#d9d9dd]  text-[#616161] flex items-center justify-center shrink-0 mt-0.5">
                      <User size={15} />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3 justify-start animate-in fade-in duration-200">
                  <div className="h-9 w-9 rounded-full overflow-hidden shrink-0 ring-2 ring-[#d9d9dd] ring-[#003c33]/40 shadow-sm">
                    <img src="/agent.svg" alt="Defne" className="object-cover w-full h-full" />
                  </div>
                  <div className="px-4 py-3 bg-white  border border-[#d9d9dd]/60  rounded-2xl rounded-tl-none shadow-sm flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin text-[#ff7759]" />
                    <span className="text-xs italic bg-[linear-gradient(110deg,var(--color-muted-foreground)_40%,var(--color-foreground)_50%,var(--color-muted-foreground)_60%)] bg-[length:200%_100%] bg-clip-text text-transparent animate-[shimmer_2s_linear_infinite]">Defne düşünüyor...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input area */}
            <div className="shrink-0 p-4 border-t border-border bg-white/90  backdrop-blur-sm">
              {isReady && (
                <div className="mb-3 p-3 bg-[#edfce9] border border-[#003c33]/30 rounded-xl flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-[#003c33] text-sm font-semibold">
                    <CheckCircle2 size={16} />
                    Brief hazır! Sonraki adıma geçebilirsiniz.
                  </div>
                  <Button
                    size="sm"
                    onClick={handleStartResearch}
                    className="bg-[#003c33] hover:bg-[#003c33]/85 text-white gap-2 font-semibold"
                  >
                    Araştırmayı Başlat
                    <ChevronRight size={14} />
                  </Button>
                </div>
              )}
              <div className="flex gap-2">
                <textarea
                  className="flex-1 resize-none rounded-xl border border-border bg-[#f5f4f1] px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#17171c]/30 transition-shadow min-h-[44px] max-h-[120px] disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder={loading ? "Defne yazıyor, lütfen bekleyin..." : "Yanıtınızı yazın... (Enter ile gönder, Shift+Enter ile yeni satır)"}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  disabled={loading}
                />
                <Button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  size="sm"
                  className="h-auto px-4 bg-[#17171c] hover:bg-[#17171c] text-white gap-1.5 self-end py-2.5 rounded-xl"
                >
                  {loading ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* ── RIGHT: Brief Preview ── */}
        <div className={`lg:w-80 xl:w-96 overflow-y-auto ${showMobileBrief ? 'block' : 'hidden lg:block'}`}>
          <BriefPreview brief={brief} mode={researchMode} onToggleMobile={() => setShowMobileBrief(false)} />
        </div>
      </div>
    </div>
  );
}
