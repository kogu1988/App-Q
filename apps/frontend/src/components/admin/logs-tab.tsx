"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
} from "@/components/ui/dialog";
import {
} from "lucide-react";
import type {
  AuditLog,
} from "@/features/admin/types";

interface LogsTabProps {
  logs: AuditLog[];
}

/** Denetim kayitlari sekmesi (refactor R3). */
export function LogsTab({ logs }: LogsTabProps) {
  return (
    <>
  <div className="mb-6">
    <p className="text-sm text-muted-foreground">
      Simülasyon motorundaki kalite uyarıları, hallüsinasyon tespitleri ve aksiyon kayıtları.
    </p>
  </div>
  <div className="flex justify-between items-center mb-2">
    <span className="text-sm font-semibold text-muted-foreground">{logs.length} kayıt</span>
  </div>
  <Card>
    <CardContent className="pt-6">
      <div className="overflow-x-auto w-full">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tarih</TableHead>
              <TableHead>Persona</TableHead>
              <TableHead>Hata / Uyarı</TableHead>
              <TableHead>Alınan Aksiyon</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-10 text-muted-foreground">
                  Denetim kaydı bulunmuyor.
                </TableCell>
              </TableRow>
            ) : (
              logs.map(log => (
                <TableRow key={log.id}>
                  <TableCell className="text-muted-foreground text-xs font-mono">
                    {new Date(log.created_at).toLocaleString("tr-TR")}
                  </TableCell>
                  <TableCell className="font-medium">{log.persona_name}</TableCell>
                  <TableCell>
                    <span className="text-red-600 dark:text-red-400 text-sm font-medium">
                      {log.error_reason}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{log.action_taken}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </CardContent>
  </Card>
    </>
  );
}
