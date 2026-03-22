import React, { useDeferredValue, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LocateFixed, Search } from 'lucide-react';
import { fetchGlobalCountries } from '@/services/api';
import { useAppStore } from '@/store';

export const CountrySearchCommand: React.FC = () => {
  const [query, setQuery] = useState('');
  const [feedback, setFeedback] = useState('');
  const deferredQuery = useDeferredValue(query.trim());
  const { setSelected, setSidebarOpen, setSidebarTab } = useAppStore();

  const { data: countries = [] } = useQuery({
    queryKey: ['global-countries'],
    queryFn: fetchGlobalCountries,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const bestMatch = useMemo(() => {
    if (!deferredQuery) return null;
    const lowered = deferredQuery.toLowerCase();

    const exact = countries.find((country) =>
      [country.name, country.capital, country.iso3]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase() === lowered),
    );
    if (exact) return exact;

    return countries.find((country) =>
      [country.name, country.capital, country.region, country.macro_region, country.iso3]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(lowered)),
    ) ?? null;
  }, [countries, deferredQuery]);

  const runSearch = () => {
    if (!deferredQuery) {
      setFeedback('');
      return;
    }

    if (!bestMatch) {
      setFeedback('No country match');
      return;
    }

    setSelected(bestMatch.id, 'country');
    setSidebarTab('global');
    setSidebarOpen(true);
    setQuery(bestMatch.name);
    setFeedback(`Selected ${bestMatch.name}`);
  };

  return (
    <div className="flex min-w-0 items-center gap-2">
      <div className="relative min-w-0 flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={13} />
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            if (feedback) setFeedback('');
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              runSearch();
            }
          }}
          placeholder="Search any country..."
          className="w-full min-w-0 rounded-xl border border-zinc-800 bg-zinc-950/90 py-2 pl-8 pr-3 text-[11px] text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-cyan-500/50"
        />
      </div>

      <button
        onClick={runSearch}
        className="flex shrink-0 items-center gap-1 rounded-xl border border-cyan-800/40 bg-cyan-950/20 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-600/60 hover:bg-cyan-950/35"
      >
        <LocateFixed size={12} />
        <span>Go</span>
      </button>

      <div className="hidden min-w-[110px] text-right text-[10px] uppercase tracking-widest text-zinc-500 xl:block">
        {feedback || 'Country search'}
      </div>
    </div>
  );
};
