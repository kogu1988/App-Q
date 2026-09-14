/** Arastirma istek/polling katmani (refactor R4-3). */
import { getAuthHeaders } from "@/lib/auth";
import type { ResearchResult } from "../types";

const RESEARCH_POLL_INTERVAL_MS = 2000;
const RESEARCH_POLL_TIMEOUT_MS = 6 * 60 * 1000;

export async function pollResearchJob(
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
export async function requestResearch(payload: Record<string, unknown>): Promise<ResearchResult> {
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
