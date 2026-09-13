import { getAuthHeaders } from "./auth";

/**
 * İstemci taraflı ürün KPI event'i gönderir (funnel ölçümü).
 *
 * Fail-safe: ağ/oturum hatası kullanıcı akışını etkilemez (fire-and-forget).
 * Yalnızca backend beyaz listesindeki event adları kabul edilir.
 */
export function trackEvent(
  eventName: string,
  studyId?: string,
  props?: Record<string, unknown>,
): void {
  if (typeof window === "undefined") return;
  try {
    void fetch("/api/client/events", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify({ event_name: eventName, study_id: studyId ?? "", props: props ?? {} }),
      keepalive: true,
    }).catch(() => {
      /* ölçüm hatası yok sayılır */
    });
  } catch {
    /* ölçüm hatası yok sayılır */
  }
}
