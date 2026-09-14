"use client";

import { TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Activity,
  BarChart3,
  Code,
  DollarSign,
  Heart,
  ListOrdered,
  MessageSquare,
  Settings,
  Users,
} from "lucide-react";

interface AdminTabNavProps {
  onSchemasOpen: () => void;
  onMetricsOpen: () => void;
  onUsageOpen: () => void;
}

/** Admin sekme listesi (refactor R3). Tembel yükleme guard'ları hook'tadır. */
export function AdminTabNav({ onSchemasOpen, onMetricsOpen, onUsageOpen }: AdminTabNavProps) {
  return (
    <TabsList className="flex flex-col h-auto w-full md:w-64 bg-muted p-2 rounded-lg gap-2 justify-start items-stretch">
      <TabsTrigger value="clients" className="justify-start px-4 py-2.5 w-full">
        <Users size={16} className="mr-3" />
        <span>Danışanlar</span>
      </TabsTrigger>
      <TabsTrigger value="config" className="justify-start px-4 py-2.5 w-full">
        <Settings size={16} className="mr-3" />
        <span>Yapılandırma</span>
      </TabsTrigger>
      <TabsTrigger value="personas" className="justify-start px-4 py-2.5 w-full">
        <ListOrdered size={16} className="mr-3" />
        <span>Personalar</span>
      </TabsTrigger>
      <TabsTrigger value="questions" className="justify-start px-4 py-2.5 w-full">
        <MessageSquare size={16} className="mr-3" />
        <span>Soru Koleksiyonu</span>
      </TabsTrigger>
      <TabsTrigger value="feedbacks" className="justify-start px-4 py-2.5 w-full">
        <Heart size={16} className="mr-3" />
        <span>Geri Bildirimler</span>
      </TabsTrigger>
      <TabsTrigger value="logs" className="justify-start px-4 py-2.5 w-full">
        <Activity size={16} className="mr-3" />
        <span>Denetim Kayıtları</span>
      </TabsTrigger>
      <TabsTrigger value="schemas" className="justify-start px-4 py-2.5 w-full" onClick={onSchemasOpen}>
        <Code size={16} className="mr-3" />
        <span>Ajan Şablonları</span>
      </TabsTrigger>
      <TabsTrigger value="metrics" className="justify-start px-4 py-2.5 w-full" onClick={onMetricsOpen}>
        <BarChart3 size={16} className="mr-3" />
        <span>Metrikler</span>
      </TabsTrigger>
      <TabsTrigger value="usage" className="justify-start px-4 py-2.5 w-full" onClick={onUsageOpen}>
        <DollarSign size={16} className="mr-3" />
        <span>Maliyet</span>
      </TabsTrigger>
    </TabsList>
  );
}
