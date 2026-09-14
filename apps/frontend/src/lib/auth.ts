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

/**
 * Oturum işareti cookie'si — middleware'in derin bağlantı koruması için.
 * Hassas veri İÇERMEZ (JWT localStorage'da kalır); yalnızca "giriş yapıldı" bilgisi.
 */
const SESSION_COOKIE = "clarere_session";
const SESSION_MAX_AGE = 60 * 60 * 24 * 30; // 30 gün

// ── Oturum deposu (useSyncExternalStore) ─────────────────────────────────────
// localStorage bir dış sistemdir; React state'i yerine buradan okunur. Böylece
// giriş/çıkış anında oturuma bağlı tüm bileşenler kendiliğinden yenilenir ve
// hiçbir bileşen "boş kimlikle bir kez fetch atıp bir daha denememe" tuzağına
// düşmez.

const AUTH_EVENT = "clarere:auth-changed";

/** Oturum değişimini dinler (aynı sekme: AUTH_EVENT, diğer sekmeler: storage). */
export function subscribeAuth(onChange: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(AUTH_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(AUTH_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/** İstemcideki güncel kullanıcı adı (yoksa null). */
export function getAuthUsernameSnapshot(): string | null {
  return localStorage.getItem("clarere_username");
}

/** Sunucu ve hydration sırasında oturum okunamaz → "henüz bilinmiyor". */
export function getAuthUsernameServerSnapshot(): undefined {
  return undefined;
}

/** Oturumu kaydeder ve dinleyicileri bilgilendirir. */
export function setAuthUsername(username: string | null): void {
  if (typeof window === "undefined") return;
  if (username) {
    localStorage.setItem("clarere_username", username);
  } else {
    localStorage.removeItem("clarere_username");
  }
  window.dispatchEvent(new Event(AUTH_EVENT));
}

/** Oturumu (token dahil) tamamen temizler ve dinleyicileri bilgilendirir. */
export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("clarere_username");
  localStorage.removeItem("clarere_token");
  clearSessionMarker();
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function setSessionMarker(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${SESSION_COOKIE}=1; path=/; max-age=${SESSION_MAX_AGE}; samesite=lax`;
}

export function clearSessionMarker(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${SESSION_COOKIE}=; path=/; max-age=0; samesite=lax`;
}
