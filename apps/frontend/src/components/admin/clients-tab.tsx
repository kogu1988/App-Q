"use client";

import { useState } from "react";
import { toast } from "sonner";
import { getAdminHeaders } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Plus, Loader2, Pencil, Trash2, Check, X, AlertTriangle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ClientInfo {
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

const PLAN_TEMPLATES: Record<string, { max_simulations: number; max_tokens: number }> = {
  Free: { max_simulations: 2, max_tokens: 100_000 },
  Flex: { max_simulations: 3, max_tokens: 200_000 },
  Starter: { max_simulations: 10, max_tokens: 500_000 },
  Pro: { max_simulations: 9999, max_tokens: 9_999_999 },
  Enterprise: { max_simulations: 9999, max_tokens: 9_999_999 },
};

export function ClientsTab({ clients, onRefresh }: { clients: ClientInfo[]; onRefresh: () => void }) {
  // New Client Form States
  const [showClientForm, setShowClientForm] = useState(false);
  const [clientForm, setClientForm] = useState({
    username: "",
    email: "",
    plan_type: "Free",
    max_simulations: 2,
    max_tokens: 100_000,
    plan_start: "",
    plan_end: "",
  });
  const [savingClient, setSavingClient] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deletingClient, setDeletingClient] = useState(false);

  // Edit Client States
  const [editingClient, setEditingClient] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<ClientInfo>>({});

  // Apply plan template to creation form
  const applyTemplate = (planName: string) => {
    const tpl = PLAN_TEMPLATES[planName];
    if (tpl) {
      setClientForm(f => ({
        ...f,
        plan_type: planName,
        max_simulations: tpl.max_simulations,
        max_tokens: tpl.max_tokens,
      }));
    } else {
      setClientForm(f => ({ ...f, plan_type: planName }));
    }
  };

  // Apply plan template to edit form
  const applyTemplateToEdit = (planName: string) => {
    const tpl = PLAN_TEMPLATES[planName];
    if (tpl) {
      setEditForm(f => ({
        ...f,
        plan_type: planName,
        max_simulations: tpl.max_simulations,
        max_tokens: tpl.max_tokens,
      }));
    } else {
      setEditForm(f => ({ ...f, plan_type: planName }));
    }
  };

  const createClient = async () => {
    setSavingClient(true);
    try {
      const res = await fetch("/api/admin/clients", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAdminHeaders() },
        body: JSON.stringify(clientForm),
      });
      if (!res.ok) throw new Error();
      toast.success("Danışan eklendi.");
      setShowClientForm(false);
      setClientForm({
        username: "",
        email: "",
        plan_type: "Free",
        max_simulations: 2,
        max_tokens: 100_000,
        plan_start: "",
        plan_end: "",
      });
      onRefresh();
    } catch {
      toast.error("Danışan eklenemedi.");
    } finally {
      setSavingClient(false);
    }
  };

  const updateClient = async (username: string) => {
    try {
      const res = await fetch(`/api/admin/clients/${username}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...getAdminHeaders() },
        body: JSON.stringify({
          email: editForm.email || "",
          plan_type: editForm.plan_type || "Free",
          max_simulations: editForm.max_simulations || 2,
          max_tokens: editForm.max_tokens || 50000,
          plan_start: editForm.plan_start || "",
          plan_end: editForm.plan_end || "",
          status: editForm.status || "Aktif",
        }),
      });
      if (!res.ok) throw new Error();
      toast.success("Danışan güncellendi.");
      setEditingClient(null);
      onRefresh();
    } catch {
      toast.error("Güncelleme başarısız.");
    }
  };

  const deleteClient = async (username: string) => {
    setDeletingClient(true);
    try {
      const res = await fetch(`/api/admin/clients/${username}`, { method: "DELETE", headers: getAdminHeaders() });
      if (!res.ok) throw new Error();
      toast.success("Danışan silindi.");
      setDeleteTarget(null);
      onRefresh();
    } catch {
      toast.error("Silme başarısız.");
    } finally {
      setDeletingClient(false);
    }
  };

  return (
    <>
    <div className="mt-6 flex-1 outline-none">
      <div className="mb-6">
        <p className="text-sm text-body-muted dark:text-muted-text">
          Sisteme kayıtlı kurumsal müşteriler ve simülasyon limitleri.
        </p>
      </div>
      <div className="flex justify-between items-center mb-2">
        <Button
          onClick={() => setShowClientForm(!showClientForm)}
          className="gap-2 bg-primary text-white hover:opacity-85 h-9"
        >
          <Plus size={16} />
          Yeni Danışan
        </Button>
      </div>

      {/* Add Client Form */}
      {showClientForm && (
        <Card className="border-hairline bg-pale-green/30 animate-in fade-in slide-in-from-top-2 duration-200 mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-deep-green">Yeni Danışan Ekle</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-4 p-3 bg-white border border-border rounded-lg space-y-2">
              <Label className="text-[11px] font-mono uppercase tracking-wider text-muted-text">
                Plan Şablonu Seç (Limitler Otomatik Dolar)
              </Label>
              <div className="flex flex-wrap gap-2">
                {Object.entries(PLAN_TEMPLATES).map(([name, tpl]) => (
                  <button
                    key={name}
                    type="button"
                    onClick={() => applyTemplate(name)}
                    className={`flex flex-col items-start px-3 py-2 rounded-lg border-2 transition-all text-left ${
                      clientForm.plan_type === name
                        ? "border-primary bg-pale-green"
                        : "border-border hover:border-primary"
                    }`}
                  >
                    <span className={`font-bold text-sm ${clientForm.plan_type === name ? "text-deep-green" : ""}`}>
                      {name}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {tpl.max_simulations >= 9999 ? "∞" : tpl.max_simulations} sim ·{" "}
                      {tpl.max_tokens >= 1_000_000
                        ? (tpl.max_tokens / 1_000_000).toFixed(0) + "M"
                        : (tpl.max_tokens / 1_000).toFixed(0) + "K"}{" "}
                      token
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <Label>Kullanıcı Adı</Label>
                <Input
                  value={clientForm.username}
                  onChange={e => setClientForm(f => ({ ...f, username: e.target.value }))}
                  placeholder="ornek_musteri"
                />
              </div>
              <div className="space-y-1.5">
                <Label>E-Posta</Label>
                <Input
                  value={clientForm.email}
                  onChange={e => setClientForm(f => ({ ...f, email: e.target.value }))}
                  placeholder="ornek@firma.com"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Maks. Simülasyon</Label>
                <Input
                  type="number"
                  value={clientForm.max_simulations}
                  onChange={e => setClientForm(f => ({ ...f, max_simulations: +e.target.value }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Maks. Token</Label>
                <Input
                  type="number"
                  value={clientForm.max_tokens}
                  onChange={e => setClientForm(f => ({ ...f, max_tokens: +e.target.value }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Plan Bitiş (opsiyonel)</Label>
                <Input
                  type="date"
                  value={clientForm.plan_end}
                  onChange={e => setClientForm(f => ({ ...f, plan_end: e.target.value }))}
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4 justify-end">
              <Button variant="outline" onClick={() => setShowClientForm(false)}>
                İptal
              </Button>
              <Button
                onClick={createClient}
                disabled={savingClient || !clientForm.username}
                className="gap-2 bg-primary text-white hover:opacity-85"
              >
                {savingClient && <Loader2 size={14} className="animate-spin" />}
                Kaydet
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="pt-4">
          <div className="overflow-x-auto w-full">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Kullanıcı</TableHead>
                  <TableHead>E-Posta</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Kullanım</TableHead>
                  <TableHead>Token</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead className="text-right">İşlemler</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {clients.map(cli => (
                  <TableRow key={cli.username}>
                    <TableCell className="font-medium">{cli.username}</TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {editingClient === cli.username ? (
                        <Input
                          className="h-7 text-xs"
                          value={editForm.email || ""}
                          onChange={e => setEditForm(f => ({ ...f, email: e.target.value }))}
                        />
                      ) : (
                        cli.email
                      )}
                    </TableCell>
                    <TableCell>
                      {editingClient === cli.username ? (
                        <select
                          className="h-7 text-xs border border-border rounded-md px-1.5 bg-background text-foreground"
                          value={editForm.plan_type || ""}
                          onChange={e => applyTemplateToEdit(e.target.value)}
                        >
                          {Object.keys(PLAN_TEMPLATES).map(p => (
                            <option key={p} value={p}>
                              {p}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <Badge variant="outline">{cli.plan_type}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      <span
                        className={cli.total_simulations >= cli.max_simulations ? "text-red-600 font-semibold" : ""}
                      >
                        {cli.total_simulations} /{" "}
                        {editingClient === cli.username ? (
                          <input
                            className="h-7 text-xs w-16 border border-border rounded px-1 bg-background text-foreground"
                            type="number"
                            value={editForm.max_simulations ?? cli.max_simulations}
                            onChange={e => setEditForm(f => ({ ...f, max_simulations: +e.target.value }))}
                          />
                        ) : (
                          cli.max_simulations
                        )}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {editingClient === cli.username ? (
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">{cli.tokens_used?.toLocaleString()} /</span>
                          <input
                            className="h-7 text-xs w-24 border border-border rounded px-1 bg-background text-foreground"
                            type="number"
                            value={editForm.max_tokens ?? cli.max_tokens}
                            onChange={e => setEditForm(f => ({ ...f, max_tokens: +e.target.value }))}
                          />
                        </div>
                      ) : (
                        <span>
                          {cli.tokens_used?.toLocaleString()} /{" "}
                          <strong>
                            {cli.max_tokens >= 1_000_000
                              ? (cli.max_tokens / 1_000_000).toFixed(0) + "M"
                              : cli.max_tokens >= 1_000
                              ? (cli.max_tokens / 1_000).toFixed(0) + "K"
                              : cli.max_tokens}
                          </strong>
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {cli.status === "Aktif" ? (
                        <Badge className="bg-deep-green hover:bg-deep-green/85 text-white text-xs">Aktif</Badge>
                      ) : (
                        <Badge variant="secondary" className="text-xs">
                          {cli.status}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-1.5 justify-end">
                        {editingClient === cli.username ? (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-emerald-600 hover:text-deep-green"
                              onClick={() => updateClient(cli.username)}
                            >
                              <Check size={14} />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-muted-foreground"
                              onClick={() => setEditingClient(null)}
                            >
                              <X size={14} />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                              onClick={() => {
                                setEditingClient(cli.username);
                                setEditForm(cli);
                              }}
                            >
                              <Pencil size={14} />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 w-7 p-0 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                              onClick={() => setDeleteTarget(cli.username)}
                            >
                              <Trash2 size={14} />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>

      {/* Delete Confirmation Modal */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-50 border border-red-200 shrink-0">
                <AlertTriangle size={18} className="text-red-600" />
              </div>
              <div>
                <DialogTitle className="text-base">Danışanı Sil</DialogTitle>
                <DialogDescription className="text-sm mt-0.5">
                  <span className="font-semibold text-foreground">&quot;{deleteTarget}&quot;</span> hesabı kalıcı olarak silinecek. Bu işlem geri alınamaz.
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-2">
            <button
              onClick={() => setDeleteTarget(null)}
              className="flex-1 h-9 px-4 text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors"
            >
              İptal
            </button>
            <button
              onClick={() => deleteTarget && deleteClient(deleteTarget)}
              disabled={deletingClient}
              className="flex-1 h-9 px-4 text-sm font-semibold bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {deletingClient && <Loader2 size={14} className="animate-spin" />}
              Evet, Sil
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
