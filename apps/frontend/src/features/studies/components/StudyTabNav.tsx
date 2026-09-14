"use client";

import { FileText, Users, ListTodo, MessageSquare, Search, TrendingUp } from "lucide-react";
import type { ComponentType } from "react";
import type { StudyDetailTab } from "../hooks/use-study-detail";

interface StudyTabNavProps {
  activeTab: StudyDetailTab;
  onTabChange: (tab: StudyDetailTab) => void;
  personasCount: number;
  interviewsCount: number;
}

const TABS: Array<{
  key: StudyDetailTab;
  icon: ComponentType<{ size?: number }>;
  label: string;
  withPersonasCount?: boolean;
  withInterviewsCount?: boolean;
}> = [
  { key: "summary", icon: FileText, label: "Özet & Hedefler" },
  { key: "personas", icon: Users, label: "Personalar", withPersonasCount: true },
  { key: "script", icon: ListTodo, label: "Senaryo" },
  { key: "interviews", icon: MessageSquare, label: "Mülakat Kayıtları", withInterviewsCount: true },
  { key: "findings", icon: Search, label: "Kanıt Zinciri" },
  { key: "report", icon: TrendingUp, label: "Sentez Raporu" },
];

/** Study detay sekme gezinmesi (refactor R2-6). */
export function StudyTabNav({ activeTab, onTabChange, personasCount, interviewsCount }: StudyTabNavProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-2 bg-soft-stone dark:bg-ink p-1.5 rounded-xl border border-hairline dark:border-canvas/10">
      {TABS.map(tab => {
        const Icon = tab.icon;
        const label = tab.withPersonasCount
          ? `${tab.label} (${personasCount})`
          : tab.withInterviewsCount
          ? `${tab.label} (${interviewsCount})`
          : tab.label;
        return (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key)}
            className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
              activeTab === tab.key
                ? "bg-white text-action-blue dark:text-focus-blue shadow-sm border border-hairline"
                : "text-body-muted hover:text-primary hover:bg-hairline/40 dark:text-muted-text dark:hover:text-white dark:hover:bg-surface-dark"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        );
      })}
    </div>
  );
}
