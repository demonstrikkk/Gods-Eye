// ConstituencyPanel — shown when activeView === 'constituency'
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBooths } from '@/services/api';
import { useAppStore } from '@/store';
import { Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const sentColor = (s: number) => s < 40 ? 'text-red-400' : s < 60 ? 'text-amber-400' : 'text-emerald-400';
const sentBg = (s: number) => s < 40 ? 'border-red-900/50 bg-red-950/20' : s < 60 ? 'border-amber-900/50 bg-amber-950/20' : 'border-emerald-900/50 bg-emerald-950/20';

export const ConstituencyPanel: React.FC = () => {
  const { setHoveredItem, setSidebarTab } = useAppStore();
  const { data: booths = [], isLoading } = useQuery({
    queryKey: ['booths'],
    queryFn: fetchBooths,
    refetchInterval: 60_000,
  });

  const safeBooths = Array.isArray(booths) ? booths : [];
  const sorted = [...safeBooths].sort((a: any, b: any) => a.avg_sentiment - b.avg_sentiment);
  const critical = sorted.slice(0, 5);

  if (isLoading) return (
    <div className="p-4 flex justify-center"><Loader2 className="animate-spin text-orange-400" size={20} /></div>
  );

  return (
    <div className="p-3 space-y-2">
      <div className="text-[9px] font-bold text-orange-400 uppercase tracking-widest px-1 flex items-center space-x-2">
        <span className="w-1 h-3 rounded-full bg-orange-500 inline-block" />
        <span>Critical Constituencies</span>
      </div>

      {critical?.map((b: any) => (
        <div
          key={b.id}
          onMouseEnter={() => setHoveredItem(b)}
          onMouseLeave={() => setHoveredItem(null)}
          onClick={() => { setHoveredItem(null); setSidebarTab('booths'); }}
          className={`rounded-xl p-2.5 border cursor-pointer transition-all hover:scale-[1.01] ${sentBg(b.avg_sentiment)}`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold text-zinc-200 truncate pr-2">{b.name}</span>
            <span className={`text-sm font-black tabular-nums ${sentColor(b.avg_sentiment)}`}>{b.avg_sentiment}%</span>
          </div>
          <div className="text-[8px] text-zinc-500">{b.constituency_name} · {b.state}</div>
          {b.top_issues?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {b.top_issues.slice(0, 2)?.map((iss: any, i: number) => (
                <span key={i} className="text-[7px] text-zinc-400 bg-zinc-900/60 border border-zinc-800 px-1.5 py-0.5 rounded-full">
                  {iss.issue}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}

      <div className="text-[9px] text-zinc-600 text-center pt-1">
        {safeBooths?.length} total booths monitored
      </div>
    </div>
  );
};
