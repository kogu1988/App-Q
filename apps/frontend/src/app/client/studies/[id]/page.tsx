"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Loader2, 
  Calendar, 
  AlertCircle,
  CheckCircle2,
  Trash2
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { useClientPlan } from "@/hooks/use-client-plan";
import {
  askFollowUp,
  askResearchChat,
  deleteStudy,
} from "@/features/studies/api/studies-api";
import { useStudyDetail } from "@/features/studies/hooks/use-study-detail";
import { synthesizeAndSaveReport } from "@/features/studies/lib/synthesis";

import { SummaryTab } from "@/features/studies/components/SummaryTab";
import { PersonasTab } from "@/features/studies/components/PersonasTab";
import { InterviewsTab } from "@/features/studies/components/InterviewsTab";
import { ScriptTab } from "@/features/studies/components/ScriptTab";
import { EvidenceTab } from "@/features/studies/components/EvidenceTab";
import { ReportTab } from "@/features/studies/components/ReportTab";
import { StudyHeaderActions } from "@/features/studies/components/StudyHeaderActions";
import { StudyTabNav } from "@/features/studies/components/StudyTabNav";

export default function StudyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const studyId = params.id as string;

  const { study, setStudy, loading, error, activeTab, setActiveTab } = useStudyDetail(studyId);
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

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteStudy(studyId);
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
      const turn = await askFollowUp(studyId, personaId, followUpText);

      // Yeni turu anında göster
      setStudy(prev => {
        if (!prev) return prev;
        const newInterviews = [...(prev.interviews || [])];
        const idx = newInterviews.findIndex(i => i.persona.id === personaId);
        if (idx !== -1) {
          newInterviews[idx].turns.push(turn);
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
      const answer = await askResearchChat(studyId, question);
      setChatMessages(prev => [...prev, { role: "assistant", content: answer }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Bir hata oluştu. Lütfen tekrar deneyin.";
      setChatMessages(prev => [...prev, { role: "assistant", content: msg }]);
    } finally {
      setSendingChat(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="h-10 w-10 animate-spin text-action-blue" />
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

  const handleSynthesize = async () => {
    setSynthesizing(true);
    try {
      const updated = await synthesizeAndSaveReport({ studyId, brief, metadata, plan, personas, interviews });
      if (updated) setStudy(updated);
      toast.success("Rapor olusturuldu!");
      setActiveTab("report");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Rapor olusturulamadi.");
    } finally {
      setSynthesizing(false);
    }
  };

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
              <Badge variant="outline" className="bg-soft-stone text-body-muted text-xs font-semibold">
                {metadata?.category || "Genel"}
              </Badge>
              {isCompleted ? (
                <Badge className="bg-deep-green hover:bg-deep-green/85 text-white flex items-center gap-1 text-xs">
                  <CheckCircle2 size={12} />
                  Tamamlandı
                </Badge>
              ) : (
                <Badge variant="secondary" className="text-xs">Taslak</Badge>
              )}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-primary dark:text-white">
              {metadata?.title || "İsimsiz Simülasyon"}
            </h1>
            <p className="text-muted-foreground text-sm flex items-center gap-1.5">
              <Calendar size={14} />
              Son Güncelleme: {metadata?.updated_at ? new Date(metadata.updated_at).toLocaleDateString("tr-TR") : "-"}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
          <StudyHeaderActions
            studyId={studyId}
            isCompleted={isCompleted}
            interviewsCount={interviews.length}
            synthesizing={synthesizing}
            onSynthesize={handleSynthesize}
            pdfExportEnabled={!!clientPlan?.features?.pdf_export}
            whiteLabel={!!clientPlan?.features?.white_label}
            onDelete={() => setDeleteModalOpen(true)}
          />

            <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <div className="flex items-center gap-3 mb-1">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-100 dark:bg-red-950/40 shrink-0">
                      <Trash2 size={18} className="text-red-600 dark:text-red-400" />
                    </div>
                    <DialogTitle className="text-lg font-bold text-primary dark:text-white">
                      Araştırmayı Sil
                    </DialogTitle>
                  </div>
                  <DialogDescription className="text-sm text-body-muted dark:text-muted-text leading-relaxed pl-[52px]">
                    <span className="font-semibold text-ink dark:text-border-light">&ldquo;{metadata?.title || "Bu araştırma"}&rdquo;</span>{" "}
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

      <StudyTabNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        personasCount={personas.length}
        interviewsCount={interviews.length}
      />

      {/* 💼 Tab View Content */}
      <div className="space-y-6">

        {/* ==================== Tab 1: Summary ==================== */}
        {activeTab === "summary" && (
          <SummaryTab
            brief={brief}
            metadata={metadata}
            plan={plan}
            study={study}
            planType={clientPlan.plan_type}
          />
        )}

        {/* ==================== Tab 2: Personas ==================== */}
        {activeTab === "personas" && (
          <PersonasTab
            personas={personas}
            interviews={interviews}
            study={study}
            onOpenTranscript={(idx) => {
              setSelectedPersonaIdx(idx);
              setActiveTab("interviews");
            }}
          />
        )}

        {/* ==================== Tab 3: Interviews & Transcripts ==================== */}
        {activeTab === "interviews" && (
          <InterviewsTab
            interviews={interviews}
            study={study}
            planType={clientPlan?.plan_type || "Free"}
            followUpText={followUpText}
            onFollowUpTextChange={setFollowUpText}
            sendingFollowUp={sendingFollowUp}
            onFollowUp={handleFollowUp}
          />
        )}

        {/* ==================== Tab: Script ==================== */}
        {activeTab === "script" && (
          <ScriptTab plan={plan} />
        )}

        {/* ==================== Tab: Findings (Kanıt Zinciri) ==================== */}
        {activeTab === "findings" && (
          <EvidenceTab study={study} />
        )}

{/* ==================== Tab 4: Synthesis Report ==================== */}
        {activeTab === "report" && (
          <ReportTab
            study={study}
            personas={personas}
            interviews={interviews}
            planType={clientPlan.plan_type}
            isCompleted={isCompleted}
            chatMessages={chatMessages}
            chatInput={chatInput}
            onChatInputChange={setChatInput}
            sendingChat={sendingChat}
            onSendChat={sendChat}
          />
        )}
      </div>
    </div>
  );
}
