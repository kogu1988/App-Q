"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000";

export interface ClientPlan {
  username: string;
  plan_type: "Free" | "Starter" | "Pro" | "Enterprise";
  billing_cycle: "monthly" | "annual";
  period_start: string | null;
  limits: {
    max_personas: number;
    max_simulations: number;
  };
  features: Record<string, boolean>;
  total_simulations: number;
  period_simulations: number;
}

const DEFAULT_PLAN: ClientPlan = {
  username: "anonymous",
  plan_type: "Free",
  billing_cycle: "monthly",
  period_start: null,
  limits: { max_personas: 3, max_simulations: 2 },
  features: {
    ab_test: false,
    b2b_mode: false,
    streaming: false,
    pdf_export: false,
    adversarial: false,
    rfi: false,
    brand_health: false,
    ses_crosstab: false,
    custom_personas: false,
    fine_tuning_export: false,
    audit_log: false,
    multi_user: false,
    white_label: false,
  },
  total_simulations: 0,
  period_simulations: 0,
};

/**
 * Mevcut kullanıcının plan bilgisini /api/client/me endpoint'inden çeker.
 * X-Username header'ı localStorage'daki "username" değerinden okunur.
 */
export function useClientPlan() {
  const [plan, setPlan] = useState<ClientPlan>(DEFAULT_PLAN);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const username = localStorage.getItem("appq_username") || "";
    fetch(`${API_BASE}/api/client/me`, {
      headers: username ? { "X-Username": username } : {},
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setPlan(data);
      })
      .catch(() => {/* backend ulaşılamazsa Default Free kullan */})
      .finally(() => setLoading(false));
  }, []);

  return { plan, loading };
}
