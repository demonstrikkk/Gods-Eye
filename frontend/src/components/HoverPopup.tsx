// ─────────────────────────────────────────────────────────────────────────────
// HoverPopup — global glassmorphic floating card for hovered items
// Triggered by setHoveredItem in the store, positioned near mouse
// ─────────────────────────────────────────────────────────────────────────────

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '@/store';
import { X, ExternalLink, AlertTriangle, Zap, Shield, CheckCircle } from 'lucide-react';
import clsx from 'clsx';

const sentimentColor = (s: number) => s < 35 ? 'text-red-400' : s < 55 ? 'text-amber-400' : 'text-emerald-400';
const sentimentBg   = (s: number) => s < 35 ? 'bg-red-950/50 border-red-900' : s < 55 ? 'bg-amber-950/50 border-amber-900' : 'bg-emerald-950/50 border-emerald-900';
const urgencyIcon   = (u: string) => u === 'High' ? <AlertTriangle size={12} className="text-red-400" /> : u === 'Medium' ? <Zap size={12} className="text-amber-400" /> : <Shield size={12} className="text-blue-400" />;

export const HoverPopup: React.FC = () => {
  const { hoveredItem, setHoveredItem } = useAppStore();
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => setMousePos({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', onMouseMove);
    return () => window.removeEventListener('mousemove', onMouseMove);
  }, []);

  if (!hoveredItem) return null;

  // Smart positioning: flip if too close to edge
  const W = window.innerWidth;
  const H = window.innerHeight;
  const popupW = 280;
  const popupH = 200;
  const left = mousePos.x + 18 + popupW > W ? mousePos.x - popupW - 12 : mousePos.x + 18;
  const top  = mousePos.y + 18 + popupH > H ? mousePos.y - popupH - 12 : mousePos.y + 18;

  const item = hoveredItem;

  return (
    <AnimatePresence>
      <motion.div
        ref={ref}
        initial={{ opacity: 0, scale: 0.94, y: 6 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94 }}
        transition={{ duration: 0.12 }}
        style={{ position: 'fixed', left, top, zIndex: 9999, minWidth: popupW, maxWidth: 320, pointerEvents: 'none' }}
        className="bg-[#0a0a0d]/95 border border-zinc-800 rounded-lg shadow-[0_12px_40px_rgba(0,0,0,0.8)] backdrop-blur-xl overflow-hidden"
      >
        {/* Top accent line */}
        <div className="h-0.5 w-full bg-gradient-to-r from-blue-600/80 via-purple-600/80 to-transparent" />

        <div className="p-4 space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="min-w-0 pr-2">
              <h4 className="text-[12px] font-black text-zinc-100 leading-tight truncate">
                {item.name || item.title || item.text?.slice(0, 60) || 'Intelligence Signal'}
              </h4>
              {item.constituency_name && (
                <div className="text-[9px] text-zinc-500 mt-0.5 uppercase tracking-widest">{item.constituency_name}</div>
              )}
              {item.source && (
                <div className="text-[9px] text-zinc-500 mt-0.5 uppercase tracking-widest">{item.source}</div>
              )}
            </div>
            {item.urgency && (
              <div className="flex items-center space-x-1 shrink-0">
                {urgencyIcon(item.urgency)}
              </div>
            )}
          </div>

          {/* Booth-type data */}
          {item.avg_sentiment !== undefined && (
            <div className={clsx('rounded bg-zinc-950/50 px-3 py-2 border', sentimentBg(item.avg_sentiment))}>
              <div className="flex items-center justify-between">
                <span className="text-[8.5px] text-zinc-500 uppercase tracking-widest font-mono">Sentiment</span>
                <span className={clsx('text-base font-black font-mono tracking-tight', sentimentColor(item.avg_sentiment))}>
                  {item.avg_sentiment}%
                </span>
              </div>
              {item.top_issues?.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {item.top_issues.slice(0, 3).map((issue: any, i: number) => (
                    <span key={i} className="text-[8px] font-mono tracking-wide uppercase bg-zinc-900 border border-zinc-800/80 text-zinc-400 px-1.5 py-0.5 rounded-sm">
                      {issue.issue || issue}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* News/alert-type data */}
          {item.urgency && item.text && (
            <p className="text-[10px] text-zinc-300 leading-relaxed line-clamp-3">{item.text}</p>
          )}

          {/* Worker-type data */}
          {item.performance_score !== undefined && (
            <div className="flex items-center space-x-3">
              <div className="flex-1 h-1 rounded-full bg-zinc-900 overflow-hidden border border-zinc-800">
                <div
                  className="h-full rounded-full bg-blue-500"
                  style={{ width: `${item.performance_score}%` }}
                />
              </div>
              <span className="text-[10px] font-mono font-bold text-zinc-300">{item.performance_score}%</span>
            </div>
          )}

          {/* Status badge */}
          {item.status && (
            <div className="flex items-center space-x-1.5">
              <span className={clsx(
                'w-1.5 h-1.5 rounded-full',
                item.status === 'Online' ? 'bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.8)]' : item.status === 'Field' ? 'bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.8)]' : 'bg-zinc-600'
              )} />
              <span className="text-[9px] font-mono text-zinc-400 uppercase tracking-[0.2em]">{item.status}</span>
            </div>
          )}

          {/* Geo event */}
          {item.fatalities !== undefined && (
            <div className="text-[9px] font-mono text-zinc-400 uppercase tracking-widest">
              Fatality count: <span className="font-bold text-red-500">{item.fatalities}</span>
              {item.date && <span className="ml-2 text-zinc-600">· {item.date}</span>}
            </div>
          )}

          {/* Scheme */}
          {item.ministry && (
            <div className="space-y-1">
              <div className="text-[9px] text-zinc-500">{item.ministry}</div>
              {item.benefit && <div className="text-[10px] text-zinc-300 line-clamp-2">{item.benefit}</div>}
            </div>
          )}

          {/* Click hint */}
          <div className="text-[8px] text-zinc-700 uppercase tracking-widest text-center pt-1 border-t border-zinc-800/60">
            Click for full details in panel →
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
