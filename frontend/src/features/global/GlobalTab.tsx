import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchCountryAnalysis, fetchGlobalCountries, fetchGlobalOverview, fetchGlobalSignals } from '@/services/api';
import { useAppStore } from '@/store';
import { ListSkeleton } from '@/components/Skeleton';
import { Search, Signal, Brain, Radar, CloudSun, Database } from 'lucide-react';

const riskColor = (risk: number) =>
  risk >= 70 ? 'text-red-400 border-red-900/50 bg-red-950/20' :
  risk >= 50 ? 'text-amber-400 border-amber-900/50 bg-amber-950/20' :
  'text-emerald-400 border-emerald-900/50 bg-emerald-950/20';

export const GlobalTab: React.FC = () => {
  const [search, setSearch] = useState('');
  const { selectedId, selectedType, setSelected, setHoveredItem, setPendingAgentQuery, setSidebarTab } = useAppStore();

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

  const { data: signals = [] } = useQuery({
    queryKey: ['global-signals'],
    queryFn: fetchGlobalSignals,
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

  const filteredCountries = useMemo(
    () => countries
      .filter((country: any) =>
        !search ||
        country.name.toLowerCase().includes(search.toLowerCase()) ||
        country.region.toLowerCase().includes(search.toLowerCase()),
      )
      .sort((a: any, b: any) => b.risk_index - a.risk_index),
    [countries, search],
  );

  if (isLoading) return <ListSkeleton count={6} />;

  return (
    <div className="flex h-full flex-col">
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-2">
          <div className="text-lg font-black text-zinc-100">{overview?.total_countries ?? 0}</div>
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">Countries</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-2">
          <div className="text-lg font-black text-cyan-400">{overview?.total_signals ?? 0}</div>
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">Signals</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-2">
          <div className="text-lg font-black text-emerald-400">{overview?.total_assets ?? 0}</div>
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">Assets</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-2">
          <div className="text-lg font-black text-red-400">{overview?.critical_zones ?? 0}</div>
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">Critical</div>
        </div>
      </div>

      <div className="relative mb-3">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={13} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search country or region..."
          className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-3 py-2 text-xs text-zinc-300 focus:outline-none focus:border-blue-600 transition-colors"
        />
      </div>

      {selectedType === 'country' && (
        <div className="mb-3 rounded-xl border border-zinc-800 bg-zinc-900/70 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center text-[10px] uppercase tracking-widest text-cyan-400">
              <Radar size={11} className="mr-1.5" />
              Country Analysis
            </div>
            {analysis?.ai_prompt && (
              <button
                onClick={() => {
                  setPendingAgentQuery(analysis.ai_prompt, 'strategic');
                  setSidebarTab('ai');
                }}
                className="rounded-lg border border-blue-800/60 bg-blue-950/20 px-2 py-1 text-[9px] font-bold uppercase tracking-widest text-blue-400"
              >
                Send To AI
              </button>
            )}
          </div>

          {analysisLoading && <div className="text-xs text-zinc-500">Synthesizing country brief...</div>}

          {analysis && (
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-black text-zinc-100">{analysis.country.name}</div>
                    <div className="text-[9px] uppercase tracking-widest text-zinc-500">{analysis.country.region}</div>
                  </div>
                  <div className={`rounded-full border px-2 py-1 text-[9px] font-black uppercase tracking-widest ${riskColor(analysis.country.risk_index)}`}>
                    Risk {analysis.country.risk_index}
                  </div>
                </div>
                <div className="mt-2 text-[11px] leading-relaxed text-zinc-300">{analysis.summary}</div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-lg border border-zinc-800 bg-black/20 p-2">
                  <div className="text-[8px] uppercase tracking-widest text-zinc-500">Signals</div>
                  <div className="text-sm font-black text-cyan-400">{analysis.country.active_signals}</div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-black/20 p-2">
                  <div className="text-[8px] uppercase tracking-widest text-zinc-500">Assets</div>
                  <div className="text-sm font-black text-emerald-400">{analysis.country.asset_count ?? 0}</div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-black/20 p-2">
                  <div className="text-[8px] uppercase tracking-widest text-zinc-500">Influence</div>
                  <div className="text-sm font-black text-amber-400">{analysis.country.influence_index}</div>
                </div>
              </div>

              {!!analysis.risk_factors.length && (
                <div>
                  <div className="mb-1.5 flex items-center text-[9px] uppercase tracking-widest text-zinc-500">
                    <Signal size={11} className="mr-1.5 text-red-400" />
                    Risk Drivers
                  </div>
                  <div className="space-y-1.5">
                    {analysis.risk_factors.slice(0, 3).map((factor: any) => (
                      <div key={factor.factor} className="rounded-lg border border-zinc-800 bg-black/20 px-2.5 py-2">
                        <div className="flex items-center justify-between">
                          <div className="text-[10px] font-bold text-zinc-100">{factor.factor}</div>
                          <div className="text-[8px] uppercase tracking-widest text-red-400">{factor.severity}</div>
                        </div>
                        <div className="mt-1 text-[10px] text-zinc-400">{factor.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-zinc-800 bg-black/20 p-2">
                  <div className="mb-1 flex items-center text-[9px] uppercase tracking-widest text-zinc-500">
                    <CloudSun size={11} className="mr-1.5 text-orange-400" />
                    Weather
                  </div>
                  <div className="text-[10px] text-zinc-300">
                    Temp {analysis.weather?.current?.temperature_2m ?? '--'} | Wind {analysis.weather?.current?.wind_speed_10m ?? '--'}
                  </div>
                </div>
                <div className="rounded-lg border border-zinc-800 bg-black/20 p-2">
                  <div className="mb-1 flex items-center text-[9px] uppercase tracking-widest text-zinc-500">
                    <Database size={11} className="mr-1.5 text-emerald-400" />
                    Open Data
                  </div>
                  <div className="text-[10px] text-zinc-300">
                    GDP year {analysis.world_bank?.gdp_current_usd?.date ?? '--'} | CPI year {analysis.world_bank?.inflation_consumer?.date ?? '--'}
                  </div>
                </div>
              </div>

              {!!analysis.signals.length && (
                <div>
                  <div className="mb-1.5 text-[9px] uppercase tracking-widest text-zinc-500">Live Signals</div>
                  <div className="space-y-1.5">
                    {analysis.signals.slice(0, 3).map((signal: any) => (
                      <div key={signal.id} className="rounded-lg border border-zinc-800 bg-black/20 px-2.5 py-2">
                        <div className="text-[10px] font-bold text-zinc-100">{signal.title}</div>
                        <div className="mt-1 text-[10px] text-zinc-400">{signal.summary}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!!analysis.assets.length && (
                <div>
                  <div className="mb-1.5 text-[9px] uppercase tracking-widest text-zinc-500">Strategic Assets</div>
                  <div className="space-y-1.5">
                    {analysis.assets.slice(0, 3).map((asset: any) => (
                      <div key={asset.id} className="rounded-lg border border-zinc-800 bg-black/20 px-2.5 py-2">
                        <div className="text-[10px] font-bold text-zinc-100">{asset.title}</div>
                        <div className="mt-1 text-[10px] text-zinc-400">{asset.kind} | {asset.status}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!!analysis.feeds.length && (
                <div>
                  <div className="mb-1.5 text-[9px] uppercase tracking-widest text-zinc-500">Mentioned In Feeds</div>
                  <div className="space-y-1.5">
                    {analysis.feeds.slice(0, 2).map((feed: any) => (
                      <div key={feed.id} className="rounded-lg border border-zinc-800 bg-black/20 px-2.5 py-2 text-[10px] text-zinc-300">
                        {feed.text}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!!analysis.suggested_questions.length && (
                <div>
                  <div className="mb-1.5 flex items-center text-[9px] uppercase tracking-widest text-zinc-500">
                    <Brain size={11} className="mr-1.5 text-blue-400" />
                    Suggested Questions
                  </div>
                  <div className="space-y-1.5">
                    {analysis.suggested_questions.map((question: string) => (
                      <button
                        key={question}
                        onClick={() => {
                          setPendingAgentQuery(question, 'strategic');
                          setSidebarTab('ai');
                        }}
                        className="w-full rounded-lg border border-zinc-800 bg-black/20 px-2.5 py-2 text-left text-[10px] text-zinc-300 hover:border-blue-800/60 hover:bg-blue-950/10"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="mb-2 rounded-xl border border-zinc-800 bg-zinc-900/60 p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center text-[10px] uppercase tracking-widest text-zinc-500">
            <Signal size={11} className="mr-1.5 text-cyan-400" />
            Global Pressure
          </div>
          <div className="text-xs font-black text-zinc-100">{overview?.systemic_stress ?? '--'}</div>
        </div>
        <div className="text-[10px] text-zinc-400 leading-relaxed">
          {signals.slice(0, 3).map((signal: any) => signal.title).join(' | ') || 'Awaiting signal synthesis'}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1.5 pr-0.5">
        {filteredCountries.map((country: any) => (
          <button
            key={country.id}
            onClick={() => setSelected(country.id, 'country')}
            onMouseEnter={() => setHoveredItem(country)}
            onMouseLeave={() => setHoveredItem(null)}
            className={`w-full text-left rounded-xl border p-3 transition-all hover:border-zinc-700 hover:bg-zinc-900/70 ${riskColor(country.risk_index)}`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="min-w-0 pr-2">
                <div className="text-xs font-bold text-zinc-100 truncate">{country.name}</div>
                <div className="text-[9px] uppercase tracking-widest text-zinc-500 mt-0.5">{country.region}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-black">{country.risk_index}</div>
                <div className="text-[8px] uppercase tracking-widest text-zinc-500">Risk</div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 text-[10px]">
              <div>
                <div className="text-zinc-500 uppercase tracking-wide">Influence</div>
                <div className="font-bold text-blue-300">{country.influence_index}</div>
              </div>
              <div>
                <div className="text-zinc-500 uppercase tracking-wide">Signals</div>
                <div className="font-bold text-cyan-300">{country.active_signals}</div>
              </div>
              <div>
                <div className="text-zinc-500 uppercase tracking-wide">Assets</div>
                <div className="font-bold text-emerald-300">{country.asset_count ?? 0}</div>
              </div>
              <div>
                <div className="text-zinc-500 uppercase tracking-wide">Status</div>
                <div className="font-bold text-zinc-100">{country.stability}</div>
              </div>
            </div>

            <div className="mt-2 flex flex-wrap gap-1">
              {country.top_domains?.slice(0, 3).map((domain: string) => (
                <span key={domain} className="rounded-full border border-zinc-800 bg-black/30 px-2 py-0.5 text-[8px] uppercase tracking-wider text-zinc-400">
                  {domain}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
