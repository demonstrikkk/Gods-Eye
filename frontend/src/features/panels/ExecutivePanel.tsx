// Executive Panel — shown in sidebar when activeView === 'executive'
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchExecutiveKPIs } from '@/services/api';
import { useAppStore } from '@/store';
import { Activity, ShieldAlert, Users, Database, TrendingUp, Loader2 } from 'lucide-react';

const Stat: React.FC<{ label: string; value: any; suffix?: string; color: string; icon: React.ReactNode }> = ({
  label, value, suffix = '', color, icon
}) => (
  <div className="bg-zinc-900/60 border border-zinc-800/50 rounded-xl p-3 flex items-center space-x-3 hover:border-zinc-700 transition-colors">
    <div className={`p-1.5 rounded-lg bg-zinc-800 ${color}`}>{icon}</div>
    <div>
      <div className="text-[8px] text-zinc-500 uppercase tracking-widest">{label}</div>
      <div className={`text-base font-black tabular-nums ${color}`}>{value}{suffix}</div>
    </div>
  </div>
);

export const ExecutivePanel: React.FC = () => {
  const { data: kpis, isLoading } = useQuery({
    queryKey: ['executive-kpis'],
    queryFn: fetchExecutiveKPIs,
    refetchInterval: 30_000,
  });

  if (isLoading) return (
    <div className="p-4 flex justify-center">
      <Loader2 className="animate-spin text-blue-400" size={20} />
    </div>
  );

  return (
    <div className="p-3 space-y-2">
      <div className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest px-1 flex items-center space-x-2">
        <span className="w-1 h-3 rounded-full bg-emerald-500 inline-block" />
        <span>Executive KPIs — Live</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <Stat label="Nat. Sentiment" value={kpis?.national_sentiment ?? '–'} suffix="%" color="text-blue-400"    icon={<Activity size={12} />} />
        <Stat label="Critical Booths" value={kpis?.active_alerts ?? '–'}                color="text-red-400"    icon={<ShieldAlert size={12} />} />
        <Stat label="Workers Online"  value={kpis?.field_workers_online ?? '–'}         color="text-emerald-400" icon={<Users size={12} />} />
        <Stat label="Scheme Cov."     value={kpis?.scheme_coverage_pct ?? '–'} suffix="%" color="text-teal-400" icon={<Database size={12} />} />
      </div>
      <div className="bg-zinc-900/40 border border-zinc-800/30 rounded-xl p-2.5 flex items-center justify-between">
        <span className="text-[9px] text-zinc-500">Citizens Profiled</span>
        <span className="text-sm font-black text-zinc-200 tabular-nums">{kpis?.total_citizens?.toLocaleString('en-IN') ?? '–'}</span>
      </div>
    </div>
  );
};
