/**
 * Merkezi auth header yardımcısı — JWT token varsa `Authorization: Bearer`,
 * yoksa `X-Username` (geriye dönük uyumluluk) döndürür.
 */
export function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const headers: Record<string, string> = {};
  const token = localStorage.getItem("clarere_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const username = localStorage.getItem("clarere_username");
  if (username) {
    // X-Username her zaman da gönderilir: production'da middleware bunu yok sayar
    // (JWT zorunlu), development'ta ise süresi dolmuş/geçersiz token durumunda
    // yedek oturum bilgisi olarak kullanılır.
    headers["X-Username"] = username;
  }
  return headers;
}

/**
 * Admin API auth header'ı — localStorage'daki admin anahtarını gönderir.
 */
export function getAdminHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const key = localStorage.getItem("clarere_admin_key");
  if (key) {
    return { "X-Admin-Key": key };
  }
  return {};
}
