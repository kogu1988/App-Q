"use client";

import { useState, useRef, useEffect } from "react";
import { BriefPreview } from "@/features/wizard/components/BriefPreview";
import { ModeSelection } from "@/features/wizard/components/ModeSelection";
import { SimulatingScreen } from "@/features/wizard/components/SimulatingScreen";
import { requestResearch } from "@/features/wizard/lib/research-client";
import { toArray } from "@/features/wizard/types";
import type { Brief, ChatMessage } from "@/features/wizard/types";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { getAuthHeaders } from "@/lib/auth";
import {
  Loader2, Send, User, ChevronRight,
  FileText,
  FlaskConical, BarChart2, CheckCircle2, Lock
} from "lucide-react";
import { useClientPlan } from "@/hooks/use-client-plan";
import Link from "next/link";

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
          <h1 className="text-2xl font-black tracking-tight text-primary">Trial Expired (Deneme Süreniz Doldu)</h1>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Every plan comes with a 1-month free trial and 2 free researches — no credit card required. You get access to the platform so you can run real research and see the output before committing.
          </p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            After 3 days or 2 researches (whichever comes first), you’ll be asked to choose a plan. Your research reports and data stay accessible for 30 days — after that, access is limited. Pick a plan to keep everything unlocked.
          </p>
        </div>
        <Link href="/client/upgrade" className="w-full">
          <Button className="w-full bg-primary hover:opacity-85 text-white font-semibold rounded-xl h-12 text-sm">
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
        } catch {}
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
      <ModeSelection
        researchMode={researchMode}
        onModeChange={setResearchMode}
        abTestLocked={abTestLocked}
        onUpgrade={() => router.push("/client/upgrade")}
        onStart={() => {
          setStage("chat");
          const greeting = researchMode === "ab_test"
            ? "Merhaba! Ben Defne. A/B test simülasyonu için buradayım. Hangi iki varyantı karşılaştırmak istiyorsunuz? Önce ürün/hizmet fikrinizi kısaca anlatın."
            : "Merhaba! Ben Defne — kıdemli pazar araştırması mimarınız. Ürün veya hizmet fikrinizi anlatın. Adım adım ihtiyacınız olan tüm araştırma verisini birlikte çıkaralım.";
          setMessages([{ role: "assistant", content: greeting }]);
        }}
      />
    );
  }

  // ── STEP 2: Simulating ────────────────────────────────────────────────────
  if (stage === "simulating") {
    return <SimulatingScreen />;
  }

  // ── STEP 1: Defne Chat ──────────────────────────────────────────────────────
  return (
    <div className="p-4 sm:p-6 animate-in fade-in duration-300 flex-1 min-h-0 w-full flex flex-col">
      <div className="flex flex-col lg:flex-row gap-6 max-w-7xl w-full mx-auto flex-1 min-h-0">

        {/* ── LEFT: Chat Panel ── */}
        <div className={`flex-1 flex-col min-h-0 ${showMobileBrief ? 'hidden lg:flex' : 'flex'}`}>
          <div className="mb-4 shrink-0">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs gap-1 border-hairline ">
                {researchMode === "ab_test" ? <FlaskConical size={11} /> : <BarChart2 size={11} />}
                {researchMode === "ab_test" ? "A/B Test Modu" : "Pazar Araştırması"}
              </Badge>
              <button onClick={() => setStage("mode")} className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2">
                Modu değiştir
              </button>
              <div className="flex-1" />
              <button 
                onClick={() => setShowMobileBrief(!showMobileBrief)} 
                className="lg:hidden text-xs text-deep-green font-bold flex items-center gap-1 bg-pale-green px-2 py-1 rounded-md"
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
            <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-4 bg-muted-surface/30 ">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-200`}>
                  {msg.role === "assistant" && (
                    <div className="h-9 w-9 rounded-full overflow-hidden shrink-0 ring-2 ring-hairline ring-deep-green/40 shadow-sm mt-0.5">
                      <Image src="/agent.svg" alt="Defne" width={36} height={36} className="object-cover w-full h-full" />
                    </div>
                  )}
                  <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    msg.role === "assistant"
                      ? "bg-white  border border-hairline/60  text-ink  rounded-tl-none"
                      : "bg-primary text-white rounded-tr-none"
                  }`}>
                    {msg.content}
                  </div>
                  {msg.role === "user" && (
                    <div className="h-8 w-8 rounded-full bg-hairline  text-body-muted flex items-center justify-center shrink-0 mt-0.5">
                      <User size={15} />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3 justify-start animate-in fade-in duration-200">
                  <div className="h-9 w-9 rounded-full overflow-hidden shrink-0 ring-2 ring-hairline ring-deep-green/40 shadow-sm">
                    <Image src="/agent.svg" alt="Defne" width={36} height={36} className="object-cover w-full h-full" />
                  </div>
                  <div className="px-4 py-3 bg-white  border border-hairline/60  rounded-2xl rounded-tl-none shadow-sm flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin text-coral" />
                    <span className="text-xs italic bg-[linear-gradient(110deg,var(--color-muted-foreground)_40%,var(--color-foreground)_50%,var(--color-muted-foreground)_60%)] bg-[length:200%_100%] bg-clip-text text-transparent animate-[shimmer_2s_linear_infinite]">Defne düşünüyor...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input area */}
            <div className="shrink-0 p-4 border-t border-border bg-white/90  backdrop-blur-sm">
              {isReady && (
                <div className="mb-3 p-3 bg-pale-green border border-deep-green/30 rounded-xl flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-deep-green text-sm font-semibold">
                    <CheckCircle2 size={16} />
                    Brief hazır! Sonraki adıma geçebilirsiniz.
                  </div>
                  <Button
                    size="sm"
                    onClick={handleStartResearch}
                    className="bg-deep-green hover:bg-deep-green/85 text-white gap-2 font-semibold"
                  >
                    Araştırmayı Başlat
                    <ChevronRight size={14} />
                  </Button>
                </div>
              )}
              <div className="flex gap-2">
                <textarea
                  className="flex-1 resize-none rounded-xl border border-border bg-muted-surface px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-shadow min-h-[44px] max-h-[120px] disabled:opacity-50 disabled:cursor-not-allowed"
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
                  className="h-auto px-4 bg-primary hover:bg-primary text-white gap-1.5 self-end py-2.5 rounded-xl"
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
