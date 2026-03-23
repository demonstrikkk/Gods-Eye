// ─────────────────────────────────────────────────────────────────────────────
// ViewNav — horizontal mode switcher for all intelligence views
// Each mode drives what the Intelligence Sidebar shows
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import { useAppStore, type ActiveView } from '@/store';
import {
  Globe, BarChart2, Brain, Target, Users,
  Database, MessageSquare, AlertTriangle, Network, Sparkles,
} from 'lucide-react';
import clsx from 'clsx';

interface ViewItem {
  key: ActiveView;
  label: string;
  icon: React.ReactNode;
  color: string;
}

const VIEWS: ViewItem[] = [
  { key: 'cockpit',      label: 'Cockpit',     icon: <Globe size={12} />,         color: 'text-blue-400' },
  { key: 'executive',    label: 'Executive',   icon: <BarChart2 size={12} />,      color: 'text-emerald-400' },
  { key: 'strategic',    label: 'Strategic',   icon: <Brain size={12} />,          color: 'text-purple-400' },
  { key: 'expert',       label: 'Expert AI',   icon: <Sparkles size={12} />,       color: 'text-amber-400' },
  { key: 'constituency', label: 'Lens',        icon: <Target size={12} />,         color: 'text-orange-400' },
  { key: 'workers',      label: 'Workers',     icon: <Users size={12} />,          color: 'text-cyan-400' },
  { key: 'schemes',      label: 'Schemes',     icon: <Database size={12} />,       color: 'text-teal-400' },
  { key: 'comms',        label: 'Comms',       icon: <MessageSquare size={12} />,  color: 'text-pink-400' },
  { key: 'alerts',       label: 'Risk Alerts', icon: <AlertTriangle size={12} />,  color: 'text-red-400' },
  { key: 'ontology',     label: 'Ontology',    icon: <Network size={12} />,        color: 'text-indigo-400' },
];

export const ViewNav: React.FC = () => {
  const { activeView, setActiveView, setSidebarOpen, setSidebarTab } = useAppStore();

  const handleViewChange = (view: ActiveView) => {
    setActiveView(view);
    setSidebarOpen(true);
    // Map to closest sidebar tab
    if (view === 'cockpit')      setSidebarTab('global');
    if (view === 'executive')    setSidebarTab('booths');
    if (view === 'strategic')    setSidebarTab('ai');
    if (view === 'expert')       setSidebarTab('expert');
    if (view === 'constituency') setSidebarTab('booths');
    if (view === 'workers')      setSidebarTab('workers');
    if (view === 'schemes')      setSidebarTab('schemes');
    if (view === 'comms')        setSidebarTab('alerts');
    if (view === 'alerts')       setSidebarTab('alerts');
    if (view === 'ontology')     setSidebarTab('global');
  };

  return (
    <div className="h-9 w-full bg-[#07070a] border-b border-zinc-800/60 flex items-center px-3 space-x-0.5 shrink-0 overflow-x-auto">
      {VIEWS.map(({ key, label, icon, color }) => {
        const active = activeView === key;
        return (
          <button
            key={key}
            onClick={() => handleViewChange(key)}
            className={clsx(
              'flex items-center space-x-1.5 px-3 h-7 rounded-md text-[9px] font-bold uppercase tracking-widest whitespace-nowrap transition-all',
              active
                ? `bg-zinc-800 border border-zinc-700 ${color}`
                : 'text-zinc-600 hover:text-zinc-300 hover:bg-zinc-800/40 border border-transparent'
            )}
          >
            <span className={active ? color : ''}>{icon}</span>
            <span>{label}</span>
            {active && (
              <span className={clsx('w-1 h-1 rounded-full', color.replace('text-', 'bg-'))} />
            )}
          </button>
        );
      })}
    </div>
  );
};
