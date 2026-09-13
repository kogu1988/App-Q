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
    <div className="grid grid-cols-2 md:grid-cols-6 gap-2 bg-[#eeece7] dark:bg-[#212121] p-1.5 rounded-xl border border-[#d9d9dd] dark:border-[rgba(255,255,255,0.1)]">
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
                ? "bg-white text-[#1863dc] dark:text-[#4c6ee6] shadow-sm border border-[#d9d9dd]"
                : "text-[#616161] hover:text-[#17171c] hover:bg-[#d9d9dd]/40 dark:text-[#93939f] dark:hover:text-white dark:hover:bg-[#2c2c33]"
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
