import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Globe, Map } from 'lucide-react';
import clsx from 'clsx';
import { useAppStore } from '@/store';
import { GlobeEngine } from './GlobeEngine';
import { FlatMapEngine } from './FlatMapEngine';
import { LayerControl } from '@/components/LayerControl';

export const MapView: React.FC = () => {
  const { mapMode, setMapMode } = useAppStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setDims({ width: Math.floor(width), height: Math.floor(height) });
    });

    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden bg-[#050505]">
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
            {dims.width > 0 && <GlobeEngine width={dims.width} height={dims.height} />}
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

      <div className="pointer-events-none absolute top-3 left-3 z-[401] flex flex-col space-y-2">
        <div className="pointer-events-auto flex items-center overflow-hidden rounded-xl border border-zinc-800 bg-black/70 text-[10px] font-bold uppercase backdrop-blur-md">
          <button
            onClick={() => setMapMode('globe')}
            className={clsx(
              'flex items-center space-x-1.5 px-3 py-2 transition-all',
              mapMode === 'globe'
                ? 'bg-blue-600/80 text-white'
                : 'text-zinc-500 hover:bg-zinc-800/40 hover:text-zinc-300',
            )}
          >
            <Globe size={12} />
            <span>Globe</span>
          </button>
          <div className="h-5 w-px bg-zinc-800" />
          <button
            onClick={() => setMapMode('flat')}
            className={clsx(
              'flex items-center space-x-1.5 px-3 py-2 transition-all',
              mapMode === 'flat'
                ? 'bg-blue-600/80 text-white'
                : 'text-zinc-500 hover:bg-zinc-800/40 hover:text-zinc-300',
            )}
          >
            <Map size={12} />
            <span>Flat</span>
          </button>
        </div>

        <div className="pointer-events-auto">
          <LayerControl />
        </div>
      </div>
    </div>
  );
};
