// ─────────────────────────────────────────────────────────────────────────────
// IntelligenceSidebar — right-side context panel
// Shows view-specific data panels + always-available tabs
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import clsx from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '@/store';
import type { SidebarTab } from '@/types';
import { GlobalTab }   from '@/features/global/GlobalTab';
import { BoothsTab }   from '@/features/booths/BoothsTab';
import { WorkersTab }  from '@/features/workers/WorkersTab';
import { SchemesTab }  from '@/features/schemes/SchemesTab';
import { AlertsTab }   from '@/features/intelligence/AlertsTab';
import { AIConsoleTab } from '@/features/intelligence/AIConsoleTab';
import { ExecutivePanel }     from '@/features/panels/ExecutivePanel';
import { GlobalOverviewPanel } from '@/features/panels/GlobalOverviewPanel';
import { StrategicDashboard } from '@/pages/StrategicDashboard';
import { OntologyDashboard } from '@/pages/OntologyDashboard';
import { ConstituencyPanel }  from '@/features/panels/ConstituencyPanel';
import { CommsPanel }         from '@/features/panels/CommsPanel';
import {
  Globe2, MapPin, Users, BookOpen, Bell, Sparkles, ChevronsRight,
  BarChart2, Brain, Target, MessageSquare,
} from 'lucide-react';

const TABS: { key: SidebarTab; label: string; icon: React.ReactNode }[] = [
  { key: 'global',  label: 'Global',   icon: <Globe2 size={13} />     },
  { key: 'booths',  label: 'Booths',   icon: <MapPin size={13} />    },
  { key: 'workers', label: 'Workers',  icon: <Users size={13} />     },
  { key: 'schemes', label: 'Schemes',  icon: <BookOpen size={13} />  },
  { key: 'alerts',  label: 'Signals',  icon: <Bell size={13} />      },
  { key: 'ai',      label: 'Agent',    icon: <Sparkles size={13} />  },
];

// View-specific overlay panels shown above the tabs
const VIEW_PANEL: Partial<Record<string, React.ReactNode>> = {
  cockpit:      <GlobalOverviewPanel />,
  executive:    <ExecutivePanel />,
  constituency: <ConstituencyPanel />,
  comms:        <CommsPanel />,
};

const TAB_CONTENT: Record<SidebarTab, React.ReactNode> = {
  global:  <GlobalTab />,
  booths:  <BoothsTab />,
  workers: <WorkersTab />,
  schemes: <SchemesTab />,
  alerts:  <AlertsTab />,
  ai:      <AIConsoleTab />,
};

export const IntelligenceSidebar: React.FC = () => {
  const { sidebarTab, setSidebarTab, sidebarOpen, setSidebarOpen, activeView } = useAppStore();
  const viewPanel = VIEW_PANEL[activeView];

  return (
    <AnimatePresence mode="wait">
      {sidebarOpen && (
        <motion.div
          key="sidebar"
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 35 }}
          className={clsx(
            "border-l border-zinc-800/80 bg-[#0b0b0e]/95 backdrop-blur-xl flex flex-col flex-shrink-0 relative z-30 transition-all duration-300",
            activeView === 'strategic' || activeView === 'ontology' ? "w-[60%] lg:w-[65%]" : "w-[40%]"
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800/80 shrink-0">
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse shadow-[0_0_6px_rgba(59,130,246,0.6)]" />
              <span className="text-[10px] font-mono font-bold tracking-[0.25em] text-zinc-400 uppercase">
                Intelligence Panel
              </span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-zinc-600 hover:text-zinc-400 transition-colors"
              title="Collapse panel"
            >
              <ChevronsRight size={14} />
            </button>
          </div>

          {activeView === 'strategic' ? (
            <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
              <StrategicDashboard />
            </div>
          ) : activeView === 'ontology' ? (
            <div className="flex-1 overflow-y-auto w-full custom-scrollbar p-3">
              <OntologyDashboard />
            </div>
          ) : (
            <>
              {/* View-specific context panel (collapsible) */}
              <AnimatePresence>
                {viewPanel && (
                  <motion.div
                    key={activeView}
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden border-b border-zinc-800/60 shrink-0"
                  >
                    {viewPanel}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Tab nav */}
              <div className="flex border-b border-zinc-800/80 shrink-0 overflow-x-auto">
                {TABS.map(({ key, label, icon }) => (
                  <button
                    key={key}
                    onClick={() => setSidebarTab(key)}
                    className={clsx(
                      'flex items-center space-x-1 px-3 py-2 text-[9px] font-bold uppercase tracking-wide whitespace-nowrap transition-all border-b-2 flex-1 justify-center',
                      sidebarTab === key
                        ? 'border-blue-500 text-blue-400 bg-blue-950/20'
                        : 'border-transparent text-zinc-600 hover:text-zinc-400 hover:bg-zinc-800/30'
                    )}
                  >
                    {icon}
                    <span className="hidden xl:inline">{label}</span>
                  </button>
                ))}
              </div>

              {/* Tab content */}
              <div className="flex-1 overflow-hidden p-3">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={sidebarTab}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.15 }}
                    className="h-full flex flex-col"
                  >
                    {TAB_CONTENT[sidebarTab]}
                  </motion.div>
                </AnimatePresence>
              </div>
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};
