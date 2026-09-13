import { getAuthHeaders } from "@/lib/auth";
import type { PersonaInterview, StudyDetail, StudyFinding, DecisionItem } from "../types";

/**
 * Study detay ekranının API erişim katmanı (refactor R1-3).
 *
 * Buradaki fonksiyonlar UI'dan bağımsızdır: ham istek/yanıt yönetimini yapar.
 * Hata mesajları kullanıcıya gösterilebilir biçimde Türkçe döner.
 */

export interface StudyFindingsResponse {
  findings: StudyFinding[];
  decision_items: DecisionItem[];
}

async function readErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    const d = data?.detail;
    if (typeof d === "string") return d;
    if (d?.message) return d.message as string;
    if (d?.required_plan) return `Bu özellik ${d.required_plan} planı gerektirir.`;
  } catch {
    /* gövde JSON değilse yok say */
  }
  return fallback;
}

/** Çalışma detayını getirir. */
export async function fetchStudyDetail(studyId: string): Promise<StudyDetail> {
  const res = await fetch(`/api/client/studies/${studyId}`, { headers: getAuthHeaders() });
  if (!res.ok) {
    if (res.status === 404) throw new Error("Araştırma bulunamadı.");
    if (res.status === 403) throw new Error("Bu araştırmayı görüntüleme yetkiniz yok.");
    throw new Error("Veriler yüklenirken bir hata oluştu.");
  }
  return (await res.json()) as StudyDetail;
}

/** Rapor varsa kanıt zinciri (bulgular + karar öğeleri) getirir. Hata opsiyoneldir. */
export async function fetchStudyFindings(studyId: string): Promise<StudyFindingsResponse> {
  const res = await fetch(`/api/client/studies/${studyId}/findings`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Bulgular yüklenemedi.");
  const data = await res.json();
  return {
    findings: data.findings || [],
    decision_items: data.decision_items || [],
  };
}

/** Çalışmayı kalıcı olarak siler. */
export async function deleteStudy(studyId: string): Promise<void> {
  const res = await fetch(`/api/client/studies/${studyId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string })?.detail || "Silme başarısız.");
  }
}

/** Persone'ya ek (takip) soru sorar ve üretilen turu döner. */
export async function askFollowUp(
  studyId: string,
  personaId: string,
  question: string,
): Promise<PersonaInterview["turns"][number]> {
  const res = await fetch(`/api/client/studies/${studyId}/follow-up`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ persona_id: personaId, question }),
  });
  if (!res.ok) throw new Error(await readErrorDetail(res, "Soru sorulamadı."));
  const data = await res.json();
  return data.turn;
}

/** Araştırma asistanına (copilot) soru sorar ve yanıt metnini döner. */
export async function askResearchChat(studyId: string, question: string): Promise<string> {
  const res = await fetch(`/api/client/studies/${studyId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    throw new Error(await readErrorDetail(res, "Yanıt alınamadı. Lütfen tekrar deneyin."));
  }
  const data = await res.json();
  return data.answer || data.response || "";
}

// ── Ham Response dönen istekler ──────────────────────────────────────────────
// Çağıran taraf kontrol akışını (res.ok / res.json) korumak istediğinde kullanılır.

/** Sentez raporu isteği (POST /api/client/synthesize). */
export function synthesizeReportRequest(body: unknown): Promise<Response> {
  return fetch(`/api/client/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(body),
  });
}

/** Çalışma kaydetme/güncelleme isteği (POST /api/client/studies). */
export function saveStudyRequest(body: unknown): Promise<Response> {
  return fetch(`/api/client/studies`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(body),
  });
}

/** PDF indirme isteği (GET /api/client/studies/{id}/pdf). */
export function studyPdfRequest(studyId: string): Promise<Response> {
  return fetch(`/api/client/studies/${studyId}/pdf`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
}
