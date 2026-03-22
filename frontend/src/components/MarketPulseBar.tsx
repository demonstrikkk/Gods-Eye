import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { fetchMarketSnapshot } from '@/services/api';
import { CandlestickChart } from 'lucide-react';

export const MarketPulseBar: React.FC = () => {
  const { data: quotes = [] } = useQuery({
    queryKey: ['market-snapshot'],
    queryFn: fetchMarketSnapshot,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  if (!quotes.length) return null;

  return (
    <div className="relative flex h-8 w-full items-center overflow-hidden border-b border-zinc-800/70 bg-[#08080b]">
      <div className="z-10 flex h-full flex-shrink-0 items-center border-r border-zinc-800/70 bg-zinc-950 px-3 text-[9px] font-black uppercase tracking-widest text-cyan-300">
        <CandlestickChart size={12} className="mr-1.5" />
        Market Pulse
      </div>

      <div className="relative flex-1 overflow-hidden">
        <motion.div
          className="flex items-center whitespace-nowrap"
          animate={{ x: [0, -1400] }}
          transition={{ x: { repeat: Infinity, repeatType: 'loop', duration: 28, ease: 'linear' } }}
        >
          {[...quotes, ...quotes, ...quotes].map((quote: any, index: number) => (
            <div key={`${quote.symbol}-${index}`} className="mx-5 flex items-center gap-2 text-[11px]">
              <span className="font-bold text-zinc-100">{quote.symbol}</span>
              <span className="text-zinc-400">{quote.price}</span>
              <span className={quote.change_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                {quote.change_pct >= 0 ? '+' : ''}{quote.change_pct}%
              </span>
              <span className="text-[9px] uppercase tracking-widest text-zinc-600">{quote.name}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
};
