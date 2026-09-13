import { synthesizeReportRequest, saveStudyRequest, fetchStudyDetail } from "../api/studies-api";
import type {
  Persona,
  PersonaInterview,
  ResearchBriefDetail,
  ResearchPlan,
  StudyDetail,
  StudyMetadata,
} from "../types";

interface SynthesizeParams {
  studyId: string;
  brief?: ResearchBriefDetail;
  metadata?: StudyMetadata;
  plan?: ResearchPlan;
  personas: Persona[];
  interviews: PersonaInterview[];
}

/**
 * Sentez raporunu üretir, çalışmaya kaydeder ve güncel detayı getirir
 * (refactor R2-6). Reload başarısız olursa `null` döner; hata fırlatmaz.
 */
export async function synthesizeAndSaveReport({
  studyId,
  brief,
  metadata,
  plan,
  personas,
  interviews,
}: SynthesizeParams): Promise<StudyDetail | null> {
  const res = await synthesizeReportRequest({
    brief: brief || { title: metadata?.title || "", market: "TR", category: metadata?.category || "genel", context: "" },
    plan: plan || {},
    interviews,
    personas,
  });
  if (!res.ok) throw new Error("Rapor olusturulamadi.");
  const report = await res.json();

  // Save report to study — spread report fields to top level
  const reportPayload = {
    brief, plan, personas, interviews,
    report_json: report,
    report_markdown: report.report_markdown || report.executive_summary?.join("\n") || "",
    report_html: report.report_html || "",
    findings: report.findings || [],
    action_items: report.action_items || [],
    recommendations: report.recommendations || [],
    limitations: report.limitations || [],
    pricing: report.pricing || null,
    van_westendorp: report.van_westendorp || null,
    brand_health: report.brand_health || null,
    pain_point_matrix: report.pain_point_matrix || [],
    ses_cross_tab: report.ses_cross_tab || [],
    research_quality: report.research_quality || null,
  };

  await saveStudyRequest({
    metadata: {
      ...metadata,
      has_report: true,
      quality_score: report.quality_score ?? metadata?.quality_score ?? 0,
      quality_grade: report.quality_grade ?? metadata?.quality_grade ?? "N/A",
    },
    payload: reportPayload,
  });

  // Reload study data (hata sessizce yok sayilir)
  return await fetchStudyDetail(studyId).catch(() => null);
}
