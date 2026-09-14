/** Admin panel veri sozlesmeleri (refactor R3). */
export interface UsageRow {
  username: string;
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cache_hit_tokens: number;
  cost_usd: string | number;
}

export interface UsageResponse {
  usage: UsageRow[];
}

export interface AdminConfig {
  b2c_model?: string;
  b2b_model?: string;
  pii_active?: string;
  pii_terms?: string;
  wizard_prompt?: string;
  persona_interview_prompt?: string;
  synthesis_prompt?: string;
  [key: string]: string | undefined;
}

export interface ClientInfo {
  username: string;
  email: string;
  plan_type: string;
  total_simulations: number;
  tokens_used: number;
  max_simulations: number;
  max_tokens: number;
  status: string;
  plan_start?: string;
  plan_end?: string;
  created_at?: string;
}

export interface PersonaInfo {
  id: string;
  name: string;
  age: number;
  city: string;
  segment: string;
  role_title?: string;
  is_global: boolean;
  ses_group?: string;
  respondent_type?: string;
  settlement_type?: string;
  stance?: string;
  bio?: string;
  traits?: string;
  attributes?: string;
  goals?: string;
  objections?: string;
  price_sensitivity?: number;
  digital_confidence?: number;
  is_locked?: boolean;
}

export interface AuditLog {
  id: string;
  created_at: string;
  study_id?: string;
  persona_name: string;
  error_reason: string;
  action_taken: string;
}

export interface CuratedQuestion {
  id: number;
  question: string;
  research_title?: string;
  research_category?: string;
  purpose_context?: string;
  is_liked: boolean;
  created_at?: string;
}

export interface FeedbackItem {
  id: number;
  username?: string;
  study_id?: string;
  item_type?: string;
  vote: number;
  comment?: string;
  created_at?: string;
}

export interface MetricsData {
  totals: { clients: number; tokens_used: number; tokens_capacity: number; simulations: number };
  plan_distribution: { plan_type: string; count: number; total_tokens: number; total_sims: number }[];
  clients: {
    username: string;
    plan_type: string;
    tokens_used: number;
    max_tokens: number;
    total_simulations: number;
    max_simulations: number;
    period_simulations: number;
  }[];
  study_stats: { total: number; avg_quality: number; with_report: number; archived: number; error_count: number };
  categories: { category: string; count: number }[];
  models: { b2c: string; b2b: string; orchestrator: string };
  persona_pool?: {
    total: number;
    top_used: { name: string; stance: string; ses_group: string; usage_count: number }[];
    stances: { stance: string; count: number }[];
  };
}

export interface SchemaField {
  key: string;
  type: string;
  required?: boolean;
  desc: string;
}

export interface AgentSchemas {
  brief_schema: {
    description: string;
    fields: SchemaField[];
    defaults: Record<string, string>;
  };
  persona_schema: { description: string; fields: SchemaField[] };
  interview_schema: { description: string; prompt_variables: string[]; output: Record<string, string> };
  synthesis_schema: { description: string; inputs: string[]; output_fields: string[] };
  default_interview_questions: string[];
  concept_pools: Record<string, { persona_name: string; focus_areas: string; questions: string[] }>;
}
