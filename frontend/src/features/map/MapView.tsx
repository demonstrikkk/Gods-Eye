// ─────────────────────────────────────────────────────────────────────────────
// MapView — Dual-map orchestrator (Globe ↔ Flat) with layer controls
// ─────────────────────────────────────────────────────────────────────────────

import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Map } from 'lucide-react';
import { useAppStore } from '@/store';
import { GlobeEngine } from './GlobeEngine';
import { FlatMapEngine } from './FlatMapEngine';
import { LayerControl } from '@/components/LayerControl';
import clsx from 'clsx';

export const MapView: React.FC = () => {
  const { mapMode, setMapMode } = useAppStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const obs = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setDims({ width: Math.floor(width), height: Math.floor(height) });
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden bg-[#050505]">

      {/* Map content */}
      <AnimatePresence mode="wait">
        {mapMode === 'globe' ? (
          <motion.div
            key="globe"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            {dims.width > 0 && (
              <GlobeEngine width={dims.width} height={dims.height} />
            )}
          </motion.div>
        ) : (
          <motion.div
            key="flat"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0"
          >
            <FlatMapEngine />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overlay controls — top-left */}
      <div className="absolute top-3 left-3 z-[401] flex flex-col space-y-2">
        {/* Mode toggle */}
        <div className="flex items-center bg-black/70 border border-zinc-800 rounded-xl overflow-hidden backdrop-blur-md text-[10px] font-bold uppercase">
          <button
            onClick={() => setMapMode('globe')}
            className={clsx(
              'flex items-center space-x-1.5 px-3 py-2 transition-all',
              mapMode === 'globe'
                ? 'bg-blue-600/80 text-white'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40'
            )}
          >
            <Globe size={12} />
            <span>Globe</span>
          </button>
          <div className="w-px h-5 bg-zinc-800" />
          <button
            onClick={() => setMapMode('flat')}
            className={clsx(
              'flex items-center space-x-1.5 px-3 py-2 transition-all',
              mapMode === 'flat'
                ? 'bg-blue-600/80 text-white'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40'
            )}
          >
            <Map size={12} />
            <span>Flat</span>
          </button>
        </div>

        {/* Layer toggles */}
        <LayerControl />
      </div>

    </div>
  );
};
