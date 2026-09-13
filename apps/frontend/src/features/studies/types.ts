/**
 * Study detay ekranının veri sözleşmeleri.
 *
 * Bu tipler backend Pydantic modellerini yansıtır ve `client/studies/[id]/page.tsx`
 * içinden çıkarılmıştır (refactor R1-5). Davranış değişikliği yoktur; yalnızca
 * tek bir kaynaktan yönetilir.
 */

export interface Persona {
  id: string;
  name: string;
  age: number;
  city: string;
  segment: string;
  stance: string;
  price_sensitivity: number;
  digital_confidence: number;
  context: string;
  goals: string[];
  objections: string[];
  bio: string;
  role_title?: string;
  ses_group?: string;
  respondent_type?: string;
  settlement_type?: string;
  big_five?: Record<string, number>;
  attributes?: Record<string, string>;
}

export interface InterviewTurn {
  question: string;
  answer: string;
  tags?: string[];
}

export interface PersonaInterview {
  persona: Persona;
  turns: InterviewTurn[];
  consistency_notes?: string[];
}

export interface ResearchPlan {
  objective?: string;
  assumptions?: string[];
  interview_questions?: string[];
  recommended_panel_size?: number;
}

export interface SesCrossTabRow {
  ses_group: string;
  total: number;
  dominant_stance: string;
  stance_counts: Record<string, number>;
}

export interface RespondentTypeSummary {
  respondent_type: string;
  label: string;
  count: number;
  avg_price_sensitivity: number;
  top_pain: string | null;
  top_objection: string | null;
}

export interface VanWestendorp {
  too_cheap_values: number[];
  cheap_values: number[];
  expensive_values: number[];
  too_expensive_values: number[];
  opp: number;
  ipp: number;
  pmc: number;
  pme: number;
  acceptable_range: [number, number];
  currency: string;
  methodology_note: string;
}

export interface BrandHealth {
  unaided_recall: Record<string, number>;
  associations: Record<string, string[]>;
  top_of_mind: string | null;
  total_mentions: number;
}

export interface ChannelMapItem {
  channel: string;
  count: number;
  pct: number;
}

export interface ResearchQualityFlag {
  phase: string;
  severity: string;
  code: string;
  message: string;
  finding?: string;
  suggested_confidence?: number;
  suggested_step?: string;
}

export interface ResearchQuality {
  // Eski format (backward compat)
  overall_score?: number;
  grade?: string;
  bias_flags?: Record<string, string[]>;
  straight_lining_count?: number;
  acquiescence_count?: number;
  social_desirability_count?: number;
  summary?: string;
  // Yeni adversarial review format (Grounded Simulation)
  flags?: ResearchQualityFlag[];
  flag_count?: number;
  warning_count?: number;
  phases_passed?: string[];
  phases_flagged?: string[];
  // RFI
  rfi?: number;
  components?: Record<string, number>;
  valid?: boolean;
  validity_threshold?: number;
  interpretation?: string;
}

export interface FindingEvidence {
  persona_id: string;
  persona_name: string;
  stance: string;
  question: string;
  quote: string;
  sentiment: string;
}

export interface StudyFinding {
  id: number;
  title: string;
  category: string;
  summary: string;
  confidence: number;
  implication: string;
  supporting_count: number;
  refuting_count: number;
  neutral_count: number;
  contradiction_score: number;
  decision_signal: string;
  evidence?: FindingEvidence[];
}

export interface DecisionItem {
  signal: string;
  title: string;
  confidence: number;
  supporting_count: number;
  refuting_count: number;
  evidence_summary: string;
  recommended_action: string;
}

export interface ExternalEvidence {
  finding_title: string;
  source_title: string;
  source_url: string;
  snippet: string;
  relevance: string;
}

export interface ReportMetrics {
  findings_total?: number;
  findings_with_evidence?: number;
  unsourced_findings?: number;
  evidence_total?: number;
  evidence_per_finding?: number;
  unique_personas_in_evidence?: number;
  refuting_ratio?: number;
  answer_completion_rate?: number;
  external_evidence_count?: number;
  decision_signals?: Record<string, number>;
}

export interface StudyMetadata {
  id: string;
  title: string;
  market: string;
  category: string;
  created_at: string;
  updated_at: string;
  has_report: boolean;
  quality_score?: number;
  quality_grade?: string;
  quality_summary?: string;
}

export interface ResearchBriefDetail {
  title: string;
  market?: string;
  category?: string;
  idea?: string;
  expected_price?: string;
  target_users?: string[];
  competitors?: string[];
  success_metric?: string;
  sales_channel?: string;
  discovery_channels?: string[];
  panel_size?: string;
  geography?: string;
}

export interface StudyDetail {
  metadata?: StudyMetadata;
  brief?: ResearchBriefDetail;
  plan?: ResearchPlan;
  personas?: Persona[];
  interviews?: PersonaInterview[];
  report_markdown?: string;
  report_html?: string;
  ses_cross_tab?: SesCrossTabRow[];
  respondent_type_summary?: RespondentTypeSummary[];
  van_westendorp?: VanWestendorp;
  brand_health?: BrandHealth;
  channel_map?: ChannelMapItem[];
  research_quality?: ResearchQuality;
  findings?: StudyFinding[];
  recommendations?: string[];
  action_items?: string[];
  decision_items?: DecisionItem[];
  external_evidence?: ExternalEvidence[];
  report_metrics?: ReportMetrics;
}
