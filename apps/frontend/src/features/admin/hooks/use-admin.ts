"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { getAdminHeaders } from "@/lib/auth";
import type {
  AdminConfig,
  AgentSchemas,
  AuditLog,
  ClientInfo,
  CuratedQuestion,
  FeedbackItem,
  MetricsData,
  PersonaInfo,
  UsageResponse,
} from "../types";

/**
 * Admin panel veri katmanı (refactor R3-1).
 *
 * Durum, veri çekme ve mutasyon handler'ları UI bileşenlerinden ayrıldı.
 * Davranış birebir korunmuştur: aynı endpoint'ler, aynı bildirimler,
 * aynı tembel (lazy) yükleme guard'ları.
 */
export function useAdmin() {
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
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [usageLoading, setUsageLoading] = useState(false);
  const [adminKey, setAdminKey] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem("clarere_admin_key") || "" : "",
  );

  // Edit question purpose states
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null);
  const [editPurpose, setEditPurpose] = useState("");
  const [deleteQuestionTarget, setDeleteQuestionTarget] = useState<number | null>(null);
  const [deletingQuestion, setDeletingQuestion] = useState(false);

  const fetchAll = useCallback(() => {
    Promise.all([
      fetch("/api/admin/config", { headers: getAdminHeaders() }).then(r => r.json()),
      fetch("/api/admin/clients", { headers: getAdminHeaders() }).then(r => r.json()),
      fetch("/api/admin/personas", { headers: getAdminHeaders() }).then(r => r.json()),
      fetch("/api/admin/audit_logs", { headers: getAdminHeaders() }).then(r => r.json()),
      fetch("/api/admin/questions", { headers: getAdminHeaders() }).then(r => r.json()),
      fetch("/api/admin/feedbacks", { headers: getAdminHeaders() }).then(r => r.json()),
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

  // ── Tembel yükleme (sekme ilk açıldığında) ──
  const loadSchemas = useCallback(() => {
    if (schemas) return;
    setSchemasLoading(true);
    fetch("/api/admin/schemas", { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(d => {
        setSchemas(d);
        setBriefDefaults(d.brief_schema.defaults);
        setDraftQuestions(d.default_interview_questions);
      })
      .catch(() => toast.error("Şemalar yüklenemedi."))
      .finally(() => setSchemasLoading(false));
  }, [schemas]);

  const loadMetrics = useCallback(() => {
    if (metrics || metricsLoading) return;
    setMetricsLoading(true);
    fetch("/api/admin/metrics", { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(d => setMetrics(d))
      .catch(() => toast.error("Metrikler yüklenemedi."))
      .finally(() => setMetricsLoading(false));
  }, [metrics, metricsLoading]);

  const loadUsage = useCallback(() => {
    if (usage || usageLoading) return;
    setUsageLoading(true);
    fetch("/api/admin/usage", { headers: getAdminHeaders() })
      .then(r => r.json())
      .then(d => setUsage(d))
      .catch(() => toast.error("Maliyet verisi yüklenemedi."))
      .finally(() => setUsageLoading(false));
  }, [usage, usageLoading]);

  // ── Config Saving ──
  const saveConfig = async (key: string, value: string) => {
    setSavingConfig(key);
    try {
      const res = await fetch("/api/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAdminHeaders() },
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

  // ── Question Management ──
  const toggleLike = async (id: number, current: boolean) => {
    try {
      await fetch(`/api/admin/questions/${id}/like?is_liked=${!current}`, { method: "PUT", headers: getAdminHeaders() });
      setQuestions(prev => prev.map(q => (q.id === id ? { ...q, is_liked: !current } : q)));
      toast.success("Beğeni güncellendi.");
    } catch {
      toast.error("İşlem başarısız.");
    }
  };

  const savePurpose = async (id: number) => {
    try {
      await fetch(`/api/admin/questions/${id}/purpose?purpose=${encodeURIComponent(editPurpose)}`, { method: "PUT", headers: getAdminHeaders() });
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
      await fetch(`/api/admin/questions/${id}`, { method: "DELETE", headers: getAdminHeaders() });
      setQuestions(prev => prev.filter(q => q.id !== id));
      toast.success("Soru silindi.");
      setDeleteQuestionTarget(null);
    } catch {
      toast.error("Silme başarısız.");
    } finally {
      setDeletingQuestion(false);
    }
  };

  return {
    // durum
    config, clients, personas, logs, questions, feedbacks,
    schemas, schemasLoading, expandedPool, editingDefaultQ, draftQuestions,
    savingDefaults, briefDefaults, loading, savingConfig, metrics, metricsLoading,
    usage, usageLoading, adminKey,
    editingQuestion, editPurpose, deleteQuestionTarget, deletingQuestion,
    // setter'lar
    setAdminKey, setSchemas, setExpandedPool, setEditingDefaultQ,
    setDraftQuestions, setSavingDefaults, setBriefDefaults,
    setEditingQuestion, setEditPurpose, setDeleteQuestionTarget,
    // eylemler
    fetchAll, loadSchemas, loadMetrics, loadUsage,
    saveConfig, toggleLike, savePurpose, deleteQuestion,
  };
}
