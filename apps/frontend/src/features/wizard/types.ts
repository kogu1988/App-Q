/** Sihirbaz veri sozlesmeleri (refactor R4-3). */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface Brief {
  title?: string;
  market?: string;
  category?: string;
  idea?: string;
  target_users?: string | string[];
  questions?: string | string[];
  competitors?: string | string[];
  expected_price?: string;
  sales_channel?: string;
  success_metric?: string;
  variant_a?: string;
  variant_b?: string;
}

/** Backend bazen string, bazen string[] döner — her ikisini de handle eder */
export const toArray = (val: string | string[] | undefined): string[] => {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  return [val];
};


export type ResearchResult = {
  plan?: unknown;
  personas?: unknown[];
  interviews?: unknown[];
};
