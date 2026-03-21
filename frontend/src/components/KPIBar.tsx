import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchExecutiveKPIs, fetchGlobalOverview } from '@/services/api';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { Activity, AlertTriangle, Users, Globe2, TrendingUp } from 'lucide-react';
import clsx from 'clsx';

interface KPIItemProps {
  label: string;
  value: string | number;
  suffix?: string;
  icon: React.ReactNode;
  colorClass: string;
  loading?: boolean;
}

const KPIItem: React.FC<KPIItemProps> = ({ label, value, suffix, icon, colorClass, loading }) => (
  <div className="flex items-center space-x-2.5 border-r border-zinc-800/80 px-4 last:border-r-0">
    <div className={clsx('flex-shrink-0', colorClass)}>{icon}</div>
    <div>
      <div className="text-[9px] font-bold uppercase tracking-widest text-zinc-600">{label}</div>
      {loading ? (
        <div className="mt-0.5 h-4 w-14 animate-pulse rounded bg-zinc-800" />
      ) : (
        <div className={clsx('text-sm font-black leading-tight tabular-nums', colorClass)}>
          {value}{suffix}
        </div>
      )}
    </div>
  </div>
);

export const KPIBar: React.FC = () => {
  const { data: kpis, isLoading, dataUpdatedAt } = useQuery({
    queryKey: ['executive-kpis'],
    queryFn: fetchExecutiveKPIs,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const { data: globalOverview } = useQuery({
    queryKey: ['global-overview'],
    queryFn: fetchGlobalOverview,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const lastUpdated = useLastUpdated(dataUpdatedAt);
  const sentiment = kpis?.national_sentiment ?? null;

  return (
    <div className="flex h-12 w-full shrink-0 items-center border-b border-zinc-800/80 bg-[#0b0b0e]/90 backdrop-blur-sm">
      <KPIItem
        label="Nat. Sentiment"
        value={sentiment ?? '—'}
        suffix="%"
        icon={<Activity size={14} />}
        colorClass={sentiment < 40 ? 'text-red-400' : sentiment < 60 ? 'text-yellow-400' : 'text-emerald-400'}
        loading={isLoading}
      />
      <KPIItem
        label="Global Stress"
        value={globalOverview?.systemic_stress ?? '—'}
        icon={<TrendingUp size={14} />}
        colorClass="text-amber-400"
        loading={isLoading}
      />
      <KPIItem
        label="Critical Zones"
        value={globalOverview?.critical_zones ?? '—'}
        icon={<AlertTriangle size={14} />}
        colorClass="text-red-400"
        loading={isLoading}
      />
      <KPIItem
        label="Workers Online"
        value={kpis?.field_workers_online ?? '—'}
        icon={<Users size={14} />}
        colorClass="text-emerald-400"
        loading={isLoading}
      />
      <KPIItem
        label="Countries"
        value={globalOverview?.total_countries ?? '—'}
        icon={<Globe2 size={14} />}
        colorClass="text-blue-400"
        loading={isLoading}
      />

      <div className="ml-auto whitespace-nowrap pr-4 text-[9px] font-mono text-zinc-700">
        {!isLoading && <>Updated {lastUpdated}</>}
      </div>
    </div>
  );
};
