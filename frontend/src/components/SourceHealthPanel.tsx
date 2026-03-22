import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSourceHealth } from '@/services/api';
import type { SourceHealth } from '@/types';
import { Activity, AlertTriangle, CheckCircle2, CircleDashed } from 'lucide-react';

const statusMeta = (status: string) => {
  if (status === 'live' || status === 'local') {
    return {
      icon: <CheckCircle2 size={12} className="text-emerald-400" />,
      badge: 'text-emerald-400 bg-emerald-950/30 border-emerald-900/40',
    };
  }
  if (status === 'fallback') {
    return {
      icon: <AlertTriangle size={12} className="text-amber-400" />,
      badge: 'text-amber-400 bg-amber-950/30 border-amber-900/40',
    };
  }
  if (status === 'limited') {
    return {
      icon: <AlertTriangle size={12} className="text-amber-400" />,
      badge: 'text-amber-400 bg-amber-950/30 border-amber-900/40',
    };
  }
  return {
    icon: <CircleDashed size={12} className="text-zinc-500" />,
    badge: 'text-zinc-400 bg-zinc-900/40 border-zinc-800',
  };
};

export const SourceHealthPanel: React.FC = () => {
  const { data: health = [] } = useQuery({
    queryKey: ['source-health'],
    queryFn: fetchSourceHealth,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  return (
    <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/40 p-3">
      <div className="mb-3 flex items-center text-[9px] uppercase tracking-widest text-zinc-500">
        <Activity size={11} className="mr-1.5 text-cyan-400" />
        Source Health
      </div>

      <div className="space-y-2">
        {health.slice(0, 8).map((item: SourceHealth) => {
          const meta = statusMeta(item.status);
          return (
            <div
              key={item.id}
              className="flex items-center justify-between gap-3 rounded-lg border border-zinc-800/60 bg-black/20 px-2.5 py-2"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-[10px] font-bold text-zinc-100">
                  {meta.icon}
                  <span className="truncate">{item.label}</span>
                </div>
                <div className="mt-0.5 text-[8px] uppercase tracking-widest text-zinc-500">
                  {item.mode} | {item.item_count} items
                </div>
                {item.message && (
                  <div className="mt-1 line-clamp-2 text-[9px] text-zinc-400">
                    {item.message}
                  </div>
                )}
              </div>
              <div className={`rounded-full border px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest ${meta.badge}`}>
                {item.status}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
