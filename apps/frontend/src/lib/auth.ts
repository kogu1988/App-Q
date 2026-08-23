/**
 * Merkezi auth header yardımcısı — JWT token varsa `Authorization: Bearer`,
 * yoksa `X-Username` (geriye dönük uyumluluk) döndürür.
 */
export function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("clarere_token");
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  const username = localStorage.getItem("clarere_username");
  if (username) {
    return { "X-Username": username };
  }
  return {};
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
