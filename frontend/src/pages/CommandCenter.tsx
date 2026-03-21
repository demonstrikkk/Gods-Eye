// ─────────────────────────────────────────────────────────────────────────────
// CommandCenter — unified full-screen intelligence cockpit
// All views live here; data surfaces via the Intelligence Sidebar and hover popups
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import { StatusBar }          from '@/components/StatusBar';
import { KPIBar }             from '@/components/KPIBar';
import { MapView }            from '@/features/map/MapView';
import { IntelligenceSidebar } from '@/features/intelligence/IntelligenceSidebar';
import { HoverPopup }         from '@/components/HoverPopup';
import { ViewNav }            from '@/components/ViewNav';
import { useAppStore }        from '@/store';
import { ChevronsLeft, Brain } from 'lucide-react';

export const CommandCenter: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <div className="flex flex-col w-screen h-screen bg-[#09090b] text-zinc-100 overflow-hidden font-sans">
      {/* ── Status strip ── */}
      <StatusBar />

      {/* ── Horizontal view navigator ── */}
      <ViewNav />

      {/* ── KPI strip ── */}
      <KPIBar />

      {/* ── Main workspace ── */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* Map fills remaining space */}
        <div className="flex-1 relative overflow-hidden">
          <MapView />

          {/* Re-open sidebar button */}
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              title="Open Intelligence Panel"
              className="absolute top-3 right-3 z-[402] flex items-center space-x-1.5 bg-black/70 border border-zinc-700 hover:border-blue-700 text-zinc-400 hover:text-blue-400 text-[10px] font-bold uppercase px-3 py-2 rounded-xl backdrop-blur-md transition-all"
            >
              <Brain size={12} />
              <span>Intel Panel</span>
              <ChevronsLeft size={12} />
            </button>
          )}
        </div>

        {/* Intelligence sidebar — 40% wide, context-aware */}
        <IntelligenceSidebar />
      </div>

      {/* Glassmorphic hover popup — global overlay */}
      <HoverPopup />
    </div>
  );
};
