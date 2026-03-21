import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchGlobalCountries, fetchGlobalOverview } from '@/services/api';
import { Loader2, Globe, ShieldAlert, ArrowRightLeft } from 'lucide-react';

export const GlobalOverviewPanel: React.FC = () => {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['global-overview'],
    queryFn: fetchGlobalOverview,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const { data: countries = [] } = useQuery({
    queryKey: ['global-countries'],
    queryFn: fetchGlobalCountries,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <div className="p-4 flex justify-center">
        <Loader2 className="animate-spin text-blue-400" size={18} />
      </div>
    );
  }

  const watchlist = [...countries].sort((a: any, b: any) => b.risk_index - a.risk_index).slice(0, 4);

  return (
    <div className="p-3 space-y-2">
      <div className="text-[9px] font-bold text-cyan-400 uppercase tracking-widest px-1 flex items-center space-x-2">
        <span className="w-1 h-3 rounded-full bg-cyan-500 inline-block" />
        <span>Global Ontology Pulse</span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
          <div className="text-[8px] uppercase tracking-widest text-zinc-500">Countries</div>
          <div className="text-base font-black text-zinc-100">{overview?.total_countries ?? 0}</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
          <div className="text-[8px] uppercase tracking-widest text-zinc-500">Signals</div>
          <div className="text-base font-black text-cyan-400">{overview?.total_signals ?? 0}</div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
          <div className="text-[8px] uppercase tracking-widest text-zinc-500">Stress</div>
          <div className="text-base font-black text-amber-400">{overview?.systemic_stress ?? '--'}</div>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/40 p-3">
        <div className="mb-2 flex items-center text-[9px] uppercase tracking-widest text-zinc-500">
          <ShieldAlert size={11} className="mr-1.5 text-red-400" />
          Risk Watchlist
        </div>
        <div className="space-y-1.5">
          {watchlist.map((country: any) => (
            <div key={country.id} className="flex items-center justify-between rounded-lg bg-black/20 px-2.5 py-2">
              <div className="min-w-0 pr-2">
                <div className="text-[10px] font-bold text-zinc-100 truncate">{country.name}</div>
                <div className="text-[8px] uppercase tracking-widest text-zinc-500">{country.region}</div>
              </div>
              <div className="text-[10px] font-black text-red-400">{country.risk_index}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/40 p-3 text-[10px] text-zinc-400">
        <div className="mb-1.5 flex items-center uppercase tracking-widest text-zinc-500">
          <ArrowRightLeft size={11} className="mr-1.5 text-purple-400" />
          Operating Logic
        </div>
        Countries are nodes, signals are events, and corridors express system pressure between regions.
      </div>
    </div>
  );
};
