import React, { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, RadioTower, Shield, Wifi } from 'lucide-react';
import { fetchSourceHealth } from '@/services/api';
import { CountrySearchCommand } from '@/features/map/CountrySearchCommand';

export const StatusBar: React.FC = () => {
  const [time, setTime] = useState(() => new Date().toISOString());
  const { data: sourceHealth = [] } = useQuery({
    queryKey: ['source-health'],
    queryFn: fetchSourceHealth,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toISOString()), 1000);
    return () => clearInterval(id);
  }, []);

  const statusSummary = useMemo(() => {
    const live = sourceHealth.filter((item) => item.status === 'live' || item.status === 'local').length;
    const degraded = sourceHealth.filter((item) => !['live', 'local'].includes(item.status)).length;
    return { live, degraded };
  }, [sourceHealth]);

  const timestamp = new Date(time);
  const hh = timestamp.getHours().toString().padStart(2, '0');
  const mm = timestamp.getMinutes().toString().padStart(2, '0');
  const ss = timestamp.getSeconds().toString().padStart(2, '0');

  return (
    <div className="z-50 flex h-11 w-full shrink-0 items-center gap-3 border-b border-zinc-800/80 bg-[#050507] px-4 text-[10px] font-mono">
      <div className="flex shrink-0 items-center space-x-4 text-zinc-500">
        <span className="flex items-center space-x-1.5">
          <Shield size={10} className="text-cyan-300" />
          <span className="font-bold uppercase tracking-widest text-cyan-300">JANGRAPH OS</span>
          <span className="text-zinc-600">·</span>
          <span>SOVEREIGN NODE</span>
        </span>
        <span className="text-zinc-700">|</span>
        <span className="flex items-center space-x-1.5">
          <Wifi size={10} className={statusSummary.degraded ? 'text-amber-300' : 'text-emerald-400'} />
          <span className={statusSummary.degraded ? 'text-amber-300' : 'text-emerald-400'}>
            {statusSummary.degraded ? 'DEGRADED' : 'LIVE'}
          </span>
        </span>
      </div>

      <div className="min-w-0 flex-1">
        <CountrySearchCommand />
      </div>

      <div className="hidden shrink-0 items-center space-x-1 text-zinc-600 xl:flex">
        <RadioTower size={9} className="text-cyan-300" />
        <span>{statusSummary.live} live connectors · {statusSummary.degraded} degraded/unavailable</span>
      </div>

      <div className="flex shrink-0 items-center space-x-1.5 text-zinc-500">
        <Clock size={10} />
        <span className="tabular-nums">{hh}:{mm}:{ss}</span>
        <span className="text-zinc-700">IST</span>
      </div>
    </div>
  );
};
