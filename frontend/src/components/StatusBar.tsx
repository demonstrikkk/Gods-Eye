// ─────────────────────────────────────────────────────────────────────────────
// StatusBar — top strip showing live status, node info, time.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState, useEffect } from 'react';
import { RadioTower, Shield, Clock, Wifi } from 'lucide-react';

export const StatusBar: React.FC = () => {
  const [time, setTime] = useState(() => new Date().toISOString());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toISOString()), 1000);
    return () => clearInterval(id);
  }, []);

  const ts = new Date(time);
  const hh = ts.getHours().toString().padStart(2, '0');
  const mm = ts.getMinutes().toString().padStart(2, '0');
  const ss = ts.getSeconds().toString().padStart(2, '0');

  return (
    <div className="h-7 w-full bg-[#050507] border-b border-zinc-800/80 flex items-center justify-between px-4 text-[10px] font-mono shrink-0 z-50">
      {/* Left: node identity */}
      <div className="flex items-center space-x-4 text-zinc-500">
        <span className="flex items-center space-x-1.5">
          <Shield size={10} className="text-blue-500" />
          <span className="text-blue-400 font-bold tracking-widest uppercase">JANGRAPH OS</span>
          <span className="text-zinc-600">·</span>
          <span>SOVEREIGN NODE v2.1</span>
        </span>
        <span className="text-zinc-700">|</span>
        <span className="flex items-center space-x-1.5">
          <Wifi size={10} className="text-emerald-500" />
          <span className="text-emerald-400">LIVE</span>
        </span>
      </div>

      {/* Center: scrolling intel ticker */}
      <div className="hidden lg:flex items-center space-x-1 text-zinc-600">
        <RadioTower size={9} className="text-blue-500 animate-pulse" />
        <span>INTEL STREAM ACTIVE · ALL SOURCES NOMINAL</span>
      </div>

      {/* Right: clock */}
      <div className="flex items-center space-x-1.5 text-zinc-500">
        <Clock size={10} />
        <span className="tabular-nums">{hh}:{mm}:{ss}</span>
        <span className="text-zinc-700">IST</span>
        <span className="text-zinc-700">|</span>
        <span className="text-blue-400 uppercase tracking-widest">AUTH: ALPHA-SEC</span>
      </div>
    </div>
  );
};
