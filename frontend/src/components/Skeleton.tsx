// ─────────────────────────────────────────────────────────────────────────────
// Skeleton — generic loading skeleton for structured data panels
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
  rows?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, rows = 1 }) => (
  <div className="space-y-2">
    {Array.from({ length: rows }).map((_, i) => (
      <div
        key={i}
        className={clsx(
          'animate-pulse rounded-md bg-zinc-800/70',
          className ?? 'h-4 w-full'
        )}
      />
    ))}
  </div>
);

export const CardSkeleton: React.FC = () => (
  <div className="glass-panel p-4 space-y-3">
    <Skeleton className="h-3 w-2/5" />
    <Skeleton className="h-6 w-3/4" />
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-4/5" />
  </div>
);

export const ListSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="space-y-2">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="flex items-center space-x-3 p-3 rounded-lg bg-zinc-900/60">
        <div className="w-8 h-8 rounded-full bg-zinc-800 animate-pulse flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-2/3" />
          <Skeleton className="h-2 w-1/2" />
        </div>
        <Skeleton className="h-5 w-12 rounded-full" />
      </div>
    ))}
  </div>
);
