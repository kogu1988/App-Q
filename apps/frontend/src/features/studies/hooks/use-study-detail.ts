"use client";

import { useEffect, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { trackEvent } from "@/lib/events";
import { fetchStudyDetail, fetchStudyFindings } from "../api/studies-api";
import type { StudyDetail } from "../types";

export type StudyDetailTab =
  | "summary"
  | "personas"
  | "script"
  | "interviews"
  | "findings"
  | "report";

interface UseStudyDetailResult {
  study: StudyDetail | null;
  setStudy: Dispatch<SetStateAction<StudyDetail | null>>;
  loading: boolean;
  error: string | null;
  activeTab: StudyDetailTab;
  setActiveTab: Dispatch<SetStateAction<StudyDetailTab>>;
}

/**
 * Study detay ekranının veri katmanı (refactor R1-1).
 *
 * Sorumluluklar: detay + kanıt zinciri getirme, yükleme/hata durumu,
 * aktif sekme yönetimi ve funnel ölçüm event'leri. UI'dan bağımsızdır.
 */
export function useStudyDetail(studyId: string): UseStudyDetailResult {
  const [study, setStudy] = useState<StudyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<StudyDetailTab>("summary");

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

    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const data = await fetchStudyDetail(studyId);
        if (cancelled) return;
        setStudy(data);

        // Rapor varsa kanıt zincirini (bulgular) ekle — opsiyonel
        if (data.metadata?.has_report) {
          try {
            const { findings, decision_items } = await fetchStudyFindings(studyId);
            if (cancelled) return;
            setStudy(prev => (prev ? { ...prev, findings, decision_items } : prev));
          } catch {
            /* findings optional */
          }
          // Rapor hazırsa doğrudan rapor sekmesine geç
          if (!cancelled) setActiveTab("report");
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Bir hata oluştu.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [studyId]);

  return { study, setStudy, loading, error, activeTab, setActiveTab };
}
