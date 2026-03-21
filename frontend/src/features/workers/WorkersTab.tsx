// ─────────────────────────────────────────────────────────────────────────────
// Worker Operations tab
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchWorkers } from '@/services/api';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { ListSkeleton } from '@/components/Skeleton';
import { useAppStore } from '@/store';
import { AlertTriangle, RefreshCw, Wifi, WifiOff, MapPin } from 'lucide-react';
import clsx from 'clsx';

const statusMeta = (status: string) => {
  if (status === 'Online')  return { icon: <Wifi size={10} />,    color: 'text-emerald-400 bg-emerald-950 border-emerald-800' };
  if (status === 'Field')   return { icon: <MapPin size={10} />,   color: 'text-blue-400 bg-blue-950 border-blue-800'          };
  return                           { icon: <WifiOff size={10} />, color: 'text-zinc-500 bg-zinc-900 border-zinc-800'           };
};

export const WorkersTab: React.FC = () => {
  const { data: workers = [], isLoading, isError, refetch, dataUpdatedAt } = useQuery({
    queryKey: ['workers'],
    queryFn: fetchWorkers,
    refetchInterval: 30_000,
    retry: 3,
  });

  const lastUpdated = useLastUpdated(dataUpdatedAt);
  const { setHoveredItem } = useAppStore();
  const online  = Array.isArray(workers) ? workers.filter((w: any) => w.status === 'Online').length : 0;
  const inField = Array.isArray(workers) ? workers.filter((w: any) => w.status === 'Field').length : 0;

  if (isLoading) return <ListSkeleton count={5} />;

  if (isError) return (
    <div className="flex flex-col items-center justify-center py-12 text-center space-y-3">
      <AlertTriangle className="text-red-400" size={28} />
      <p className="text-zinc-400 text-sm">Worker data unavailable</p>
      <button onClick={() => refetch()} className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors">
        <RefreshCw size={12} /><span>Retry</span>
      </button>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      {/* Stat chips */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: 'Total', value: workers.length, color: 'text-zinc-200' },
          { label: 'Online', value: online, color: 'text-emerald-400' },
          { label: 'Field', value: inField, color: 'text-blue-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-zinc-900 border border-zinc-800 rounded-lg py-2 text-center">
            <div className={clsx('text-lg font-black tabular-nums', color)}>{value}</div>
            <div className="text-[9px] text-zinc-600 uppercase tracking-widest">{label}</div>
          </div>
        ))}
      </div>

      <div className="text-[10px] font-mono text-zinc-600 mb-2 px-0.5">Updated {lastUpdated}</div>

      <div className="flex-1 overflow-y-auto space-y-1.5">
        {Array.isArray(workers) && workers.map((w: any) => {
          const { icon, color } = statusMeta(w.status);
          return (
            <div key={w.id}
              onMouseEnter={() => setHoveredItem(w)}
              onMouseLeave={() => setHoveredItem(null)}
              className="flex items-center space-x-3 p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/50 hover:border-zinc-700 transition-colors group cursor-default">
              <div className={clsx('w-8 h-8 rounded-full flex items-center justify-center border text-[10px] font-bold flex-shrink-0', color)}>
                {w.name?.[0] ?? '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-zinc-200 truncate">{w.name}</div>
                <div className="text-[10px] text-zinc-500">{w.constituency_id || 'Unassigned'}</div>
              </div>
              <div className="flex flex-col items-end space-y-1">
                <span className={clsx('flex items-center space-x-1 text-[9px] font-bold px-1.5 py-0.5 rounded border', color)}>
                  {icon}<span>{w.status}</span>
                </span>
                <div className="text-[9px] text-zinc-600">{w.performance_score}%</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
