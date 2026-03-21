// ─────────────────────────────────────────────────────────────────────────────
// KPIBar — top horizontal stats strip fed from executive KPIs endpoint
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchExecutiveKPIs } from '@/services/api';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { Activity, AlertTriangle, Users, Database, TrendingUp, TrendingDown } from 'lucide-react';
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
  <div className="flex items-center space-x-2.5 px-4 border-r border-zinc-800/80 last:border-r-0">
    <div className={clsx('flex-shrink-0', colorClass)}>{icon}</div>
    <div>
      <div className="text-[9px] text-zinc-600 uppercase tracking-widest font-bold">{label}</div>
      {loading ? (
        <div className="h-4 w-14 bg-zinc-800 animate-pulse rounded mt-0.5" />
      ) : (
        <div className={clsx('text-sm font-black tabular-nums leading-tight', colorClass)}>
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

  const lastUpdated = useLastUpdated(dataUpdatedAt);
  const sentiment = kpis?.national_sentiment ?? null;
  const prevSentiment = 48; // track sign change; use actual delta if backend provides it

  return (
    <div className="h-12 w-full bg-[#0b0b0e]/90 border-b border-zinc-800/80 backdrop-blur-sm flex items-center shrink-0">
      <KPIItem label="Nat. Sentiment" value={sentiment ?? '–'} suffix="%" icon={<Activity size={14} />} colorClass={sentiment < 40 ? 'text-red-400' : sentiment < 60 ? 'text-yellow-400' : 'text-emerald-400'} loading={isLoading} />
      <KPIItem label="Critical Booths" value={kpis?.active_alerts ?? '–'} icon={<AlertTriangle size={14} />} colorClass="text-red-400" loading={isLoading} />
      <KPIItem label="Workers Online" value={kpis?.field_workers_online ?? '–'} icon={<Users size={14} />} colorClass="text-emerald-400" loading={isLoading} />
      <KPIItem label="Scheme Coverage" value={kpis?.scheme_coverage_pct ?? '–'} suffix="%" icon={<Database size={14} />} colorClass="text-blue-400" loading={isLoading} />
      <KPIItem label="Citizens" value={kpis?.total_citizens?.toLocaleString('en-IN') ?? '–'} icon={<TrendingUp size={14} />} colorClass="text-zinc-300" loading={isLoading} />

      {/* Spacer + timestamp */}
      <div className="ml-auto pr-4 text-[9px] font-mono text-zinc-700 whitespace-nowrap">
        {!isLoading && <>Updated {lastUpdated}</>}
      </div>
    </div>
  );
};
