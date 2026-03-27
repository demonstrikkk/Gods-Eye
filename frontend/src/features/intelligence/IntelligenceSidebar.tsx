import React, { Suspense, lazy, useEffect } from 'react';
import clsx from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '@/store';
import type { SidebarTab } from '@/types';
import {
  Globe2,
  MapPin,
  Users,
  BookOpen,
  Bell,
  Sparkles,
  ChevronsRight,
  Swords,
  Crown,
  Folder,
  Layers3,
} from 'lucide-react';

const GlobalTab = lazy(() => import('@/features/global/GlobalTab').then((module) => ({ default: module.GlobalTab })));
const BoothsTab = lazy(() => import('@/features/booths/BoothsTab').then((module) => ({ default: module.BoothsTab })));
const WorkersTab = lazy(() => import('@/features/workers/WorkersTab').then((module) => ({ default: module.WorkersTab })));
const SchemesTab = lazy(() => import('@/features/schemes/SchemesTab').then((module) => ({ default: module.SchemesTab })));
const AlertsTab = lazy(() => import('@/features/intelligence/AlertsTab').then((module) => ({ default: module.AlertsTab })));
const AIConsoleTab = lazy(() => import('@/features/intelligence/AIConsoleTab').then((module) => ({ default: module.AIConsoleTab })));
const ExpertAnalysisTab = lazy(() => import('@/features/intelligence/ExpertAnalysisTab'));
const VisualIntelligenceTab = lazy(() => import('@/features/intelligence/VisualIntelligenceTab'));
const UnifiedIntelligenceTab = lazy(() => import('@/features/intelligence/UnifiedIntelligenceTab'));
const BattlegroundTab = lazy(() => import('@/features/intelligence/BattlegroundTab'));
const OfficialsTab = lazy(() => import('@/features/intelligence/OfficialsTab'));
const CountryWorkspaceTab = lazy(() => import('@/features/intelligence/CountryWorkspaceTab').then((module) => ({ default: module.CountryWorkspaceTab })));
const ExecutivePanel = lazy(() => import('@/features/panels/ExecutivePanel').then((module) => ({ default: module.ExecutivePanel })));
const GlobalOverviewPanel = lazy(() => import('@/features/panels/GlobalOverviewPanel').then((module) => ({ default: module.GlobalOverviewPanel })));
const StrategicDashboard = lazy(() => import('@/pages/StrategicDashboard').then((module) => ({ default: module.StrategicDashboard })));
const OntologyDashboard = lazy(() => import('@/pages/OntologyDashboard').then((module) => ({ default: module.OntologyDashboard })));
const ConstituencyPanel = lazy(() => import('@/features/panels/ConstituencyPanel').then((module) => ({ default: module.ConstituencyPanel })));
const CommsPanel = lazy(() => import('@/features/panels/CommsPanel').then((module) => ({ default: module.CommsPanel })));

const PanelLoading = () => (
  <div className="rounded-xl border border-white/10 bg-black/25 p-4 text-xs uppercase tracking-[0.2em] text-zinc-500">
    Loading intelligence panel...
  </div>
);

type TabItem = {
  key: SidebarTab;
  label: string;
  icon: React.ReactNode;
};

const TAB_GROUPS: { title: string; tabs: TabItem[] }[] = [
  {
    title: 'Core Intelligence',
    tabs: [
      { key: 'global', label: 'Global', icon: <Globe2 size={13} /> },
      { key: 'booths', label: 'Booths', icon: <MapPin size={13} /> },
      { key: 'workers', label: 'Workers', icon: <Users size={13} /> },
      { key: 'schemes', label: 'Schemes', icon: <BookOpen size={13} /> },
      { key: 'alerts', label: 'Signals', icon: <Bell size={13} /> },
      { key: 'workspace', label: 'Workspace', icon: <Folder size={13} /> },
    ],
  },
  {
    title: 'Analyst Tools',
    tabs: [
      { key: 'unified', label: 'Unified', icon: <Sparkles size={13} /> },
      { key: 'battleground', label: 'Battle', icon: <Swords size={13} /> },
      { key: 'officials', label: 'Leaders', icon: <Crown size={13} /> },
    ],
  },
];

const VIEW_PANEL: Partial<Record<string, React.ReactNode>> = {
  cockpit: <GlobalOverviewPanel />,
  executive: <ExecutivePanel />,
  constituency: <ConstituencyPanel />,
  comms: <CommsPanel />,
};

const TAB_CONTENT: Record<SidebarTab, React.ReactNode> = {
  global: <GlobalTab />,
  booths: <BoothsTab />,
  workers: <WorkersTab />,
  schemes: <SchemesTab />,
  alerts: <AlertsTab />,
  ai: <AIConsoleTab />,
  expert: <ExpertAnalysisTab />,
  visual: <VisualIntelligenceTab />,
  unified: <UnifiedIntelligenceTab />,
  battleground: <BattlegroundTab />,
  officials: <OfficialsTab />,
  workspace: <CountryWorkspaceTab />,
};

function SidebarTabButton({
  tab,
  active,
  onClick,
}: {
  tab: TabItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'group flex items-center gap-2 rounded-xl border px-3 py-2 text-left text-[10px] font-semibold uppercase tracking-[0.18em] transition-all',
        active
          ? 'border-cyan-500/30 bg-cyan-500/12 text-cyan-300 shadow-[0_0_0_1px_rgba(34,211,238,0.08)]'
          : 'border-white/5 bg-white/[0.02] text-zinc-500 hover:border-white/10 hover:bg-white/[0.04] hover:text-zinc-200'
      )}
    >
      <span
        className={clsx(
          'grid h-6 w-6 place-items-center rounded-lg border transition-colors',
          active
            ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-300'
            : 'border-white/5 bg-black/20 text-zinc-400 group-hover:text-zinc-200'
        )}
      >
        {tab.icon}
      </span>
      <span className="truncate">{tab.label}</span>
      {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-300" />}
    </button>
  );
}

export const IntelligenceSidebar: React.FC = () => {
  const sidebarTab = useAppStore((state) => state.sidebarTab);
  const setSidebarTab = useAppStore((state) => state.setSidebarTab);
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setSidebarOpen);
  const activeView = useAppStore((state) => state.activeView);
  const selectedId = useAppStore((state) => state.selectedId);
  const selectedType = useAppStore((state) => state.selectedType);

  useEffect(() => {
    if (sidebarTab === 'ai' || sidebarTab === 'expert' || sidebarTab === 'visual') {
      setSidebarTab('unified');
    }
  }, [setSidebarTab, sidebarTab]);

  const viewPanel = sidebarTab === 'battleground' ? null : VIEW_PANEL[activeView];
  const panelTitle =
    sidebarTab === 'battleground'
      ? 'Simulation War-Room'
      : sidebarTab === 'unified'
        ? 'Unified Analysis'
      : activeView === 'expert'
        ? 'Expert Multi-Agent Analysis'
        : selectedType === 'country' && selectedId
          ? `Country Research - ${selectedId.replace('CTR-', '')}`
          : 'Research Panel';

  const panelSubtitle =
    sidebarTab === 'unified'
      ? 'Auto-detected capability orchestration and synthesis'
      : activeView === 'strategic'
      ? 'High-signal analytics, live data, and synthesis'
      : activeView === 'ontology'
        ? 'Concept graph and relationship mapping'
        : 'Operational intelligence workspace';

  return (
    <AnimatePresence mode="wait">
      {sidebarOpen && (
        <motion.aside
          key="sidebar"
          initial={{ opacity: 0, x: 18 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 18 }}
          transition={{ duration: 0.22, ease: 'easeOut' }}
          className="flex h-full w-full min-h-0 flex-col overflow-y-auto overflow-x-hidden bg-zinc-950/90 text-white shadow-2xl custom-scrollbar"
        >
          <div className="sticky top-0 z-20 border-b border-white/5 bg-zinc-950/85 px-4 py-3 backdrop-blur-xl">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.75)]" />
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-[0.28em] text-zinc-400">
                    {panelTitle}
                  </span>
                </div>
                <p className="mt-1 text-xs text-zinc-500">{panelSubtitle}</p>
              </div>

              <button
                onClick={() => setSidebarOpen(false)}
                className="rounded-lg border border-white/5 bg-white/[0.03] p-2 text-zinc-500 transition-colors hover:border-white/10 hover:text-white"
                title="Collapse panel"
              >
                <ChevronsRight size={14} />
              </button>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-zinc-500">
              <span className="rounded-full border border-white/5 bg-white/[0.02] px-2.5 py-1">Live context</span>
              <span className="rounded-full border border-white/5 bg-white/[0.02] px-2.5 py-1">
                {activeView.replace('_', ' ')}
              </span>
              <span className="rounded-full border border-white/5 bg-white/[0.02] px-2.5 py-1">
                {sidebarTab.replace('_', ' ')}
              </span>
            </div>
          </div>

          <div className="flex-1 min-h-0 space-y-4 p-4">
            {activeView === 'strategic' ? (
              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-3">
                <Suspense fallback={<PanelLoading />}>
                  <StrategicDashboard />
                </Suspense>
              </div>
            ) : activeView === 'ontology' ? (
              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-3">
                <Suspense fallback={<PanelLoading />}>
                  <OntologyDashboard />
                </Suspense>
              </div>
            ) : activeView === 'expert' ? (
              <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-3">
                <Suspense fallback={<PanelLoading />}>
                  <ExpertAnalysisTab />
                </Suspense>
              </div>
            ) : sidebarTab === 'unified' ? (
              <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-cyan-500/15 bg-gradient-to-br from-cyan-500/5 via-white/[0.02] to-violet-500/5 p-3">
                <div className="mb-3 flex items-center justify-between gap-3 border-b border-white/5 pb-3">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-cyan-300">
                      Unified Analysis
                    </div>
                    <p className="mt-1 text-xs text-zinc-500">
                      Full-screen orchestration for reasoning, tools, visuals, and map intelligence.
                    </p>
                  </div>
                  <div className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-300">
                    Live
                  </div>
                </div>
                <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden custom-scrollbar">
                  <Suspense fallback={<PanelLoading />}>
                    <UnifiedIntelligenceTab />
                  </Suspense>
                </div>
              </div>
            ) : (
              <>
                {viewPanel && (
                  <motion.section
                    key={activeView}
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.18 }}
                    className="rounded-2xl border border-white/5 bg-white/[0.03] p-3"
                  >
                    <Suspense fallback={<PanelLoading />}>
                      {viewPanel}
                    </Suspense>
                  </motion.section>
                )}

                <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-3">
                  <div className="mb-3 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.24em] text-zinc-500">
                    <Layers3 size={12} />
                    Panels
                  </div>

                  <div className="space-y-4">
                    {TAB_GROUPS.map((group) => (
                      <div key={group.title} className="space-y-2">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                          {group.title}
                        </div>
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-2">
                          {group.tabs.map((tab) => (
                            <SidebarTabButton
                              key={tab.key}
                              tab={tab}
                              active={sidebarTab === tab.key}
                              onClick={() => setSidebarTab(tab.key)}
                            />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-2xl border border-white/5 bg-black/20 p-3">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={sidebarTab}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.16 }}
                      className="min-h-0"
                    >
                      <Suspense fallback={<PanelLoading />}>
                        {TAB_CONTENT[sidebarTab]}
                      </Suspense>
                    </motion.div>
                  </AnimatePresence>
                </section>
              </>
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
};
