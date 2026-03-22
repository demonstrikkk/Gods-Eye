// ─────────────────────────────────────────────────────────────────────────────
// LayerControl — toggleable map layer buttons
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import clsx from 'clsx';
import { useAppStore } from '@/store';
import type { LayerKey } from '@/types';
import { Layers, Newspaper, Globe, Activity, ShieldAlert, CloudSun, ArrowRightLeft, Landmark, Flame, Database, Plane, Shield } from 'lucide-react';

const LAYERS: { key: LayerKey; label: string; icon: React.ReactNode; color: string }[] = [
  { key: 'countries', label: 'Countries', icon: <Globe size={12} />, color: 'text-blue-400 border-blue-500/40 bg-blue-500/10' },
  { key: 'corridors', label: 'Corridors', icon: <ArrowRightLeft size={12} />, color: 'text-purple-400 border-purple-500/40 bg-purple-500/10' },
  { key: 'economics', label: 'Economics', icon: <Activity size={12} />, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' },
  { key: 'governance', label: 'Governance', icon: <Landmark size={12} />, color: 'text-lime-400 border-lime-500/40 bg-lime-500/10' },
  { key: 'climate', label: 'Climate', icon: <CloudSun size={12} />, color: 'text-orange-400 border-orange-500/40 bg-orange-500/10' },
  { key: 'defense', label: 'Defense', icon: <ShieldAlert size={12} />, color: 'text-red-400 border-red-500/40 bg-red-500/10' },
  { key: 'conflict', label: 'Conflict', icon: <Flame size={12} />, color: 'text-rose-400 border-rose-500/40 bg-rose-500/10' },
  { key: 'infrastructure', label: 'Infra', icon: <Database size={12} />, color: 'text-teal-400 border-teal-500/40 bg-teal-500/10' },
  { key: 'mobility', label: 'Mobility', icon: <Plane size={12} />, color: 'text-fuchsia-400 border-fuchsia-500/40 bg-fuchsia-500/10' },
  { key: 'cyber', label: 'Cyber', icon: <Shield size={12} />, color: 'text-sky-400 border-sky-500/40 bg-sky-500/10' },
  { key: 'news', label: 'News', icon: <Newspaper size={12} />, color: 'text-cyan-400 border-cyan-500/40 bg-cyan-500/10' },
];

export const LayerControl: React.FC = () => {
  const { activeLayers, toggleLayer } = useAppStore();

  return (
    <div className="flex max-w-[calc(100vw-2rem)] items-center space-x-1 overflow-x-auto bg-black/60 border border-zinc-800 rounded-xl px-2 py-1.5 backdrop-blur-md">
      <Layers size={11} className="text-zinc-500 mr-1 shrink-0" />
      {LAYERS.map(({ key, label, icon, color }) => {
        const active = activeLayers.has(key);
        return (
          <button
            key={key}
            onClick={() => toggleLayer(key)}
            title={`Toggle ${label} layer`}
            className={clsx(
              'flex items-center space-x-1 px-2 py-1 rounded-lg border text-[10px] font-bold uppercase tracking-wide transition-all',
              active ? color : 'text-zinc-600 border-zinc-800 bg-transparent hover:bg-zinc-800/40'
            )}
          >
            {icon}
            <span>{label}</span>
          </button>
        );
      })}
    </div>
  );
};
