import React, { useState } from 'react';
import { UnifiedTopHUD } from '@/components/UnifiedTopHUD';
import { MapView } from '@/features/map/MapView';
import { IntelligenceSidebar } from '@/features/intelligence/IntelligenceSidebar';
import { ContextLayersSidebar } from '@/features/panels/ContextLayersSidebar';
import { HoverPopup } from '@/components/HoverPopup';
import { useAppStore } from '@/store';
import { Brain, ChevronsLeft, ChevronsRight, Layers } from 'lucide-react';

export const CommandCenter: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useAppStore();
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-black font-sans text-white">
      {/* LAYER 0: MapView (Base Level) */}
      <div className="absolute inset-0 z-0">
        <MapView />
      </div>

      {/* LAYER 10: Top HUD */}
      <div className="absolute top-0 left-0 right-0 z-10 pointer-events-none">
        <div className="pointer-events-auto">
          <UnifiedTopHUD />
        </div>
      </div>

      {/* LAYER 20: Floating Base Panels (Left & Right Sidebars) */}
      <div className="absolute inset-0 z-20 pointer-events-none">
        {/* Left Context Panel */}
        <ContextLayersSidebar 
          isOpen={leftSidebarOpen} 
          onClose={() => setLeftSidebarOpen(false)} 
        />

        {/* Toggle Button for Left Panel */}
        {!leftSidebarOpen && (
          <button
            onClick={() => setLeftSidebarOpen(true)}
            title="Open Context Layers"
            className="absolute top-24 left-4 flex items-center gap-2 rounded-xl border border-zinc-800 bg-black/80 px-3 py-2 text-xs font-bold uppercase text-zinc-400 backdrop-blur-md transition-all hover:border-cyan-700 hover:text-cyan-400 pointer-events-auto shadow-lg"
          >
            <Layers size={14} />
            <span>Layers</span>
            <ChevronsRight size={14} />
          </button>
        )}

        {/* Right Intelligence Sidebar */}
        <div
          className={`absolute top-24 bottom-6 right-4 w-[500px] transition-transform duration-300 ease-in-out pointer-events-none ${
            sidebarOpen ? 'translate-x-0' : 'translate-x-[120%]'
          }`}
        >
          <div className="h-full w-full rounded-2xl overflow-hidden shadow-xl flex flex-col pointer-events-auto bg-black/80 backdrop-blur-xl border border-zinc-800/80">
            <IntelligenceSidebar />
          </div>
        </div>

        {/* Toggle Button for Right Panel */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            title="Open Intelligence Panel"
            className="absolute top-24 right-4 flex items-center gap-2 rounded-xl border border-zinc-800 bg-black/80 px-3 py-2 text-xs font-bold uppercase text-zinc-400 backdrop-blur-md transition-all hover:border-blue-700 hover:text-blue-400 pointer-events-auto shadow-lg"
          >
            <ChevronsLeft size={14} />
            <span>Intelligence</span>
            <Brain size={14} />
          </button>
        )}
      </div>

      {/* LAYER 50: Topmost Overlays & Tooltips */}
      <div className="absolute inset-0 z-50 pointer-events-none">
        <HoverPopup />
      </div>
    </div>
  );
};
