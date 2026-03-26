import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchGlobalSignals, fetchNews } from '@/services/api';
import { useAppStore } from '@/store';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { AlertTriangle, Newspaper, Zap, ShieldCheck } from 'lucide-react';

const urgencyUI = (level: string) => {
  if (level === 'High') return { icon: <AlertTriangle size={10} className="text-red-400" />, border: 'border-red-900/50', badge: 'text-red-400 bg-red-950/30' };
  if (level === 'Medium') return { icon: <Zap size={10} className="text-amber-400" />, border: 'border-amber-900/50', badge: 'text-amber-400 bg-amber-950/30' };
  return { icon: <ShieldCheck size={10} className="text-cyan-400" />, border: 'border-cyan-900/50', badge: 'text-cyan-400 bg-cyan-950/30' };
};

export const AlertsTab: React.FC = () => {
  const { setHoveredItem, setSidebarTab } = useAppStore();

  const { data: signals = [], dataUpdatedAt } = useQuery({
    queryKey: ['global-signals'],
    queryFn: fetchGlobalSignals,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: news = [] } = useQuery({
    queryKey: ['news'],
    queryFn: fetchNews,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const lastUpdated = useLastUpdated(dataUpdatedAt);
  const combined = [
    ...signals?.map((signal: any) => ({ ...signal, kind: 'signal', text: signal.title })),
    ...news.slice(0, 10)?.map((feed: any) => ({ ...feed, kind: 'feed' })),
  ].sort((a: any, b: any) => (a.severity === 'High' || a.urgency === 'High' ? -1 : b.severity === 'High' || b.urgency === 'High' ? 1 : 0));

  return (
    <div className="flex flex-col h-full bg-transparent rounded-md overflow-hidden">
      <div className="p-3 bg-white/5 border-b border-white/10 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.2em] font-mono">Global Signals</span>
        </div>
        <span className="text-[9px] font-mono text-zinc-500 uppercase">{lastUpdated}</span>
      </div>

      <div className="m-3 p-3 rounded-md bg-blue-950/10 border border-blue-900/30 flex items-start space-x-3 shrink-0">
        <div className="w-7 h-7 rounded border border-blue-800/50 bg-blue-900/20 flex items-center justify-center shrink-0">
          <Newspaper className="text-blue-400" size={12} />
        </div>
        <div className="min-w-0 pr-1">
          <h5 className="text-[9px] font-mono uppercase font-bold text-blue-300 tracking-wider">Signal Synthesis</h5>
          <p className="text-[9px] text-zinc-400 font-sans leading-relaxed mt-0.5">
            Move to the <button onClick={() => setSidebarTab('ai')} className="text-blue-400 hover:text-blue-300 underline underline-offset-2">Intelligence Agent</button> for narrative reasoning over live signals.
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 p-3 custom-scrollbar">
        {combined?.map((item: any, index: number) => {
          const level = item.severity || item.urgency || 'Low';
          const ui = urgencyUI(level);
          return (
            <div
              key={`${item.id}-${index}`}
              onMouseEnter={() => setHoveredItem(item)}
              onMouseLeave={() => setHoveredItem(null)}
              className={`rounded-xl border bg-zinc-900/50 p-3 transition-all hover:border-zinc-700 ${ui.border}`}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-[11px] font-bold text-zinc-100 leading-snug">{item.title || item.text}</div>
                  <div className="mt-1 text-[9px] uppercase tracking-widest text-zinc-500">
                    {item.category || 'Live Feed'} | {item.source}
                  </div>
                </div>
                <div className={`rounded-full px-2 py-0.5 text-[8px] font-bold uppercase tracking-wider ${ui.badge}`}>
                  {level}
                </div>
              </div>
              <div className="text-[10px] text-zinc-400 leading-relaxed">
                {item.summary || item.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
