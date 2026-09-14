"use client";

import { useState, useEffect, useRef, useCallback, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { toast } from "sonner";
import { getAdminHeaders } from "@/lib/auth";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, Loader2, Trash2, Eye, AlertTriangle } from "lucide-react";

// Big Five kaydırıcı alanları — dar (narrow) tipleme; `any` yerine güvenli indeksleme.
type BigFiveSliderKey =
  | "openness"
  | "conscientiousness"
  | "extroversion"
  | "agreeableness"
  | "neuroticism";
const BIG_FIVE_SLIDERS: { label: string; field: BigFiveSliderKey; color: string }[] = [
  { label: "Openness (Deneyime Açıklık)", field: "openness", color: "accent-blue-500" },
  { label: "Conscientiousness (Sorumluluk)", field: "conscientiousness", color: "accent-emerald-500" },
  { label: "Extraversion (Dışadönüklük)", field: "extroversion", color: "accent-amber-500" },
  { label: "Agreeableness (Geçimlilik)", field: "agreeableness", color: "accent-rose-500" },
  { label: "Neuroticism (Duygusal Dengesizlik)", field: "neuroticism", color: "accent-red-500" },
];

interface PersonaInfo {
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

function InfoTooltip({ text, position = "top" }: { text: string; position?: "top" | "bottom" }) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  // Hydration güvenli "istemci mi?" kontrolü — effect içinde setState YERİNE.
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  const updateCoordinates = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;

    if (position === "top") {
      setCoords({
        top: rect.top + scrollY - 8,
        left: rect.left + scrollX + rect.width / 2,
      });
    } else {
      setCoords({
        top: rect.bottom + scrollY + 8,
        left: rect.left + scrollX + rect.width / 2,
      });
    }
  }, [position]);

  const handleMouseEnter = () => {
    updateCoordinates();
    setVisible(true);
  };

  const handleMouseLeave = () => {
    setVisible(false);
  };

  useEffect(() => {
    if (!visible) return;
    window.addEventListener("scroll", updateCoordinates, { passive: true });
    window.addEventListener("resize", updateCoordinates, { passive: true });
    return () => {
      window.removeEventListener("scroll", updateCoordinates);
      window.removeEventListener("resize", updateCoordinates);
    };
  }, [visible, updateCoordinates]);

  const isTop = position === "top";

  return (
    <div
      ref={triggerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className="relative inline-flex items-center ml-1.5 align-middle z-10"
    >
      <div className="flex items-center justify-center w-4 h-4 rounded-full bg-soft-stone text-body-muted text-[12px] cursor-help font-medium hover:bg-hairline transition-colors">
        ?
      </div>
      {visible && mounted && createPortal(
        <div
          style={{
            position: "absolute",
            top: `${coords.top}px`,
            left: `${coords.left}px`,
            transform: isTop ? "translate(-50%, -100%)" : "translate(-50%, 0%)",
          }}
          className="w-64 px-3 py-2 bg-primary border border-ink text-white text-[12px] rounded-[8px] transition-opacity duration-200 z-[999999] pointer-events-none font-normal normal-case leading-relaxed text-center shadow-xl"
        >
          {text}
          {isTop ? (
            <>
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-primary" />
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-ink -z-10 mt-[1px]" />
            </>
          ) : (
            <>
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-b-primary" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-b-ink -z-10 mb-[1px]" />
            </>
          )}
        </div>,
        document.body
      )}
    </div>
  );
}

const parseJsonField = <T,>(field: string | undefined | null | object, fallback: T): T => {
  if (!field) return fallback;
  if (typeof field === "object") return field as T;
  try {
    return JSON.parse(field as string) as T;
  } catch {
    return fallback;
  }
};

interface TraitsJson {
  openness?: number | string;
  Openness?: number | string;
  conscientiousness?: number | string;
  Conscientiousness?: number | string;
  extroversion?: number | string;
  Extroversion?: number | string;
  agreeableness?: number | string;
  Agreeableness?: number | string;
  neuroticism?: number | string;
  Neuroticism?: number | string;
}

interface AttributesJson {
  personality?: TraitsJson;
}
const parseNumber = (val: string | number | undefined | null, fallback = 50): number => {
  if (typeof val === "number") return val;
  if (!val) return fallback;
  const parsed = parseInt(String(val));
  return isNaN(parsed) ? fallback : parsed;
};

const getBigFive = (p: PersonaInfo) => {
  const traits = parseJsonField<TraitsJson>(p.traits, {});
  if (traits && typeof traits === "object") {
    const o = traits.openness ?? traits.Openness;
    const c = traits.conscientiousness ?? traits.Conscientiousness;
    const e = traits.extroversion ?? traits.Extroversion;
    const a = traits.agreeableness ?? traits.Agreeableness;
    const n = traits.neuroticism ?? traits.Neuroticism;
    if (o !== undefined) {
      return {
        openness: parseNumber(o),
        conscientiousness: parseNumber(c),
        extroversion: parseNumber(e),
        agreeableness: parseNumber(a),
        neuroticism: parseNumber(n),
      };
    }
  }

  const attrs = parseJsonField<AttributesJson>(p.attributes, {});
  if (attrs && attrs.personality) {
    const o = attrs.personality.openness ?? attrs.personality.Openness;
    const c = attrs.personality.conscientiousness ?? attrs.personality.Conscientiousness;
    const e = attrs.personality.extroversion ?? attrs.personality.Extroversion;
    const a = attrs.personality.agreeableness ?? attrs.personality.Agreeableness;
    const n = attrs.personality.neuroticism ?? attrs.personality.Neuroticism;
    if (o !== undefined) {
      return {
        openness: parseNumber(o),
        conscientiousness: parseNumber(c),
        extroversion: parseNumber(e),
        agreeableness: parseNumber(a),
        neuroticism: parseNumber(n),
      };
    }
  }

  const s = p.stance || "";
  const openness = s === "Innovator" ? 90 : s === "EarlyAdopter" ? 75 : s === "Laggard" ? 25 : 50;
  const conscientiousness = p.ses_group === "AB" || p.ses_group === "C1" ? 80 : 45;
  const agreeableness = s === "Skeptic" ? 20 : s === "Innovator" ? 40 : 60;
  const neuroticism = s === "Skeptic" ? 85 : s === "Innovator" && p.ses_group === "AB" ? 20 : 50;
  const extroversion = s === "EarlyAdopter" || s === "Innovator" ? 85 : 50;

  return { openness, conscientiousness, extroversion, agreeableness, neuroticism };
};

export function PersonasTab({ personas, onRefresh }: { personas: PersonaInfo[]; onRefresh: () => void }) {
  const [deletingPersona, setDeletingPersona] = useState<string | null>(null);
  const [deletePersonaTarget, setDeletePersonaTarget] = useState<string | null>(null);
  const [deletePersonaName, setDeletePersonaName] = useState<string>("");
  const [poolPage, setPoolPage] = useState(1);

  // Two-Tier Manual Persona Wizard States
  const [manualOpen, setManualOpen] = useState(false);
  const [resetAlertOpen, setResetAlertOpen] = useState(false);
  const [savingManual, setSavingManual] = useState(false);
  const [generatingDraft, setGeneratingDraft] = useState(false);
  const [wizardMode, setWizardMode] = useState<"grounded" | "sandbox">("grounded");

  const [manualForm, setManualForm] = useState({
    name: "",
    age: 30,
    city: "İstanbul",
    segment: "",
    role_title: "",
    respondent_type: "potential_customer",
    settlement_type: "kentsel",
    stance: "Mainstream",
    ses_group: "C1",
    price_sensitivity: 5,
    digital_confidence: 6,
    is_global: true,
    bio: "",
    goals: "",
    objections: "",
    pazarlik_propensity: 0.5,
    taksit_preference: true,
    sor_osca_threshold: 0.5,
    credit_card_limit_doluluk: 0.5,
    openness: 50,
    conscientiousness: 50,
    extroversion: 50,
    agreeableness: 60,
    neuroticism: 50,
  });

  const getGroundedBigFive = (stance: string, sesGroup: string, priceSens: number, digConf: number) => {
    const seed = 1;
    const stanceMods: Record<string, { agreeableness_mod: number; openness_mod: number; neuroticism_mod: number }> = {
      Innovator: { agreeableness_mod: 4, openness_mod: 20, neuroticism_mod: -15 },
      EarlyAdopter: { agreeableness_mod: 3, openness_mod: 10, neuroticism_mod: -5 },
      Mainstream: { agreeableness_mod: 0, openness_mod: 0, neuroticism_mod: 0 },
      Laggard: { agreeableness_mod: -5, openness_mod: -25, neuroticism_mod: 10 },
      Skeptic: { agreeableness_mod: -10, openness_mod: -10, neuroticism_mod: 15 },
    };
    const profile = stanceMods[stance] || stanceMods.Mainstream;
    const varMod = (seed * 7 % 13) - 6;

    const agreeableness = Math.min(100, Math.max(1, 60 + profile.agreeableness_mod + varMod));
    const openness = Math.min(100, Math.max(1, digConf * 9 + 5 + profile.openness_mod));
    const conscientiousness = Math.min(100, Math.max(1, 62 + (seed * 7 % 28)));
    const extroversion = Math.min(100, Math.max(1, 42 + (seed * 5 % 35)));
    const neuroticism = Math.min(100, Math.max(1, priceSens * 7 + 8 + profile.neuroticism_mod));

    return { openness, conscientiousness, extroversion, agreeableness, neuroticism };
  };

  useEffect(() => {
    if (wizardMode === "grounded") {
      const grounded = getGroundedBigFive(
        manualForm.stance,
        manualForm.ses_group,
        manualForm.price_sensitivity,
        manualForm.digital_confidence
      );
      
      const pazarlik = manualForm.price_sensitivity >= 7 ? 0.8 : 0.3;
      const ccLimit = manualForm.ses_group === "DE" ? 0.85 : manualForm.ses_group === "C2" ? 0.65 : 0.40;
      
      // grounded modda türetilen Big Five değerlerini forma yansıtır; bilinçli senkron.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setManualForm(f => ({
        ...f,
        openness: grounded.openness,
        conscientiousness: grounded.conscientiousness,
        extroversion: grounded.extroversion,
        agreeableness: grounded.agreeableness,
        neuroticism: grounded.neuroticism,
        pazarlik_propensity: pazarlik,
        credit_card_limit_doluluk: ccLimit,
        sor_osca_threshold: 0.5,
      }));
    }
  }, [wizardMode, manualForm.stance, manualForm.ses_group, manualForm.price_sensitivity, manualForm.digital_confidence]);

  const handleWizardModeChange = (mode: "grounded" | "sandbox") => {
    if (mode === "grounded" && wizardMode === "sandbox") {
      setResetAlertOpen(true);
    } else {
      setWizardMode(mode);
    }
  };

  const confirmResetToGrounded = () => {
    setWizardMode("grounded");
    setResetAlertOpen(false);
    toast.success("Bilimsel varsayılan ayarlar geri yüklendi.");
  };

  const handleGenerateDraft = async () => {
    setGeneratingDraft(true);
    try {
      const res = await fetch("/api/admin/personas/draft", { headers: getAdminHeaders() });
      if (!res.ok) throw new Error();
      const data = await res.json();
      const draft = data.draft;
      
      setManualForm(f => ({
        ...f,
        name: draft.name || f.name,
        age: draft.age || f.age,
        city: draft.city || f.city,
        segment: draft.segment || f.segment,
        stance: draft.stance || f.stance,
        ses_group: draft.ses_group || f.ses_group,
        respondent_type: draft.respondent_type || f.respondent_type,
        settlement_type: draft.settlement_type || f.settlement_type,
        bio: draft.bio || f.bio,
        goals: draft.goals || f.goals,
        objections: draft.objections || f.objections,
      }));
      toast.success("Sürpriz taslak üretildi! Değerleri inceleyip kaydedebilirsiniz.");
    } catch {
      toast.error("Taslak persona üretimi başarısız oldu.");
    } finally {
      setGeneratingDraft(false);
    }
  };

  const handleSubmitManual = async () => {
    if (!manualForm.name.trim() || !manualForm.segment.trim()) {
      toast.error("Lütfen İsim ve Rol/Segment alanlarını doldurun.");
      return;
    }
    setSavingManual(true);
    try {
      const goalsList = manualForm.goals.split(",").map(s => s.trim()).filter(Boolean);
      const objectionsList = manualForm.objections.split(",").map(s => s.trim()).filter(Boolean);
      
      const payload = {
        name: manualForm.name,
        age: Number(manualForm.age),
        city: manualForm.city,
        segment: manualForm.segment,
        role_title: manualForm.role_title || manualForm.segment,
        respondent_type: manualForm.respondent_type,
        settlement_type: manualForm.settlement_type,
        stance: manualForm.stance,
        ses_group: manualForm.ses_group,
        price_sensitivity: Number(manualForm.price_sensitivity),
        digital_confidence: Number(manualForm.digital_confidence),
        is_global: manualForm.is_global,
        bio: manualForm.bio,
        goals: goalsList,
        objections: objectionsList,
        pazarlik_propensity: Number(manualForm.pazarlik_propensity),
        taksit_preference: manualForm.taksit_preference,
        sor_osca_threshold: Number(manualForm.sor_osca_threshold),
        credit_card_limit_doluluk: Number(manualForm.credit_card_limit_doluluk),
        traits: {
          Openness: manualForm.openness,
          Conscientiousness: manualForm.conscientiousness,
          Extraversion: manualForm.extroversion,
          Agreeableness: manualForm.agreeableness,
          Neuroticism: manualForm.neuroticism
        }
      };

      const res = await fetch("/api/admin/personas/create", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAdminHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error();
      toast.success("Yeni sentetik persona başarıyla havuzuna eklendi.");
      setManualOpen(false);
      
      setManualForm({
        name: "",
        age: 30,
        city: "İstanbul",
        segment: "",
        role_title: "",
        respondent_type: "potential_customer",
        settlement_type: "kentsel",
        stance: "Mainstream",
        ses_group: "C1",
        price_sensitivity: 5,
        digital_confidence: 6,
        is_global: true,
        bio: "",
        goals: "",
        objections: "",
        pazarlik_propensity: 0.5,
        taksit_preference: true,
        sor_osca_threshold: 0.5,
        credit_card_limit_doluluk: 0.5,
        openness: 50,
        conscientiousness: 50,
        extroversion: 50,
        agreeableness: 60,
        neuroticism: 50,
      });
      setWizardMode("grounded");
      onRefresh();
    } catch {
      toast.error("Manuel persona kaydı başarısız oldu.");
    } finally {
      setSavingManual(false);
    }
  };

  const handleDeletePersona = async (personaId: string) => {
    setDeletingPersona(personaId);
    try {
      const res = await fetch(`/api/admin/personas/${personaId}`, {
        method: "DELETE",
        headers: getAdminHeaders(),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Silme işlemi başarısız oldu.");
      }
      toast.success("Persona havuzdan silindi.");
      setDeletePersonaTarget(null);
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Persona silinemedi.";
      toast.error(msg);
    } finally {
      setDeletingPersona(null);
    }
  };

  return (
    <div className="mt-6 flex-1 outline-none">
      <div className="mb-6">
        <p className="text-sm text-body-muted dark:text-muted-text">
          Global ve müşteri özel durumlar için sisteme yüklenmiş tüm sentetik kullanıcılar.
        </p>
      </div>
      
      <div className="flex justify-between items-center mb-2">
        <Dialog open={manualOpen} onOpenChange={setManualOpen}>
          <DialogTrigger render={
            <Button className="gap-2 bg-primary text-white hover:opacity-85 h-9">
              <Plus size={16} />
              Manuel Persona Ekle
            </Button>
          } />
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto bg-background text-foreground">
                  {/* Transition Reset Alert Overlay */}
                  {resetAlertOpen && (
                    <div className="absolute inset-0 bg-background/95 backdrop-blur-sm z-[100] flex flex-col items-center justify-center p-6 text-center animate-in fade-in">
                      <div className="max-w-sm space-y-4">
                        <h4 className="text-sm font-bold">Bilimsel Varsayılanlara Dönülsün mü?</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Bilimsel moda dönerseniz yaptığınız tüm özel psikolojik katsayı ve slider değişiklikleri silinerek bilimsel varsayılanlar geri yüklenecektir.
                        </p>
                        <div className="flex gap-2 justify-center">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs h-8 text-ink"
                            onClick={() => setResetAlertOpen(false)}
                          >
                            İptal
                          </Button>
                          <Button
                            size="sm"
                            className="text-xs h-8 bg-red-600 hover:bg-red-700 text-white border-none"
                            onClick={confirmResetToGrounded}
                          >
                            Evet, Sıfırla
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  <DialogHeader className="pb-3 border-b border-border">
                    <DialogTitle className="text-base font-bold">
                      Manuel Sentetik Persona Ekle
                    </DialogTitle>
                    <DialogDescription className="text-xs text-muted-foreground mt-1">
                      Havuzunuza ve özel araştırmalarınıza dahil etmek üzere yeni bir sentetik tüketici oluşturun.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-4 mt-4 text-left">
                    <div className="flex items-end justify-between gap-4">
                      {/* Segmented Control Wizard Toggle (Stark Monochrome Style) */}
                      <div className="space-y-1.5 flex-1">
                        <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">
                          Sihirbaz Modu
                        </Label>
                        <div className="flex border border-border rounded-lg p-0.5 max-w-xs bg-muted/20">
                          <button
                            type="button"
                            onClick={() => handleWizardModeChange("grounded")}
                            className={`flex-1 text-[10px] font-bold py-1 px-3 rounded-md transition-colors ${
                              wizardMode === "grounded" ? "bg-primary text-white" : "text-body-muted hover:text-primary"
                            }`}
                          >
                            Bilimsel (Grounded)
                          </button>
                          <button
                            type="button"
                            onClick={() => handleWizardModeChange("sandbox")}
                            className={`flex-1 text-[10px] font-bold py-1 px-3 rounded-md transition-colors ${
                              wizardMode === "sandbox" ? "bg-primary text-white" : "text-body-muted hover:text-primary"
                            }`}
                          >
                            Serbest (Sandbox)
                          </button>
                        </div>
                      </div>

                      {/* Random Persona Generator Button */}
                      <div className="pb-[2px]">
                        <button
                          type="button"
                          onClick={handleGenerateDraft}
                          disabled={generatingDraft}
                          className="flex items-center justify-center gap-1.5 text-[10px] font-bold py-1 px-4 rounded-md border border-primary bg-white hover:bg-primary hover:text-white text-primary transition-colors h-[28px] shadow-sm disabled:opacity-50"
                        >
                          {generatingDraft ? <Loader2 size={12} className="animate-spin" /> : <span className="text-[10px]">✨</span>}
                          {generatingDraft ? "Üretiliyor..." : "AI ile Doldur"}
                        </button>
                      </div>
                    </div>

                    {/* Minimal Monospaced Warning Box inside Sandbox Mode */}
                    {wizardMode === "sandbox" && (
                      <div className="border border-ink bg-primary/5 rounded-lg p-3 text-[11px] text-ink font-mono leading-relaxed">
                        <strong className="block text-red-700 font-bold mb-0.5">⚠️ DİKKAT: Sandbox Modu Aktif</strong>
                        Manuel yaptığınız değişiklikler (örn: şüpheci kişilik için yüksek geçimlilik girmek) Türkiye pazarı tüketici eğilimleri veya psikometrik katsayılarla çelişebilir. Bu kombinasyonun bilimsel doğruluğu ve simülasyon gerçekçiliği garanti edilmez.
                      </div>
                    )}

                    {wizardMode === "grounded" && (
                      <div className="border border-border bg-emerald-50/20 text-emerald-800 rounded-lg p-3 text-[11px] leading-relaxed">
                        <strong>🛡️ Bilimsel (Grounded) Mod Aktif:</strong> Big Five OCEAN kişilik özellikleri ve yerel refleks katsayıları seçtiğiniz Rogers inovasyon tipi, SES grubu ve hassasiyetlere göre deterministik olarak otomatik kalibre edilir.
                      </div>
                    )}

                    {/* Section 1: Demographics */}
                    <div className="space-y-3">
                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text pb-1 border-b border-border/50">
                        1. Demografik Kimlik Bilgileri
                      </h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">İsim</Label>
                          <Input
                            value={manualForm.name}
                            onChange={e => setManualForm(f => ({ ...f, name: e.target.value }))}
                            placeholder="Örn: Ahmet Yılmaz"
                            className="h-8 text-xs bg-background text-foreground"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Yaş (18-65)</Label>
                          <Input
                            type="number"
                            min={18}
                            max={75}
                            value={manualForm.age}
                            onChange={e => setManualForm(f => ({ ...f, age: +e.target.value }))}
                            className="h-8 text-xs bg-background text-foreground"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Şehir</Label>
                          <Input
                            value={manualForm.city}
                            onChange={e => setManualForm(f => ({ ...f, city: e.target.value }))}
                            placeholder="Örn: İstanbul, Ankara"
                            className="h-8 text-xs bg-background text-foreground"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Rol / Segment</Label>
                          <Input
                            value={manualForm.segment}
                            onChange={e => setManualForm(f => ({ ...f, segment: e.target.value }))}
                            placeholder="Örn: Ev Hanımı, E-ticaret Satıcısı"
                            className="h-8 text-xs bg-background text-foreground"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Katılımcı Tipi</Label>
                          <select
                            value={manualForm.respondent_type}
                            onChange={e => setManualForm(f => ({ ...f, respondent_type: e.target.value }))}
                            className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground cursor-pointer focus:ring-1 focus:ring-primary"
                          >
                            <option value="potential_customer">Potansiyel Müşteri</option>
                            <option value="competitor_user">Rakip Kullanıcı</option>
                            <option value="churned_user">Kaybedilmiş Kullanıcı</option>
                            <option value="decision_maker">Karar Verici</option>
                            <option value="individual_user">Bireysel / Genel Tüketici</option>
                          </select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Yerleşim Tipi</Label>
                          <select
                            value={manualForm.settlement_type}
                            onChange={e => setManualForm(f => ({ ...f, settlement_type: e.target.value }))}
                            className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground cursor-pointer focus:ring-1 focus:ring-primary"
                          >
                            <option value="kentsel">Kentsel (Metropol)</option>
                            <option value="banliyö">Banliyö (Şehir Çeperi)</option>
                            <option value="kırsal">Kırsal (Taşra)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Section 2: Grounded Parameters */}
                    <div className="space-y-3">
                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text pb-1 border-b border-border/50">
                        2. Tüketici Tipi & Kültürel Parametreler
                      </h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Rogers İnovasyon Tipi</Label>
                          <select
                            value={manualForm.stance}
                            onChange={e => setManualForm(f => ({ ...f, stance: e.target.value }))}
                            className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground cursor-pointer focus:ring-1 focus:ring-primary"
                          >
                            <option value="Innovator">Yenilikçi (Innovator)</option>
                            <option value="EarlyAdopter">Erken Benimseyen (Early Adopter)</option>
                            <option value="Mainstream">Çoğunluk (Mainstream)</option>
                            <option value="Laggard">Gelenekçi (Laggard)</option>
                            <option value="Skeptic">Şüpheci (Skeptic)</option>
                          </select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Sosyoekonomik Sınıf (SES)</Label>
                          <select
                            value={manualForm.ses_group}
                            onChange={e => setManualForm(f => ({ ...f, ses_group: e.target.value }))}
                            className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground cursor-pointer focus:ring-1 focus:ring-primary"
                          >
                            <option value="AB">AB — Üst Grup (%21.5)</option>
                            <option value="C1">C1 — Üst-Orta Grup (%22.4)</option>
                            <option value="C2">C2 — Alt-Orta Grup (%32.5)</option>
                            <option value="DE">DE — Alt Grup (%23.6)</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Fiyat Hassasiyeti (1-10)</Label>
                          <select
                            value={manualForm.price_sensitivity}
                            onChange={e => setManualForm(f => ({ ...f, price_sensitivity: +e.target.value }))}
                            className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground cursor-pointer focus:ring-1 focus:ring-primary"
                          >
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
                              <option key={n} value={n}>{n} / 10</option>
                            ))}
                          </select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Dijital Özgüven (1-10)</Label>
                          <select
                            value={manualForm.digital_confidence}
                            onChange={e => setManualForm(f => ({ ...f, digital_confidence: +e.target.value }))}
                            className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground cursor-pointer focus:ring-1 focus:ring-primary"
                          >
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
                              <option key={n} value={n}>{n} / 10</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Section 3: OCEAN Personality */}
                    <div className="space-y-3">
                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text pb-1 border-b border-border/50">
                        3. Beş Büyük Kişilik Özelliği (OCEAN)
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2.5 bg-muted-surface dark:bg-primary border border-border/40 p-3 rounded-xl">
                        {BIG_FIVE_SLIDERS.map(item => (
                          <div key={item.field} className="space-y-1">
                            <div className="flex justify-between text-[10px] font-medium text-body-muted dark:text-muted-text">
                              <span>{item.label}</span>
                              <span className="font-bold">%{manualForm[item.field]}</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={manualForm[item.field]}
                              disabled={wizardMode === "grounded"}
                              onChange={e => setManualForm(f => ({ ...f, [item.field]: +e.target.value }))}
                              className={`w-full h-1 bg-hairline dark:bg-surface-dark rounded-lg appearance-none cursor-pointer ${item.color} disabled:opacity-60 disabled:cursor-not-allowed`}
                            />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Section 4: Enterprise Local Reflexes (Sandbox only) */}
                    {wizardMode === "sandbox" && (
                      <div className="space-y-3">
                        <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text pb-1 border-b border-border/50">
                          4. Gelişmiş Türkiye İşlem Refleksleri (Enterprise)
                        </h4>
                        <div className="grid grid-cols-2 gap-3 bg-muted/10 border border-border/40 p-3 rounded-xl">
                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] font-medium text-body-muted">
                              <span>Pazarlık Eğilimi (Bargaining)</span>
                              <span className="font-bold">%{Math.round(manualForm.pazarlik_propensity * 100)}</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.05"
                              value={manualForm.pazarlik_propensity}
                              onChange={e => setManualForm(f => ({ ...f, pazarlik_propensity: +e.target.value }))}
                              className="w-full h-1 bg-hairline rounded-lg appearance-none cursor-pointer accent-primary"
                            />
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] font-medium text-body-muted">
                              <span>Kargo Sepet Terk (S-O-R Logit)</span>
                              <span className="font-bold">%{Math.round(manualForm.sor_osca_threshold * 100)}</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.05"
                              value={manualForm.sor_osca_threshold}
                              onChange={e => setManualForm(f => ({ ...f, sor_osca_threshold: +e.target.value }))}
                              className="w-full h-1 bg-hairline rounded-lg appearance-none cursor-pointer accent-primary"
                            />
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] font-medium text-body-muted">
                              <span>Kart Limit Doluluğu (Limit VRAM)</span>
                              <span className="font-bold">%{Math.round(manualForm.credit_card_limit_doluluk * 100)}</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.05"
                              value={manualForm.credit_card_limit_doluluk}
                              onChange={e => setManualForm(f => ({ ...f, credit_card_limit_doluluk: +e.target.value }))}
                              className="w-full h-1 bg-hairline rounded-lg appearance-none cursor-pointer accent-primary"
                            />
                          </div>

                          <div className="space-y-1">
                            <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text block mb-1">Enflasyon Taksit Tercihi</Label>
                            <select
                              value={manualForm.taksit_preference ? "true" : "false"}
                              onChange={e => setManualForm(f => ({ ...f, taksit_preference: e.target.value === "true" }))}
                              className="w-full h-8 text-xs border border-border rounded-lg px-2 bg-background text-foreground"
                            >
                              <option value="true">Taksit İstiyor (%71)</option>
                              <option value="false">Tek Çekim İstiyor</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Section 5: Bio, Goals, Objections */}
                    <div className="space-y-3">
                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text pb-1 border-b border-border/50">
                        {wizardMode === "sandbox" ? "5. Yaşam Konsepti & Hedefler" : "4. Yaşam Konsepti & Hedefler"}
                      </h4>
                      <div className="space-y-2">
                        <div className="space-y-1">
                          <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">Biyografi & Hikaye</Label>
                          <textarea
                            value={manualForm.bio}
                            onChange={e => setManualForm(f => ({ ...f, bio: e.target.value }))}
                            placeholder="Personanın hayata bakış açısı, alışveriş alışkanlıkları ve pazar hedeflerine dair 2-3 cümle..."
                            className="w-full min-h-[60px] text-xs p-2 border border-border rounded-lg bg-background text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
                          />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-1">
                            <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">
                              Amaçlar / Hedefler
                              <span className="text-[9px] lowercase font-normal text-muted-foreground ml-1">(virgülle ayırın)</span>
                            </Label>
                            <Input
                              value={manualForm.goals}
                              onChange={e => setManualForm(f => ({ ...f, goals: e.target.value }))}
                              placeholder="Örn: Hızlı ödeme, Taksit bulma"
                              className="h-8 text-xs bg-background text-foreground"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">
                              Tüketici İtirazları
                              <span className="text-[9px] lowercase font-normal text-muted-foreground ml-1">(virgülle ayırın)</span>
                            </Label>
                            <Input
                              value={manualForm.objections}
                              onChange={e => setManualForm(f => ({ ...f, objections: e.target.value }))}
                              placeholder="Örn: Yüksek kargo, KVKK şüphesi"
                              className="h-8 text-xs bg-background text-foreground"
                            />
                          </div>
                        </div>

                        <div className="flex items-center gap-2 pt-2">
                          <input
                            type="checkbox"
                            id="is_global"
                            checked={manualForm.is_global}
                            onChange={e => setManualForm(f => ({ ...f, is_global: e.target.checked }))}
                            className="rounded border-border text-primary focus:ring-primary w-3.5 h-3.5"
                          />
                          <Label htmlFor="is_global" className="text-xs text-muted-foreground font-semibold cursor-pointer">
                            Bu personayı tüm kullanıcılara açık (Global) yap
                          </Label>
                        </div>
                      </div>
                    </div>

                    <Button
                      onClick={handleSubmitManual}
                      disabled={savingManual || !manualForm.name || !manualForm.segment}
                      className="w-full bg-deep-green hover:opacity-85 text-white h-9 text-xs font-semibold mt-3"
                    >
                      {savingManual ? (
                        <>
                          <Loader2 size={12} className="animate-spin" />
                          Havuzuna Kaydediliyor...
                        </>
                      ) : (
                        "Sentetik Personayı Kaydet"
                      )}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
      </div>

      <Card className="border-hairline shadow-sm h-full">
        <CardContent className="pt-4">
              <div className="overflow-x-auto w-full">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>
                        İsim & Yaş <InfoTooltip text="Yapay zeka tarafından üretilen benzersiz isim ve yaş." position="bottom" />
                      </TableHead>
                      <TableHead>
                        Lokasyon{" "}
                        <InfoTooltip text="Personanın ikamet ettiği şehir. Persona üretirken girilen 'Hedef Pazar'a göre şekillenir." position="bottom" />
                      </TableHead>
                      <TableHead>
                        Rol / Segment{" "}
                        <InfoTooltip text="Personanın sosyokültürel veya mesleki kimliği. Üretimdeki 'Rol Başlığı'ndan gelir." position="bottom" />
                      </TableHead>
                      <TableHead>
                        SES{" "}
                        <InfoTooltip text="Sosyoekonomik Statü (A, B, C1, C2, vs). Personanın alım gücünü ve sosyal sınıfını ifade eder." position="bottom" />
                      </TableHead>
                      <TableHead>
                        Katılımcı Tipi{" "}
                        <InfoTooltip text="Tüketicinin pozisyonu. Üretimdeki 'Hedef Tüketici Tanımı'na göre (Örn: Potansiyel, Rakip Kullanıcı) belirlenir." position="bottom" />
                      </TableHead>
                      <TableHead>
                        Tür{" "}
                        <InfoTooltip text="Global (tüm kullanıcılara açık) veya Özel (sadece belirli bir danışana ait) olduğunu belirtir." position="bottom" />
                      </TableHead>
                      <TableHead className="text-right">Aksiyonlar</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {personas.slice((poolPage - 1) * 5, poolPage * 5).map(p => (
                      <TableRow key={p.id} className="hover:bg-muted/30 transition-colors">
                        <TableCell className="font-medium text-sm">
                          {p.name}, {p.age}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs">{p.city}</TableCell>
                        <TableCell className="text-xs font-semibold">{p.role_title || p.segment}</TableCell>
                        <TableCell>
                          {p.ses_group ? (
                            <Badge
                              variant="outline"
                              className={
                                p.ses_group === "AB"
                                  ? "border-amber-300 text-amber-700 bg-amber-50/50"
                                  : p.ses_group === "C1"
                                  ? "border-action-blue/30 text-action-blue bg-blue-50/50"
                                  : p.ses_group === "C2"
                                  ? "border-hairline text-body-muted bg-muted-surface/50"
                                  : "border-rose-300 text-rose-700 bg-rose-50/50"
                              }
                            >
                              {p.ses_group}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground text-xs">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className="text-[10px] font-semibold bg-soft-stone text-ink"
                          >
                            {({
                              potential_customer: "Potansiyel",
                              competitor_user: "Rakip Kullanıcı",
                              churned_user: "Kaybedilmiş",
                              decision_maker: "Karar Verici",
                              individual_user: "Bireysel",
                            } as Record<string, string>)[p.respondent_type ?? ""] ?? "—"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {p.is_global ? (
                            <Badge variant="secondary" className="text-[10px]">
                              Global
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="text-[10px] border-hairline text-deep-green bg-pale-green/50"
                            >
                              Özel
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Dialog>
                              <DialogTrigger render={
                                <Button
                                  variant="ghost"
                                  className="h-8 w-8 p-0 hover:bg-soft-stone dark:hover:bg-surface-dark"
                                >
                                  <Eye className="w-4 h-4 text-body-muted" />
                                </Button>
                              } />
                              <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto bg-background text-foreground">
                                <DialogHeader className="pb-3 border-b border-border">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <DialogTitle className="text-lg font-bold text-primary dark:text-border-light">
                                      {p.name}, {p.age}
                                    </DialogTitle>
                                    {p.is_global ? (
                                      <Badge variant="secondary" className="text-[10px]">
                                        Global
                                      </Badge>
                                    ) : (
                                      <Badge
                                        variant="outline"
                                        className="text-[10px] border-hairline text-deep-green bg-pale-green/50"
                                      >
                                        Özel
                                      </Badge>
                                    )}
                                  </div>
                                  <DialogDescription className="text-xs text-muted-foreground mt-1">
                                    {p.city} • {p.role_title || p.segment}
                                  </DialogDescription>
                                </DialogHeader>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                                  <div className="space-y-4 text-left">
                                    <div>
                                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text mb-1.5">
                                        Biyografi & Yaşam Konsepti
                                      </h4>
                                      <p className="text-xs text-ink dark:text-border-light leading-relaxed bg-muted-surface dark:bg-primary rounded-xl p-3 border border-border/40">
                                        {p.bio || "Bu persona için henüz biyografi hikayesi eklenmemiş."}
                                      </p>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                      <div className="p-3 border border-border/50 rounded-xl bg-card">
                                        <span className="text-[10px] text-muted-foreground block mb-0.5">
                                          Sosyoeonomik Statü (SES)
                                        </span>
                                        <span className="text-sm font-bold text-ink dark:text-border-light">
                                          {p.ses_group || "C1"}
                                        </span>
                                      </div>
                                      <div className="p-3 border border-border/50 rounded-xl bg-card">
                                        <span className="text-[10px] text-muted-foreground block mb-0.5">
                                          Rogers İnovasyon Arketipi
                                        </span>
                                        <span className="text-sm font-bold text-ink dark:text-border-light">
                                          {({
                                            Innovator: "Yenilikçi (Innovator)",
                                            EarlyAdopter: "Erken Benimseyen",
                                            Mainstream: "Çoğunluk (Mainstream)",
                                            Laggard: "Gelenekçi (Laggard)",
                                            Skeptic: "Şüpheci (Skeptic)",
                                          } as Record<string, string>)[p.stance ?? ""] ??
                                            p.stance ??
                                            "Belirsiz"}
                                        </span>
                                      </div>
                                      <div className="p-3 border border-border/50 rounded-xl bg-card">
                                        <span className="text-[10px] text-muted-foreground block mb-0.5">
                                          Yerleşim Tipi
                                        </span>
                                        <span className="text-sm font-bold text-ink dark:text-border-light">
                                          {({ kentsel: "Kentsel (Metropol)", kirsal: "Kırsal (Taşra)" } as Record<
                                            string,
                                            string
                                          >)[p.settlement_type ?? ""] ?? "Kentsel"}
                                        </span>
                                      </div>
                                      <div className="p-3 border border-border/50 rounded-xl bg-card">
                                        <span className="text-[10px] text-muted-foreground block mb-0.5">
                                          Katılımcı Tipi
                                        </span>
                                        <span className="text-sm font-bold text-ink dark:text-border-light">
                                          {({
                                            potential_customer: "Potansiyel",
                                            competitor_user: "Rakip Kullanıcı",
                                            churned_user: "Kaybedilmiş",
                                            decision_maker: "Karar Verici",
                                            individual_user: "Bireysel",
                                          } as Record<string, string>)[p.respondent_type ?? ""] ?? "Standart"}
                                        </span>
                                      </div>
                                    </div>

                                    <div className="space-y-2 border border-border/50 rounded-xl p-3 bg-muted/10">
                                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text">
                                        Tüketici Davranış Endeksleri
                                      </h4>
                                      <div className="space-y-1.5 text-xs">
                                        <div className="flex justify-between items-center">
                                          <span className="text-body-muted dark:text-muted-text">Fiyat Hassasiyeti</span>
                                          <span className="font-semibold text-ink dark:text-border-light">
                                            {(p.price_sensitivity ?? 3)} / 5
                                          </span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                          <span className="text-body-muted dark:text-muted-text">
                                            Dijital Güven & Yetkinlik
                                          </span>
                                          <span className="font-semibold text-ink dark:text-border-light">
                                            {(p.digital_confidence ?? 3)} / 5
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="space-y-4 text-left">
                                    <div>
                                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text mb-2">
                                        Beş Büyük Kişilik Özelliği (OCEAN)
                                      </h4>
                                      <div className="space-y-2 bg-muted-surface dark:bg-primary border border-border/40 p-3 rounded-xl">
                                        {(() => {
                                          const ocean = getBigFive(p);
                                          return [
                                            { name: "Openness (Deneyime Açıklık)", val: ocean.openness, color: "bg-blue-500" },
                                            {
                                              name: "Conscientiousness (Sorumluluk)",
                                              val: ocean.conscientiousness,
                                              color: "bg-emerald-500",
                                            },
                                            { name: "Extroversion (Dışadönüklük)", val: ocean.extroversion, color: "bg-amber-500" },
                                            { name: "Agreeableness (Geçimlilik)", val: ocean.agreeableness, color: "bg-rose-500" },
                                            {
                                              name: "Neuroticism (Duygusal Dengesizlik)",
                                              val: ocean.neuroticism,
                                              color: "bg-red-500",
                                            },
                                          ].map(item => (
                                            <div key={item.name} className="space-y-1">
                                              <div className="flex justify-between text-[11px] font-medium text-body-muted dark:text-muted-text">
                                                <span>{item.name}</span>
                                                <span>%{item.val}</span>
                                              </div>
                                              <div className="h-1.5 w-full bg-hairline dark:bg-surface-dark rounded-full overflow-hidden">
                                                <div
                                                  className={`h-full ${item.color} rounded-full`}
                                                  style={{ width: `${item.val}%` }}
                                                />
                                              </div>
                                            </div>
                                          ));
                                        })()}
                                      </div>
                                    </div>

                                    <div>
                                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text mb-1.5">
                                        Kullanıcı Hedefleri & Amaçları
                                      </h4>
                                      <div className="flex flex-wrap gap-1.5">
                                        {(() => {
                                          const goals = parseJsonField<string[]>(p.goals, []);
                                          const goalList = Array.isArray(goals) ? goals : [];
                                          if (goalList.length === 0)
                                            return <span className="text-xs text-muted-foreground">Hedef belirtilmemiş.</span>;
                                          return goalList.map((g: string, idx: number) => (
                                            <span
                                              key={idx}
                                              className="text-xs bg-emerald-50 text-emerald-800 dark:bg-emerald-950/20 dark:text-emerald-300 border border-emerald-100 dark:border-emerald-900/40 rounded-lg px-2.5 py-1"
                                            >
                                              {g}
                                            </span>
                                          ));
                                        })()}
                                      </div>
                                    </div>

                                    <div>
                                      <h4 className="text-[11px] font-mono uppercase tracking-wider text-muted-text mb-1.5">
                                        Satın Alma İtirazları & Kaygıları
                                      </h4>
                                      <div className="flex flex-wrap gap-1.5">
                                        {(() => {
                                          const objections = parseJsonField<string[]>(p.objections, []);
                                          const objList = Array.isArray(objections) ? objections : [];
                                          if (objList.length === 0)
                                            return <span className="text-xs text-muted-foreground">İtiraz belirtilmemiş.</span>;
                                          return objList.map((obj: string, idx: number) => (
                                            <span
                                              key={idx}
                                              className="text-xs bg-red-50 text-red-800 dark:bg-red-950/20 dark:text-red-300 border border-red-100 dark:border-red-900/40 rounded-lg px-2.5 py-1"
                                            >
                                              {obj}
                                            </span>
                                          ));
                                        })()}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </DialogContent>
                            </Dialog>

                            {p.is_locked ? (
                              <Button
                                variant="ghost"
                                disabled
                                title="Bu persona bir araştırmaya katıldığı için silinemez (Kilitli)"
                                className="h-8 w-8 p-0 text-hairline dark:text-body-muted cursor-not-allowed"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="ghost"
                                onClick={() => {
                                  setDeletePersonaTarget(p.id);
                                  setDeletePersonaName(p.name);
                                }}
                                title="Havuzdan Sil"
                                disabled={deletingPersona === p.id}
                                className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20"
                              >
                                {deletingPersona === p.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin text-red-500" />
                                ) : (
                                  <Trash2 className="w-4 h-4" />
                                )}
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {personas.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-10 text-muted-foreground text-xs">
                          Havuzda kayıtlı persona bulunmuyor. AI veya hazır paketler ile ekleyin.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
              {personas.length > 5 && (
                <div className="flex items-center justify-between mt-4 border-t border-border pt-4">
                  <span className="text-xs text-muted-foreground">Toplam {personas.length} persona</span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={poolPage === 1}
                      onClick={() => setPoolPage(p => p - 1)}
                      className="h-8 text-xs text-ink"
                    >
                      Önceki
                    </Button>
                    <span className="text-xs font-medium">
                      Sayfa {poolPage} / {Math.ceil(personas.length / 5)}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={poolPage >= Math.ceil(personas.length / 5)}
                      onClick={() => setPoolPage(p => p + 1)}
                      className="h-8 text-xs text-ink"
                    >
                      Sonraki
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
      </Card>

      {/* Persona Delete Confirmation Modal */}
      <Dialog open={!!deletePersonaTarget} onOpenChange={(o) => !o && setDeletePersonaTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-50 border border-red-200 shrink-0">
                <AlertTriangle size={18} className="text-red-600" />
              </div>
              <div>
                <DialogTitle className="text-base">Personayı Sil</DialogTitle>
                <DialogDescription className="text-sm mt-0.5">
                  <span className="font-semibold text-foreground">&quot;{deletePersonaName}&quot;</span> personası havuzdan kalıcı olarak silinecek.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-2">
            <button
              onClick={() => setDeletePersonaTarget(null)}
              className="flex-1 h-9 px-4 text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors"
            >
              İptal
            </button>
            <button
              onClick={() => deletePersonaTarget && handleDeletePersona(deletePersonaTarget)}
              disabled={!!deletingPersona}
              className="flex-1 h-9 px-4 text-sm font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {deletingPersona && <Loader2 size={14} className="animate-spin" />}
              Evet, Sil
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
