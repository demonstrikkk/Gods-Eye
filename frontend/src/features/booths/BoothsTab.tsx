// ─────────────────────────────────────────────────────────────────────────────
// Booth Intelligence tab
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBooths } from '@/services/api';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { ListSkeleton } from '@/components/Skeleton';
import { useAppStore } from '@/store';
import { AlertTriangle, RefreshCw, Search } from 'lucide-react';
import clsx from 'clsx';

const sentBar = (s: number) =>
  s < 35 ? 'bg-red-500' : s < 55 ? 'bg-yellow-500' : 'bg-emerald-500';

export const BoothsTab: React.FC = () => {
  const { selectedId, setSelected, setHoveredItem } = useAppStore();
  const [search, setSearch] = useState('');

  const { data: booths = [], isLoading, isError, refetch, dataUpdatedAt } = useQuery({
    queryKey: ['booths'],
    queryFn: fetchBooths,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: 3,
  });

  const lastUpdated = useLastUpdated(dataUpdatedAt);

  const filtered = Array.isArray(booths) ? booths.filter((b: any) =>
    !search || b.name?.toLowerCase().includes(search.toLowerCase())
    || b.constituency_name?.toLowerCase().includes(search.toLowerCase())
  ) : [];

  if (isLoading) return <ListSkeleton count={6} />;

  if (isError) return (
    <div className="flex flex-col items-center justify-center py-12 text-center space-y-3">
      <AlertTriangle className="text-red-400" size={28} />
      <p className="text-zinc-400 text-sm">Booth data unavailable</p>
      <button
        onClick={() => refetch()}
        className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
      >
        <RefreshCw size={12} />
        <span>Retry</span>
      </button>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="relative mb-3">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={13} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search booth or constituency…"
          className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600 transition-colors"
        />
      </div>

      {/* Header row */}
      <div className="flex justify-between items-center mb-2 px-1">
        <span className="text-[10px] font-mono text-zinc-600 uppercase">{filtered?.length} booths</span>
        <span className="text-[10px] font-mono text-zinc-600">Updated {lastUpdated}</span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-0.5">
        {filtered?.map((booth: any) => (
          <button
            key={booth.id}
            onClick={() => setSelected(booth.id === selectedId ? null : booth.id, 'booth')}
            onMouseEnter={() => setHoveredItem(booth)}
            onMouseLeave={() => setHoveredItem(null)}
            className={clsx(
              'w-full text-left p-2.5 rounded-md border transition-all group',
              booth.id === selectedId
                ? 'bg-blue-950/40 border-blue-700/50'
                : 'bg-zinc-950/60 border-zinc-800/80 hover:border-zinc-600 hover:bg-zinc-900/60'
            )}
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="text-[11px] font-bold text-zinc-200 leading-tight tracking-wide uppercase">{booth.name}</div>
                <div className="text-[9px] text-zinc-500 mt-0.5 tracking-wider uppercase">{booth.constituency_name}</div>
              </div>
              <div className={clsx(
                'text-[9px] font-mono tracking-tighter font-bold px-1.5 py-0.5 rounded-sm border',
                booth.avg_sentiment < 35
                  ? 'bg-red-950/50 text-red-400 border-red-900/50'
                  : booth.avg_sentiment < 55
                    ? 'bg-amber-950/50 text-amber-400 border-amber-900/50'
                    : 'bg-emerald-950/50 text-emerald-400 border-emerald-900/50'
              )}>
                {booth.avg_sentiment}%
              </div>
            </div>

            {/* Sentiment bar */}
            <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', sentBar(booth.avg_sentiment))}
                style={{ width: `${Math.min(booth.avg_sentiment, 100)}%` }}
              />
            </div>

            {/* Top issue */}
            {booth.top_issues?.[0] && (
              <div className="mt-2 text-[8px] font-mono uppercase tracking-[0.2em] text-zinc-500 truncate text-left">
                // {booth.top_issues[0].issue}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};
