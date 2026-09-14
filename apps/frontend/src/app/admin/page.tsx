"use client";

import { Loader2 } from "lucide-react";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { AdminHeader } from "@/components/admin/admin-header";
import { AdminTabNav } from "@/components/admin/admin-tab-nav";
import { ClientsTab } from "@/components/admin/clients-tab";
import { ConfigTab } from "@/components/admin/config-tab";
import { PersonasTab } from "@/components/admin/personas-tab";
import { QuestionsTab } from "@/components/admin/questions-tab";
import { FeedbackTab } from "@/components/admin/feedback-tab";
import { LogsTab } from "@/components/admin/logs-tab";
import { SchemasTab } from "@/components/admin/schemas-tab";
import { MetricsTab } from "@/components/admin/metrics-tab";
import { UsageTab } from "@/components/admin/usage-tab";
import { DeleteQuestionModal } from "@/components/admin/delete-question-modal";
import { useAdmin } from "@/features/admin/hooks/use-admin";

export default function AdminPage() {
  const admin = useAdmin();

  if (admin.loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="h-10 w-10 animate-spin text-coral mx-auto" />
          <p className="text-muted-foreground text-sm font-medium animate-pulse">Yönetici paneli yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-4 sm:p-8">
      <div className="max-w-6xl mx-auto space-y-6 sm:space-y-8 animate-in fade-in slide-in-from-bottom-4">
        <AdminHeader adminKey={admin.adminKey} onAdminKeyChange={admin.setAdminKey} />

        <Tabs defaultValue="clients" orientation="vertical" className="flex flex-col md:flex-row gap-6 w-full">
          <AdminTabNav
            onSchemasOpen={admin.loadSchemas}
            onMetricsOpen={admin.loadMetrics}
            onUsageOpen={admin.loadUsage}
          />

          <div className="flex-1 w-full min-w-0">
            <TabsContent value="clients" className="mt-0 outline-none">
              <ClientsTab clients={admin.clients} onRefresh={admin.fetchAll} />
            </TabsContent>

            <TabsContent value="config" className="mt-0 outline-none">
              <ConfigTab config={admin.config} savingConfig={admin.savingConfig} saveConfig={admin.saveConfig} />
            </TabsContent>

            <TabsContent value="personas" className="mt-0 outline-none">
              <PersonasTab personas={admin.personas} onRefresh={admin.fetchAll} />
            </TabsContent>

            <TabsContent value="questions" className="mt-6 flex-1 outline-none">
              <QuestionsTab
                questions={admin.questions}
                editingQuestion={admin.editingQuestion}
                onEditingQuestionChange={admin.setEditingQuestion}
                editPurpose={admin.editPurpose}
                onEditPurposeChange={admin.setEditPurpose}
                onRequestDelete={admin.setDeleteQuestionTarget}
                onToggleLike={admin.toggleLike}
                onSavePurpose={admin.savePurpose}
              />
            </TabsContent>

            <TabsContent value="feedbacks" className="mt-6 flex-1 outline-none">
              <FeedbackTab feedbacks={admin.feedbacks} />
            </TabsContent>

            <TabsContent value="logs" className="mt-6 flex-1 outline-none">
              <LogsTab logs={admin.logs} />
            </TabsContent>

            <TabsContent value="schemas" className="mt-6 flex-1 outline-none space-y-6">
              <SchemasTab
                schemas={admin.schemas}
                onSchemasChange={admin.setSchemas}
                schemasLoading={admin.schemasLoading}
                expandedPool={admin.expandedPool}
                onExpandedPoolChange={admin.setExpandedPool}
                editingDefaultQ={admin.editingDefaultQ}
                onEditingDefaultQChange={admin.setEditingDefaultQ}
                draftQuestions={admin.draftQuestions}
                onDraftQuestionsChange={admin.setDraftQuestions}
                savingDefaults={admin.savingDefaults}
                onSavingDefaultsChange={admin.setSavingDefaults}
                briefDefaults={admin.briefDefaults}
              />
            </TabsContent>

            <TabsContent value="metrics" className="mt-6 flex-1 outline-none space-y-6">
              <MetricsTab metrics={admin.metrics} metricsLoading={admin.metricsLoading} />
            </TabsContent>

            <TabsContent value="usage" className="mt-6 flex-1 outline-none space-y-6">
              <UsageTab usage={admin.usage} usageLoading={admin.usageLoading} />
            </TabsContent>
          </div>
        </Tabs>
      </div>

      <DeleteQuestionModal
        open={!!admin.deleteQuestionTarget}
        onOpenChange={(o) => !o && admin.setDeleteQuestionTarget(null)}
        deleting={admin.deletingQuestion}
        onConfirm={() => admin.deleteQuestionTarget && admin.deleteQuestion(admin.deleteQuestionTarget)}
      />
    </div>
  );
}
