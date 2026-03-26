import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Globe, Map } from 'lucide-react';
import clsx from 'clsx';
import { useAppStore } from '@/store';
import { GlobeEngine } from './GlobeEngine';
import { FlatMapEngine } from './FlatMapEngine';

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
    </div>
  );
};

