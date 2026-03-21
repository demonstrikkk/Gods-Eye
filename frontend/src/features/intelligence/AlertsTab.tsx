// ─────────────────────────────────────────────────────────────────────────────
// News Intelligence Tab — Integrated RSS feed with AI gist extraction
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchAlerts, fetchNews } from '@/services/api';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { 
  AlertTriangle, Zap, ShieldCheck, RefreshCw, 
  ExternalLink, ChevronDown, ChevronUp, Newspaper, 
  Info, Clock
} from 'lucide-react';
import clsx from 'clsx';

const urgencyStyle = (u: string) => {
  if (u === 'High') return { bar: 'bg-red-500', text: 'text-red-400', badge: 'bg-red-950 border-red-800 text-red-400', icon: <AlertTriangle size={10} /> };
  if (u === 'Medium') return { bar: 'bg-yellow-500', text: 'text-yellow-400', badge: 'bg-yellow-950 border-yellow-800 text-yellow-400', icon: <Zap size={10} /> };
  return { bar: 'bg-blue-500', text: 'text-blue-400', badge: 'bg-blue-950 border-blue-800 text-blue-400', icon: <ShieldCheck size={10} /> };
};

const NewsItem: React.FC<{ item: any }> = ({ item }) => {
  const [expanded, setExpanded] = useState(false);
  const { bar, badge, icon } = urgencyStyle(item.urgency);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      className={clsx(
        "flex flex-col space-y-2 p-3 rounded-xl bg-zinc-900/40 border transition-all cursor-pointer group",
        expanded ? "border-blue-900/50 bg-zinc-900/80" : "border-zinc-800/50 hover:border-zinc-700 hover:bg-zinc-900/60"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start space-x-2.5">
        <div className={clsx('w-0.5 h-10 rounded-full flex-shrink-0', bar)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1.5">
            <span className={clsx('flex items-center space-x-1 text-[8px] border font-bold px-2 py-0.5 rounded tracking-widest uppercase', badge)}>
              {icon}<span>{item.urgency}</span>
            </span>
            <div className="flex items-center space-x-2 text-[9px] text-zinc-600">
               <span className="flex items-center"><Newspaper size={9} className="mr-1" />{item.source}</span>
               <span className="flex items-center"><Clock size={9} className="mr-1" />{item.time || 'LIVE'}</span>
            </div>
          </div>
          <h4 className={clsx("text-[11px] font-bold leading-snug transition-colors", expanded ? "text-blue-100" : "text-zinc-200 group-hover:text-white")}>
            {item.text}
          </h4>
        </div>
        <div className="shrink-0 text-zinc-600 mt-1">
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="pt-2 mt-2 border-t border-zinc-800/60 pb-1">
              <div className="bg-black/40 rounded-lg p-3 text-[10.5px] text-zinc-400 leading-relaxed border border-zinc-800/30">
                 {item.summary || "No extracted description available for this segment."}
              </div>
              
              <div className="mt-3 flex items-center justify-between">
                <div className="flex space-x-2">
                  <span className="text-[9px] font-mono text-zinc-500 uppercase">Signal ID: {item.id?.slice(-6)}</span>
                </div>
                {item.url && (
                  <a 
                    href={item.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center space-x-1.5 text-blue-400 hover:text-blue-300 text-[10px] font-bold bg-blue-900/20 px-2.5 py-1 rounded-lg transition-all"
                  >
                    <span>Source Intelligence</span>
                    <ExternalLink size={10} />
                  </a>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export const AlertsTab: React.FC = () => {
  const {
    data: alerts = [], isLoading: aLoading, isError: aErr, refetch: aRefetch, dataUpdatedAt
  } = useQuery({ queryKey: ['alerts'], queryFn: fetchAlerts, refetchInterval: 30_000 });

  const {
    data: news = [], isLoading: nLoading
  } = useQuery({ queryKey: ['news'], queryFn: fetchNews, refetchInterval: 60_000 });

  const lastUpdated = useLastUpdated(dataUpdatedAt);
  const combined = [
    ...(Array.isArray(alerts) ? alerts : []),
    ...(Array.isArray(news) ? news : []),
  ].sort((a, b) => (a.urgency === 'High' ? -1 : b.urgency === 'High' ? 1 : 0));

  if (aLoading || nLoading) return (
    <div className="space-y-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="h-20 rounded-md bg-zinc-900/40 animate-pulse border border-zinc-800/40" />
      ))}
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-[#0d0d12]/40 rounded-md overflow-hidden">
      {/* Tab Header with Intelligence Gist Call-to-Action */}
      <div className="p-3 bg-zinc-950/60 border-b border-zinc-800/80 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          <span className="text-[10px] font-bold text-zinc-300 uppercase tracking-[0.2em] font-mono">Global Signals</span>
        </div>
        <span className="text-[9px] font-mono text-zinc-500 uppercase">{lastUpdated}</span>
      </div>

      {/* Embedded News AI Quick Analysis CTA */}
      <div className="m-3 p-3 rounded-md bg-blue-950/10 border border-blue-900/30 flex items-start space-x-3 shrink-0">
        <div className="w-7 h-7 rounded border border-blue-800/50 bg-blue-900/20 flex items-center justify-center shrink-0">
           <Zap className="text-blue-400" size={12} />
        </div>
        <div className="min-w-0 pr-1">
          <h5 className="text-[9px] font-mono uppercase font-bold text-blue-300 tracking-wider">Automated OSINT Synthesis</h5>
          <p className="text-[9px] text-zinc-400 font-sans leading-relaxed mt-0.5">
            Switch to the <button onClick={() => setSidebarTab('ai')} className="text-blue-400 hover:text-blue-300 underline underline-offset-2">Intelligence Agent</button> to extract custom reasoning from these live feeds.
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 p-3 custom-scrollbar">
        {combined.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center space-y-3 opacity-30">
             <RefreshCw className="animate-spin-slow" size={32} />
             <p className="text-[10px] uppercase font-bold tracking-widest">Awaiting Remote Signals...</p>
          </div>
        ) : (
          <AnimatePresence>
            {combined.map((item: any, i) => (
              <NewsItem key={`${item.id}-${i}`} item={item} />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};
