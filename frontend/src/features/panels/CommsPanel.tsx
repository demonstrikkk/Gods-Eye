// CommsPanel — shown when activeView === 'comms'
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchGlobalSignals } from '@/services/api';
import { useAppStore } from '@/store';
import { Loader2 } from 'lucide-react';
import clsx from 'clsx';

const urgencyUI = (u: string) => {
  if (u === 'High') return { dot: 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.6)]', text: 'text-red-400', label: 'CRITICAL' };
  if (u === 'Medium') return { dot: 'bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)]', text: 'text-amber-400', label: 'ELEVATED' };
  return { dot: 'bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.6)]', text: 'text-blue-400', label: 'NOMINAL' };
};

export const CommsPanel: React.FC = () => {
  const { setHoveredItem } = useAppStore();
  const { data: signals = [], isLoading } = useQuery({
    queryKey: ['global-signals'],
    queryFn: fetchGlobalSignals,
    refetchInterval: 60_000,
  });

  const safeSignals = Array.isArray(signals) ? signals : [];
  const top = [...safeSignals].sort((a: any, b: any) => (a.severity === 'High' ? -1 : b.severity === 'High' ? 1 : 0)).slice(0, 6);

  if (isLoading) return (
    <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-pink-400" size={20} /></div>
  );

  return (
    <div className="p-3 space-y-2">
      <div className="text-[9px] font-bold text-pink-400 uppercase tracking-widest px-1 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-1 h-3 rounded-full bg-pink-500 inline-block" />
          <span>Live Signal Feed</span>
        </div>
        <span className="text-zinc-600">{safeSignals?.length} total</span>
      </div>

      {top?.map((signal: any, i: number) => {
        const ui = urgencyUI(signal.severity);
        return (
          <div
            key={signal.id || i}
            onMouseEnter={() => setHoveredItem(signal)}
            onMouseLeave={() => setHoveredItem(null)}
            className="flex items-start space-x-2.5 p-2.5 rounded-xl bg-zinc-900/30 border border-zinc-800/40 hover:border-zinc-700 transition-all cursor-default"
          >
            <span className={clsx('w-1.5 h-1.5 rounded-full mt-1.5 shrink-0', ui.dot)} />
            <div className="min-w-0">
              <div className="flex items-center space-x-1.5 mb-0.5">
                <span className={clsx('text-[7px] font-bold uppercase tracking-widest', ui.text)}>{ui.label}</span>
                <span className="text-[7px] text-zinc-600">{signal.source}</span>
              </div>
              <p className="text-[10px] text-zinc-300 leading-snug line-clamp-2">{signal.title}</p>
            </div>
          </div>
        );
      })}

      {safeSignals?.length === 0 && (
        <div className="text-center py-4 text-[10px] text-zinc-600">No active signals</div>
      )}
    </div>
  );
};
