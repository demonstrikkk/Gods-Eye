import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowUpRight,
  Brain,
  CloudSun,
  Database,
  Globe2,
  Radar,
  Search,
  Signal,
} from 'lucide-react';
import { fetchCountryAnalysis, fetchGlobalCountries, fetchGlobalOverview } from '@/services/api';
import { ListSkeleton } from '@/components/Skeleton';
import { useAppStore } from '@/store';
import type { CountryAnalysis } from '@/types';

const riskColor = (risk: number) =>
  risk >= 70 ? 'text-red-300 border-red-900/50 bg-red-950/20' :
  risk >= 50 ? 'text-amber-300 border-amber-900/50 bg-amber-950/20' :
  'text-emerald-300 border-emerald-900/50 bg-emerald-950/20';

const sourceBadge = (status: string) => {
  if (status === 'live' || status === 'local') return 'border-emerald-900/50 bg-emerald-950/20 text-emerald-300';
  if (status === 'limited') return 'border-amber-900/50 bg-amber-950/20 text-amber-300';
  return 'border-zinc-800 bg-zinc-900/60 text-zinc-400';
};

const quickResearchPrompts = (analysis: CountryAnalysis) => [
  `Give me a 14-day research brief on ${analysis.country.name} using current evidence only.`,
  `What should I watch most closely in ${analysis.country.name} this week?`,
];

export const GlobalTab: React.FC = () => {
  const [search, setSearch] = useState('');
  const {
    selectedId,
    selectedType,
    setSelected,
    setHoveredItem,
    setPendingAgentQuery,
    setSidebarTab,
  } = useAppStore();

  const { data: overview } = useQuery({
    queryKey: ['global-overview'],
    queryFn: fetchGlobalOverview,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const { data: countries = [], isLoading } = useQuery({
    queryKey: ['global-countries'],
    queryFn: fetchGlobalCountries,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['country-analysis', selectedId],
    queryFn: () => fetchCountryAnalysis(selectedId as string),
    enabled: selectedType === 'country' && !!selectedId,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const filteredCountries = useMemo(() => {
    const lowered = search.trim().toLowerCase();
    return countries
      .filter((country) => {
        if (!lowered) return true;
        return [
          country.name,
          country.capital,
          country.region,
          country.macro_region,
          country.iso3,
        ]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(lowered));
      })
      .sort((left, right) => right.risk_index - left.risk_index);
  }, [countries, search]);

  if (isLoading) return <ListSkeleton count={6} />;

  return (
    <div className="flex h-full flex-col gap-3">
      <section className="rounded-2xl border border-zinc-800/80 bg-zinc-950/65 p-3">
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-xl border border-zinc-800 bg-black/20 p-2">
            <div className="text-lg font-black text-zinc-100">{overview?.total_countries ?? 0}</div>
            <div className="text-[9px] uppercase tracking-widest text-zinc-500">Countries</div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-black/20 p-2">
            <div className="text-lg font-black text-cyan-300">{overview?.live_sources ?? 0}</div>
            <div className="text-[9px] uppercase tracking-widest text-zinc-500">Live Sources</div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-black/20 p-2">
            <div className="text-lg font-black text-amber-300">{overview?.systemic_stress ?? 0}</div>
            <div className="text-[9px] uppercase tracking-widest text-zinc-500">Stress</div>
          </div>
        </div>

        <div className="mt-2 flex flex-wrap gap-2 text-[9px] font-bold uppercase tracking-widest">
          <div className="rounded-full border border-cyan-900/40 bg-cyan-950/20 px-2 py-1 text-cyan-300">
            Runtime Signals {overview?.runtime_signals ?? 0}
          </div>
          <div className="rounded-full border border-zinc-800 bg-zinc-950/60 px-2 py-1 text-zinc-300">
            Seeded Signals {overview?.seeded_signals ?? 0}
          </div>
          <div className="rounded-full border border-emerald-900/40 bg-emerald-950/20 px-2 py-1 text-emerald-300">
            Seeded Assets {overview?.seeded_assets ?? 0}
          </div>
          <div className="rounded-full border border-fuchsia-900/40 bg-fuchsia-950/20 px-2 py-1 text-fuchsia-300">
            Seeded Corridors {overview?.seeded_corridors ?? 0}
          </div>
        </div>

        <div className="relative mt-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={13} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search country, capital, region..."
            className="w-full rounded-xl border border-zinc-800 bg-black/20 py-2 pl-8 pr-3 text-xs text-zinc-100 outline-none transition-colors placeholder:text-zinc-500 focus:border-cyan-600/50"
          />
        </div>
      </section>

      <section className="rounded-2xl border border-zinc-800/80 bg-zinc-950/65 p-3">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">
            <Radar size={12} />
            <span>Selected Country Brief</span>
          </div>
          <div className="rounded-full border border-cyan-900/40 bg-cyan-950/20 px-2 py-1 text-[8px] font-bold uppercase tracking-widest text-cyan-300">
            Live Evidence Only
          </div>
        </div>

        {!analysis && !analysisLoading && (
          <div className="rounded-2xl border border-dashed border-zinc-800 bg-black/10 p-5 text-center">
            <Globe2 className="mx-auto mb-3 text-zinc-600" size={26} />
            <div className="text-sm font-semibold text-zinc-200">Search or click a country on the map.</div>
            <div className="mt-1 text-[11px] leading-relaxed text-zinc-500">
              The panel opens a research-style country brief, and the map will center on that selection.
            </div>
          </div>
        )}

        {analysisLoading && (
          <div className="text-xs text-zinc-500">Building country brief from current evidence...</div>
        )}

        {analysis && (
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-black text-zinc-100">{analysis.country.name}</div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                  {analysis.country.region} {analysis.country.capital ? `· ${analysis.country.capital}` : ''}
                </div>
              </div>
              <div className={`rounded-full border px-3 py-1 text-[10px] font-black uppercase tracking-widest ${riskColor(analysis.country.risk_index)}`}>
                Risk {analysis.country.risk_index}
              </div>
            </div>

            <div className="rounded-2xl border border-zinc-800 bg-black/20 p-3">
              <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                <Brain size={11} className="text-cyan-300" />
                <span>Researcher's Take</span>
              </div>
              <p className="text-[12px] leading-relaxed text-zinc-200">
                {analysis.research_brief || analysis.summary}
              </p>
            </div>

            {!!analysis.source_status?.length && (
              <div className="flex flex-wrap gap-2">
                {analysis.source_status.map((source) => (
                  <div
                    key={source.label}
                    className={`rounded-full border px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest ${sourceBadge(source.status)}`}
                  >
                    {source.label} · {source.count}
                  </div>
                ))}
              </div>
            )}

            {analysis.provenance && (
              <div className="flex flex-wrap gap-2">
                <div className="rounded-full border border-cyan-900/40 bg-cyan-950/20 px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest text-cyan-300">
                  Runtime Signals {analysis.provenance.runtime_signal_count ?? 0}
                </div>
                <div className="rounded-full border border-zinc-800 bg-zinc-950/60 px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest text-zinc-300">
                  Seeded Signals {analysis.provenance.seeded_signal_count ?? 0}
                </div>
                <div className="rounded-full border border-emerald-900/40 bg-emerald-950/20 px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest text-emerald-300">
                  Catalog {analysis.country.country_catalog_mode ?? 'seeded'}
                </div>
              </div>
            )}

            {!!analysis.evidence_points?.length && (
              <div className="rounded-2xl border border-zinc-800 bg-black/20 p-3">
                <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  <Signal size={11} className="text-amber-300" />
                  <span>Evidence Snapshot</span>
                </div>
                <div className="space-y-2">
                  {analysis.evidence_points.slice(0, 4).map((point) => (
                    <div key={point} className="text-[11px] leading-relaxed text-zinc-300">
                      {point}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-2xl border border-zinc-800 bg-black/20 p-3">
                <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  <CloudSun size={11} className="text-orange-300" />
                  <span>Weather</span>
                </div>
                <div className="text-[11px] text-zinc-300">
                  Temp {analysis.weather?.current?.temperature_2m ?? '--'} · Wind {analysis.weather?.current?.wind_speed_10m ?? '--'}
                </div>
              </div>

              <div className="rounded-2xl border border-zinc-800 bg-black/20 p-3">
                <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  <Database size={11} className="text-emerald-300" />
                  <span>World Bank</span>
                </div>
                <div className="text-[11px] text-zinc-300">
                  GDP {analysis.world_bank?.gdp_current_usd?.date ?? '--'} · CPI {analysis.world_bank?.inflation_consumer?.date ?? '--'}
                </div>
              </div>
            </div>

            {!!analysis.risk_factors.length && (
              <div className="rounded-2xl border border-zinc-800 bg-black/20 p-3">
                <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Key Risk Drivers
                </div>
                <div className="space-y-2">
                  {analysis.risk_factors.slice(0, 3).map((factor) => (
                    <div key={factor.factor} className="rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-[11px] font-semibold text-zinc-100">{factor.factor}</div>
                        <div className="text-[9px] uppercase tracking-widest text-amber-300">{factor.severity}</div>
                      </div>
                      <div className="mt-1 text-[10px] leading-relaxed text-zinc-400">{factor.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!!analysis.search_briefs?.results?.length && (
              <div className="rounded-2xl border border-zinc-800 bg-black/20 p-3">
                <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                  Open-Web Validation
                </div>
                <div className="space-y-2">
                  {analysis.search_briefs.results.slice(0, 3).map((item) => (
                    <a
                      key={`${item.url}-${item.source}`}
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between rounded-xl border border-zinc-800/80 bg-zinc-950/60 px-3 py-2 transition-colors hover:border-cyan-700/40 hover:bg-cyan-950/10"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-[11px] font-semibold text-zinc-100">{item.title}</div>
                        <div className="text-[9px] uppercase tracking-widest text-cyan-300">{item.source}</div>
                      </div>
                      <ArrowUpRight size={13} className="shrink-0 text-zinc-500" />
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {quickResearchPrompts(analysis).map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => {
                    setPendingAgentQuery(prompt, 'strategic');
                    setSidebarTab('ai');
                  }}
                  className="rounded-2xl border border-zinc-800 bg-black/20 px-3 py-2 text-left text-[11px] text-zinc-200 transition-all hover:border-cyan-700/40 hover:bg-cyan-950/10"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="min-h-0 flex-1 rounded-2xl border border-zinc-800/80 bg-zinc-950/65 p-3">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Country Watchlist</div>
          <div className="text-[10px] text-zinc-500">{filteredCountries.length} matches</div>
        </div>

        <div className="h-full space-y-2 overflow-y-auto pr-1">
          {filteredCountries.map((country) => (
            <button
              key={country.id}
              onClick={() => setSelected(country.id, 'country')}
              onMouseEnter={() => setHoveredItem(country)}
              onMouseLeave={() => setHoveredItem(null)}
              className={`w-full rounded-2xl border p-3 text-left transition-all hover:border-zinc-700 hover:bg-zinc-900/70 ${riskColor(country.risk_index)}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-zinc-100">{country.name}</div>
                  <div className="text-[9px] uppercase tracking-widest text-zinc-500">{country.region}</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-black">{country.risk_index}</div>
                  <div className="text-[8px] uppercase tracking-widest text-zinc-500">Risk</div>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-3 gap-2 text-[10px]">
                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">Influence</div>
                  <div className="font-bold text-blue-300">{country.influence_index}</div>
                </div>
                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">Signals</div>
                  <div className="font-bold text-cyan-300">
                    {country.runtime_signal_count ?? 0}R / {country.seeded_signal_count ?? 0}S
                  </div>
                </div>
                <div>
                  <div className="text-zinc-500 uppercase tracking-wide">Assets</div>
                  <div className="font-bold text-emerald-300">{country.asset_count ?? 0}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
};
