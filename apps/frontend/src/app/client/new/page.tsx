"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
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
  target_users?: string[];
  questions?: string[];
  competitors?: string[];
  expected_price?: string;
  sales_channel?: string;
  success_metric?: string;
  variant_a?: string;
  variant_b?: string;
}

// ─── Brief Preview Card ───────────────────────────────────────────────────────

function renderBriefValue(value: any) {
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

function BriefPreview({ brief, mode }: { brief: Brief; mode: "research" | "ab_test" }) {
  const fields = mode === "ab_test"
    ? [
      { icon: FileText, label: "Başlık", value: brief.title },
      { icon: Target, label: "Ürün Fikri", value: brief.idea },
      { icon: Layers, label: "Varyant A", value: brief.variant_a },
      { icon: Layers, label: "Varyant B", value: brief.variant_b },
      { icon: Users, label: "Hedef Kitle", value: brief.target_users?.join(", ") },
      { icon: CheckCircle2, label: "Başarı Kriteri", value: brief.success_metric },
    ]
    : [
      { icon: FileText, label: "Başlık", value: brief.title },
      { icon: Target, label: "Ürün Fikri", value: brief.idea },
      { icon: Users, label: "Hedef Kitle", value: brief.target_users?.join(", ") },
      { icon: DollarSign, label: "Fiyat Modeli", value: brief.expected_price },
      { icon: Layers, label: "Rakipler", value: brief.competitors?.join(", ") },
      { icon: CheckCircle2, label: "Başarı Kriteri", value: brief.success_metric },
    ];

  const filled = fields.filter(f => f.value && f.value.length > 0).length;
  const total = fields.length;
  const pct = Math.round((filled / total) * 100);

  return (
    <Card className="sticky top-6 shadow-sm border-[#d9d9dd] ">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-bold text-[#003c33] flex items-center gap-2">
          <FileText size={14} />
          Canlı Brief Özeti
        </CardTitle>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1.5 bg-[#eeece7]  rounded-full overflow-hidden">
            <div
              className="h-full bg-[#003c33] rounded-full transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs font-bold text-[#ff7759] /80 tabular-nums">{pct}%</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {fields.map(({ icon: Icon, label, value }) => (
          <div key={label} className={`flex gap-2 p-2 rounded-lg transition-colors ${value ? "bg-[#edfce9]/50 " : "opacity-40"}`}>
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

export default function NewResearchWizard() {
  const router = useRouter();
  const { plan } = useClientPlan();
  const abTestLocked = !plan?.features?.ab_test;

  const [researchMode, setResearchMode] = useState<"research" | "ab_test">("research");
  const [stage, setStage] = useState<"mode" | "chat" | "personas" | "simulating">("mode");

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  if (plan?.trial_expired) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] p-4 text-center max-w-md mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div className="h-16 w-16 rounded-full bg-amber-50 flex items-center justify-center shadow-sm border border-amber-200">
          <Lock size={32} className="text-amber-800" />
        </div>
        <div className="space-y-3">
          <h1 className="text-2xl font-black tracking-tight text-[#17171c]">Trial Expired (Deneme Süreniz Doldu)</h1>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Every plan comes with a 3-day free trial and 2 free researches — no credit card required. You get access to the platform so you can run real research and see the output before committing.
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
  const [brief, setBrief] = useState<Brief>({});
  const [isReady, setIsReady] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Persona Stage State
  const [matchedRoles, setMatchedRoles] = useState<{role: string, why: string, count: number}[]>([]);
  const [isMatching, setIsMatching] = useState(false);

  // Scroll to bottom on new message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Kick off with Defne's greeting after mode is confirmed
  useEffect(() => {
    if (stage !== "chat") return;
    const greeting = researchMode === "ab_test"
      ? "Merhaba! Ben Defne. A/B test simülasyonu için buradayım. Hangi iki varyantı karşılaştırmak istiyorsunuz? Önce ürün/hizmet fikrinizi kısaca anlatın."
      : "Merhaba! Ben Defne — kıdemli pazar araştırması mimarınız. Ürün veya hizmet fikrinizi anlatın. Adım adım ihtiyacınız olan tüm araştırma verisini birlikte çıkaralım.";
    setMessages([{ role: "assistant", content: greeting }]);
  }, [stage, researchMode]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: userMsg }];
    setMessages(nextMessages);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:3000/api/client/intake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_brief: brief,
          chat_history: nextMessages.map(m => ({ role: m.role, content: m.content })),
          user_message: userMsg,
          app_mode: researchMode,
        }),
      });

      if (!res.ok) throw new Error("Defne yanıt vermedi.");
      const data = await res.json();

      const reply: string = data.assistant_reply || "Anladım, devam edebiliriz.";
      const updatedBrief: Brief = data.updated_brief || brief;

      setBrief(updatedBrief);
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);

      // Detect ready signal
      if (reply.includes("butona basabilirsin") || reply.includes("başlatmaya hazırım")) {
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

  const handleProceedToPersonas = async () => {
    if (!brief.idea && !brief.title) {
      toast.error("Brief henüz tamamlanmadı.");
      return;
    }
    
    setIsMatching(true);
    setStage("personas"); // Transition to Persona stage with loading state
    
    const username = typeof window !== "undefined" ? localStorage.getItem("appq_username") : null;
    try {
      const res = await fetch("http://localhost:3000/api/client/studio/match-personas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(username ? { "X-Username": username } : {}),
        },
        body: JSON.stringify(brief),
      });
      
      if (!res.ok) throw new Error("Persona eşleştirme hatası");
      const data = await res.json();
      
      const roles = (data.matched_roles || []).map((r: any) => ({
        role: r.role,
        why: r.why,
        count: 2 // Default 2 persons per role
      }));
      setMatchedRoles(roles);
    } catch (err) {
      toast.error("Persona havuzundan eşleştirme yapılamadı. Lütfen tekrar deneyin.");
      setStage("chat"); // Revert if failed
    } finally {
      setIsMatching(false);
    }
  };

  const handleStartSimulation = async () => {
    setStage("simulating");
    const username = typeof window !== "undefined" ? localStorage.getItem("appq_username") : null;
    try {
      const res = await fetch("http://localhost:3000/api/client/studio/simulate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(username ? { "X-Username": username } : {}),
        },
        body: JSON.stringify({
          brief: brief.idea || brief.title || "",
          category: brief.category || (researchMode === "ab_test" ? "A/B Test" : "Genel"),
<<<<<<< HEAD
          title: brief.title || "Araştırma",
          context: brief.idea || "",
          brand: "Clarere",
          budget: "Standart",
          target_users: brief.target_users || [],
          competitors: brief.competitors || [],
          expected_price: brief.expected_price || null,
          sales_channel: brief.sales_channel || null,
          success_metric: brief.success_metric || null,
          variant_a: brief.variant_a || null,
          variant_b: brief.variant_b || null,
          questions: plan?.plan_type === "Free" ? [] : (brief.questions || []),
=======
          pricing: brief.expected_price || "Bilinmiyor",
          panel_roles: matchedRoles.map(r => ({ role: r.role, why: r.why, count: r.count }))
>>>>>>> c2e56332200a78c21e940108bc5898a678c72903
        }),
      });
      if (!res.ok) {
        throw new Error(`Sunucu hatası: ${res.status}`);
      }
      toast.success("Araştırma simülasyonu başlatıldı! Yönlendiriliyorsunuz...");
      router.push("/client");
    } catch (err) {
      toast.error("Araştırma motoru ulaşılamıyor.");
      setStage("personas");
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
                  "A/B Test Modu Pro planında kullanılabilir.",
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
                <Lock size={9} /> Pro
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
          onClick={() => setStage("chat")}
          className="w-full gap-2 bg-[#17171c] hover:opacity-85 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Defne ile Başla
          <ChevronRight size={18} />
        </Button>

        {abTestLocked && researchMode === "ab_test" && (
          <p className="text-center text-xs text-muted-foreground">
            A/B Test modu{" "}
            <Link href="/client/upgrade" className="text-accent underline underline-offset-2 font-medium">Pro planında</Link>
            {" "}kullanılabilir.
          </p>
        )}
      </div>
    );
  }

  // ── STEP 2: Persona Selection ───────────────────────────────────────────────
  if (stage === "personas" || stage === "simulating") {
    return (
      <div className="p-4 sm:p-8 max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Hedef Kitle Seçimi</h1>
          <p className="text-muted-foreground mt-1">Briefinize uygun veritabanı personaları eşleştirildi. Kaç kişi ile görüşmek istediğinizi seçin.</p>
        </div>

        {isMatching ? (
          <div className="flex flex-col items-center justify-center py-12 gap-4">
            <Loader2 size={32} className="animate-spin text-[#ff7759]" />
            <div className="text-[#003c33] font-medium animate-pulse">Persona havuzundan eşleştirmeler yapılıyor...</div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-[#d9d9dd] shadow-sm overflow-hidden">
              <div className="p-4 bg-[#f5f4f1] border-b border-[#d9d9dd]">
                <h3 className="font-bold text-[#003c33] flex items-center gap-2">
                  <Users size={18} />
                  Önerilen Persona Grupları
                </h3>
              </div>
              <div className="p-4 space-y-4">
                {matchedRoles.length === 0 ? (
                  <div className="text-sm text-muted-foreground italic text-center py-4">
                    Uygun persona bulunamadı. Lütfen daha detaylı bir brief girin.
                  </div>
                ) : (
                  matchedRoles.map((role, idx) => (
                    <div key={idx} className="flex flex-col sm:flex-row gap-4 items-start sm:items-center p-4 rounded-xl border border-[#d9d9dd] bg-[#faf9f7] hover:border-[#17171c] transition-colors">
                      <div className="flex-1">
                        <div className="font-bold text-[#212121]">{role.role}</div>
                        <div className="text-sm text-muted-foreground mt-1">{role.why}</div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0 bg-white p-1 rounded-lg border border-[#d9d9dd]">
                        <button
                          type="button"
                          className="w-8 h-8 flex items-center justify-center rounded bg-[#f5f4f1] text-[#212121] hover:bg-[#17171c] hover:text-white transition-colors disabled:opacity-50"
                          disabled={role.count <= 0 || stage === "simulating"}
                          onClick={() => {
                            const newRoles = [...matchedRoles];
                            newRoles[idx].count = Math.max(0, role.count - 1);
                            setMatchedRoles(newRoles);
                          }}
                        >
                          -
                        </button>
                        <span className="w-6 text-center font-bold tabular-nums">{role.count}</span>
                        <button
                          type="button"
                          className="w-8 h-8 flex items-center justify-center rounded bg-[#f5f4f1] text-[#212121] hover:bg-[#17171c] hover:text-white transition-colors disabled:opacity-50"
                          disabled={role.count >= 10 || stage === "simulating"}
                          onClick={() => {
                            const newRoles = [...matchedRoles];
                            newRoles[idx].count = Math.min(10, role.count + 1);
                            setMatchedRoles(newRoles);
                          }}
                        >
                          +
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="flex gap-4 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                size="lg"
                onClick={() => setStage("chat")}
                disabled={stage === "simulating"}
                className="px-6 border-[#d9d9dd] text-[#616161]"
              >
                Geri Dön
              </Button>
              <Button
                type="button"
                size="lg"
                onClick={handleStartSimulation}
                disabled={stage === "simulating" || matchedRoles.every(r => r.count === 0)}
                className="flex-1 gap-2 bg-[#17171c] hover:bg-[#17171c]/90 text-white font-bold"
              >
                {stage === "simulating" ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Simülasyon Başlatılıyor...
                  </>
                ) : (
                  <>
                    Simülasyonu Başlat
                    <ChevronRight size={18} />
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── STEP 1: Defne Chat ──────────────────────────────────────────────────────
  return (
    <div className="p-4 sm:p-6 animate-in fade-in duration-300 flex-1 min-h-0 w-full flex flex-col">
      <div className="flex flex-col lg:flex-row gap-6 max-w-7xl w-full mx-auto flex-1 min-h-0">

        {/* ── LEFT: Chat Panel ── */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="mb-4 shrink-0">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs gap-1 border-[#d9d9dd] ">
                {researchMode === "ab_test" ? <FlaskConical size={11} /> : <BarChart2 size={11} />}
                {researchMode === "ab_test" ? "A/B Test Modu" : "Pazar Araştırması"}
              </Badge>
              <button onClick={() => setStage("mode")} className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2">
                Modu değiştir
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
                    <span className="text-xs text-muted-foreground italic">Defne düşünüyor...</span>
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
                    onClick={handleProceedToPersonas}
                    className="bg-[#003c33] hover:bg-[#003c33]/85 text-white gap-2 font-semibold"
                  >
                    Devam Et
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
        <div className="lg:w-80 xl:w-96 overflow-y-auto">
          <BriefPreview brief={brief} mode={researchMode} />
        </div>
      </div>
    </div>
  );
}
