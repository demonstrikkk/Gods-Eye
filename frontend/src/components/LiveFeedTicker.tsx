import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { RadioTower, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';
import { apiClient, fetchGlobalOverview } from '../services/api';

const fetchFeeds = async () => {
  const { data } = await apiClient.get('/data/feeds');
  return data.data;
};

const mockFeeds = [
  { id: '1', category: 'Defense', text: 'Initializing live global feed sync...', urgency: 'High', time: 'LIVE' },
];

const getCategoryStyles = (category: string) => {
  switch (category) {
    case 'Defense': return 'text-danger border-danger/30 bg-danger/10';
    case 'Economics': return 'text-success border-success/30 bg-success/10';
    case 'Climate': return 'text-warning border-warning/30 bg-warning/10';
    case 'Conflict': return 'text-rose-400 border-rose-400/30 bg-rose-400/10';
    case 'Cyber': return 'text-sky-400 border-sky-400/30 bg-sky-400/10';
    case 'Mobility': return 'text-fuchsia-400 border-fuchsia-400/30 bg-fuchsia-400/10';
    case 'Infrastructure': return 'text-teal-400 border-teal-400/30 bg-teal-400/10';
    case 'Governance': return 'text-lime-400 border-lime-400/30 bg-lime-400/10';
    case 'Society': return 'text-primary-light border-primary/30 bg-primary/10';
    case 'Geopolitics': return 'text-purple-400 border-purple-400/30 bg-purple-400/10';
    case 'Tech': return 'text-cyan-400 border-cyan-400/30 bg-cyan-400/10';
    default: return 'text-text-muted border-border bg-panel';
  }
};

const getUrgencyIcon = (urgency: string) => {
  if (urgency === 'High') return <AlertTriangle size={12} className="inline mr-1 animate-pulse" />;
  if (urgency === 'Medium') return <Zap size={12} className="inline mr-1" />;
  return <ShieldCheck size={12} className="inline mr-1" />;
};

export const LiveFeedTicker: React.FC = () => {
  const { data: feeds } = useQuery({
    queryKey: ['live-feeds'],
    queryFn: fetchFeeds,
    refetchInterval: 30_000,
  });

  const { data: overview } = useQuery({
    queryKey: ['global-overview'],
    queryFn: fetchGlobalOverview,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const displayFeeds = feeds?.length > 0 ? feeds : mockFeeds;

  return (
    <div className="w-full bg-[#0a0a0c] border-b border-white/[0.05] h-8 flex items-center overflow-hidden relative z-50">
      <div className="flex-shrink-0 bg-danger text-white text-[10px] font-black tracking-widest px-4 h-full flex items-center uppercase z-10 shadow-[4px_0_10px_rgba(0,0,0,0.5)]">
        <RadioTower size={14} className="mr-2 animate-pulse" /> Live Intel
      </div>

      <div className="hidden md:flex items-center px-3 text-[9px] font-mono uppercase tracking-widest text-cyan-300 border-r border-white/[0.05]">
        {overview?.total_countries ?? 0} countries | {overview?.total_signals ?? 0} signals
      </div>

      <div className="absolute left-[110px] top-0 bottom-0 w-8 bg-gradient-to-r from-[#0a0a0c] to-transparent z-10 pointer-events-none" />

      <div className="flex-1 overflow-hidden relative">
        <motion.div
          className="flex whitespace-nowrap items-center"
          animate={{ x: [0, -2000] }}
          transition={{ x: { repeat: Infinity, repeatType: 'loop', duration: 40, ease: 'linear' } }}
        >
          {[...displayFeeds, ...displayFeeds, ...displayFeeds].map((feed: any, index: number) => (
            <div key={`${feed.id}-${index}`} className="flex items-center mx-6">
              <span className="text-[10px] text-text-muted/60 font-mono w-12 text-right mr-3 shrink-0">{feed.time}</span>
              <span className={`text-[9px] uppercase font-black px-2 py-0.5 rounded border mr-3 ${getCategoryStyles(feed.category)}`}>
                {getUrgencyIcon(feed.urgency)}
                {feed.category}
              </span>
              <span className="text-xs text-text-main font-medium">{feed.text}</span>
            </div>
          ))}
        </motion.div>
      </div>

      <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-[#0a0a0c] to-transparent z-10 pointer-events-none" />
    </div>
  );
};
