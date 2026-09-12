/**
 * Paddle.js v2 entegrasyonu (P0-2).
 *
 * Paddle merchant of record'dur: ödemeyi alır ve aboneliği kendisi oluşturur.
 * Backend yalnızca price ID + müşteri bilgisi döner; abonelik webhook ile aktive olur.
 */

type PaddleEnvironment = "sandbox" | "production";

interface PaddleCheckoutItem {
  priceId: string;
  quantity: number;
}

interface PaddleCheckoutOptions {
  items: PaddleCheckoutItem[];
  customer?: { email?: string };
  customData?: Record<string, string>;
  settings?: {
    locale?: string;
    successUrl?: string;
    displayMode?: "overlay" | "inline";
  };
}

interface PaddleGlobal {
  Environment: { set: (env: PaddleEnvironment) => void };
  Initialize: (options: { token: string }) => void;
  Checkout: { open: (options: PaddleCheckoutOptions) => void };
}

declare global {
  interface Window {
    Paddle?: PaddleGlobal;
  }
}

export function paddleEnvironment(): PaddleEnvironment {
  return (process.env.NEXT_PUBLIC_PADDLE_ENV as PaddleEnvironment) || "sandbox";
}

export function isPaddleConfigured(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_PADDLE_CLIENT_TOKEN);
}

let initialized = false;

/** Paddle.js global'ini (varsa) yapılandırır. Birden fazla kez çağrılabilir. */
export function initPaddle(): boolean {
  if (typeof window === "undefined" || !window.Paddle) return false;
  if (initialized) return true;

  try {
    if (paddleEnvironment() === "sandbox") {
      window.Paddle.Environment.set("sandbox");
    }
    window.Paddle.Initialize({
      token: process.env.NEXT_PUBLIC_PADDLE_CLIENT_TOKEN as string,
    });
    initialized = true;
    return true;
  } catch {
    return false;
  }
}

/** Paddle checkout overlay'ini açar. */
export function openCheckout(
  priceId: string,
  email: string,
  username: string,
): boolean {
  if (typeof window === "undefined" || !window.Paddle) return false;
  if (!initPaddle()) return false;

  window.Paddle.Checkout.open({
    items: [{ priceId, quantity: 1 }],
    customer: email ? { email } : undefined,
    customData: { clarere_username: username },
    settings: {
      locale: "tr",
      displayMode: "overlay",
      successUrl: `${window.location.origin}/client?upgraded=1`,
    },
  });
  return true;
}
