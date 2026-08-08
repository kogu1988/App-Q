"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Save } from "lucide-react";

interface AdminConfig {
  b2c_model?: string;
  b2b_model?: string;
  pii_active?: string;
  pii_terms?: string;
  wizard_prompt?: string;
  persona_interview_prompt?: string;
  synthesis_prompt?: string;
  [key: string]: string | undefined;
}

export function ConfigTab({
  config,
  savingConfig,
  saveConfig,
}: {
  config: AdminConfig;
  savingConfig: string | null;
  saveConfig: (key: string, value: string) => void;
}) {
  return (
    <div className="mt-6 flex-1 outline-none">
      <div className="mb-6">
        <p className="text-sm text-muted-foreground">
          Yapay zeka modelleri, PII/KVKK ayarları ve sistem promptları.
        </p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">Güvenlik Ayarları</CardTitle>
          <CardDescription>Kişisel veri maskeleme (KVKK) yapılandırması.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              { key: "pii_terms", label: "PII Maskeleme Terimleri (virgülle ayrılmış)" },
            ].map(({ key, label }) => (
              <div key={key} className="space-y-1.5">
                <Label>{label}</Label>
                <div className="flex gap-2">
                  <Input
                    id={`config-${key}`}
                    defaultValue={config[key] || ""}
                    className="flex-1 text-foreground bg-background"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={savingConfig === key}
                    onClick={() => {
                      const el = document.getElementById(`config-${key}`) as HTMLInputElement;
                      if (el) saveConfig(key, el.value);
                    }}
                    className="shrink-0 gap-1.5"
                  >
                    {savingConfig === key ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                    Kaydet
                  </Button>
                </div>
              </div>
            ))}
            <div className="space-y-1.5">
              <Label>PII Maskeleme (KVKK)</Label>
              <div className="flex items-center gap-3 h-10">
                <Badge
                  className={
                    config.pii_active === "true"
                      ? "bg-[#003c33] hover:bg-[#003c33]/85 text-white"
                      : "bg-[#eeece7] text-[#212121]"
                  }
                >
                  {config.pii_active === "true" ? "Aktif" : "Pasif"}
                </Badge>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => saveConfig("pii_active", config.pii_active === "true" ? "false" : "true")}
                >
                  {config.pii_active === "true" ? "Pasife Al" : "Aktive Et"}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Sistem Prompt Editörleri</CardTitle>
          <CardDescription>
            Araştırma sihirbazı, persona mülakat ve sentez raporu için LLM system promptları.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { key: "wizard_prompt", label: "Araştırma Sihirbazı Promptu (Defne)" },
            { key: "persona_interview_prompt", label: "Persona Mülakat Promptu" },
            { key: "synthesis_prompt", label: "Sentez Raporu Promptu" },
          ].map(({ key, label }) => (
            <div key={key} className="flex flex-col space-y-2 border border-border/50 rounded-lg p-4 bg-muted/20">
              <Label className="font-semibold">{label}</Label>
              <Textarea
                id={`prompt-${key}`}
                defaultValue={config[key] || ""}
                rows={8}
                className="text-sm font-mono bg-[#f5f4f1] text-slate-800 flex-1 resize-none"
              />
              <div className="flex justify-end pt-2">
                <Button
                  size="sm"
                  disabled={savingConfig === key}
                  onClick={() => {
                    const el = document.getElementById(`prompt-${key}`) as HTMLTextAreaElement;
                    if (el) saveConfig(key, el.value);
                  }}
                  className="gap-2 bg-[#ff7759] text-[#edfce9] hover:bg-[#ff7759]/90 w-full"
                >
                  {savingConfig === key ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                  Promptu Kaydet
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
