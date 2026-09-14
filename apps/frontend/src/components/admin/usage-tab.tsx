"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
} from "@/components/ui/dialog";
import {
  Loader2,
} from "lucide-react";
import type {
  UsageResponse,
} from "@/features/admin/types";

interface UsageTabProps {
  usage: UsageResponse | null;
  usageLoading: boolean;
}

/** Maliyet sekmesi (refactor R3). */
export function UsageTab({ usage, usageLoading }: UsageTabProps) {
  return (
    <>
  <div className="mb-6">
    <p className="text-sm text-body-muted dark:text-muted-text">
      Kullanıcı bazlı token tüketimi ve tahmini DeepSeek maliyeti (USD).
    </p>
  </div>

  {usageLoading && (
    <div className="flex items-center gap-3 py-16 justify-center text-muted-foreground">
      <Loader2 size={22} className="animate-spin text-coral" />
      Maliyet verisi yükleniyor...
    </div>
  )}

  {usage && (
    <Card>
      <CardHeader>
        <CardTitle>Token &amp; Maliyet Özeti</CardTitle>
        <CardDescription>
          {usage.usage.length} kullanıcı · Toplam tahmini maliyet: ${
            usage.usage.reduce((sum, r) => sum + Number(r.cost_usd || 0), 0).toFixed(4)
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        {usage.usage.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            Henüz kayıtlı token kullanımı yok.
          </p>
        ) : (
          <div className="overflow-x-auto w-full">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Kullanıcı</TableHead>
                  <TableHead className="text-right">Çağrı</TableHead>
                  <TableHead className="text-right">Prompt</TableHead>
                  <TableHead className="text-right">Completion</TableHead>
                  <TableHead className="text-right">Cache Hit</TableHead>
                  <TableHead className="text-right">Toplam Token</TableHead>
                  <TableHead className="text-right">Maliyet (USD)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usage.usage.map((row) => (
                  <TableRow key={row.username}>
                    <TableCell className="font-medium">{row.username}</TableCell>
                    <TableCell className="text-right">{row.calls.toLocaleString("tr-TR")}</TableCell>
                    <TableCell className="text-right">{row.prompt_tokens.toLocaleString("tr-TR")}</TableCell>
                    <TableCell className="text-right">{row.completion_tokens.toLocaleString("tr-TR")}</TableCell>
                    <TableCell className="text-right">{row.cache_hit_tokens.toLocaleString("tr-TR")}</TableCell>
                    <TableCell className="text-right font-semibold">{row.total_tokens.toLocaleString("tr-TR")}</TableCell>
                    <TableCell className="text-right font-mono">${Number(row.cost_usd).toFixed(4)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        <p className="text-[11px] text-muted-foreground mt-4 leading-relaxed">
          Maliyet tahminidir; DeepSeek fiyatları `DEEPSEEK_PRICE_*` ortam değişkenleriyle güncellenir.
        </p>
      </CardContent>
    </Card>
  )}
    </>
  );
}
