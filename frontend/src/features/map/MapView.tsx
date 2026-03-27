import React, { Suspense, lazy, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Lock } from 'lucide-react';
import { useAppStore } from '@/store';

const GlobeEngine = lazy(() => import('./GlobeEngine').then((module) => ({ default: module.GlobeEngine })));
const FlatMapEngine = lazy(() => import('./FlatMapEngine').then((module) => ({ default: module.FlatMapEngine })));

export const MapView: React.FC = () => {
  const mapMode = useAppStore((state) => state.mapMode);
  const liteMode = useAppStore((state) => state.liteMode);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ width: 0, height: 0 });
  const effectiveMode = liteMode ? 'flat' : mapMode;

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
        {effectiveMode === 'globe' ? (
          <motion.div
            key="globe"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <Suspense fallback={<div className="h-full w-full animate-pulse bg-[#060606]" />}>
              {dims.width > 0 && <GlobeEngine width={dims.width} height={dims.height} />}
            </Suspense>
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
            <Suspense fallback={<div className="h-full w-full animate-pulse bg-[#060606]" />}>
              <FlatMapEngine />
            </Suspense>
          </motion.div>
        )}
      </AnimatePresence>

      {liteMode && (
        <div className="pointer-events-none absolute left-4 top-4 z-[1200] rounded-md border border-emerald-500/35 bg-black/70 px-3 py-1.5 text-[10px] uppercase tracking-[0.2em] text-emerald-300 backdrop-blur-sm">
          <span className="inline-flex items-center gap-1.5">
            <Lock size={10} />
            Lite Mode Active
          </span>
        </div>
      )}
    </div>
  );
};

