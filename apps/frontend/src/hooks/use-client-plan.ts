"use client";

import { useState, useEffect } from "react";
import { getAuthHeaders } from "@/lib/auth";



export interface ClientPlan {
  username: string;
  plan_type: "Free" | "Flex" | "Starter" | "Pro" | "Enterprise";
  billing_cycle: "monthly" | "annual";
  period_start: string | null;
  limits: {
    max_personas: number;
    max_simulations: number;
  };
  features: Record<string, boolean>;
  total_simulations: number;
  period_simulations: number;
  trial_expired?: boolean;
  trial_expired_reason?: string;
}

const DEFAULT_PLAN: ClientPlan = {
  username: "anonymous",
  plan_type: "Free",
  billing_cycle: "monthly",
  period_start: null,
  limits: { max_personas: 10, max_simulations: 2 },
  features: {
    ab_test: false,
    b2b_mode: false,
    streaming: false,
    pdf_export: false,
    adversarial: true,
    rfi: true,
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
    fetch(`/api/client/me`, {
      headers: getAuthHeaders(),
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
