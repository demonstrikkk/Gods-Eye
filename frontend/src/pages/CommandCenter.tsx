import React from 'react';
import { StatusBar } from '@/components/StatusBar';
import { LiveFeedTicker } from '@/components/LiveFeedTicker';
import { MarketPulseBar } from '@/components/MarketPulseBar';
import { KPIBar } from '@/components/KPIBar';
import { MapView } from '@/features/map/MapView';
import { IntelligenceSidebar } from '@/features/intelligence/IntelligenceSidebar';
import { HoverPopup } from '@/components/HoverPopup';
import { ViewNav } from '@/components/ViewNav';
import { useAppStore } from '@/store';
import { ChevronsLeft, Brain } from 'lucide-react';

export const CommandCenter: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <div className="flex flex-col w-screen h-screen overflow-hidden bg-[#09090b] font-sans text-zinc-100">
      <StatusBar />
      <LiveFeedTicker />
      <MarketPulseBar />
      <ViewNav />
      <KPIBar />

      <div className="relative flex flex-1 overflow-hidden">
        <div className="relative flex-1 overflow-hidden">
          <MapView />

          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              title="Open Intelligence Panel"
              className="absolute top-3 right-3 z-[402] flex items-center space-x-1.5 rounded-xl border border-zinc-700 bg-black/70 px-3 py-2 text-[10px] font-bold uppercase text-zinc-400 backdrop-blur-md transition-all hover:border-blue-700 hover:text-blue-400"
            >
              <Brain size={12} />
              <span>Intel Panel</span>
              <ChevronsLeft size={12} />
            </button>
          )}
        </div>

        <IntelligenceSidebar />
      </div>

      <HoverPopup />
    </div>
  );
};
