import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Layers, Filter, Info, ChevronRight, Map, Radar, Sparkles, Signal } from 'lucide-react';
import { useAppStore } from '@/store';
import { LayerControl } from '@/components/LayerControl';
import { fetchCountryAnalysis } from '@/services/api';
import clsx from 'clsx';

type Tab = 'layers' | 'filters' | 'context';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const ContextLayersSidebar: React.FC<Props> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<Tab>('layers');

  const {
    selectedId,
    selectedType,
    setSelected,
    setSidebarOpen,
    setSidebarTab,
    activeLayers,
  } = useAppStore();

  const { data: countryAnalysis, isLoading: loadingCountryAnalysis } = useQuery({
    queryKey: ['context-country-analysis', selectedId],
    queryFn: () => fetchCountryAnalysis(selectedId as string),
    enabled: selectedType === 'country' && !!selectedId,
    staleTime: 30_000,
  });

  const activeLayerLabels = useMemo(() => {
    const labels = Array.from(activeLayers);
    return labels.slice(0, 4);
  }, [activeLayers]);

  const clearSelection = () => {
    setSelected(null, null);
  };

  const openCountryResearch = () => {
    setSidebarTab('global');
    setSidebarOpen(true);
  };

  const openSignalResearch = () => {
    setSidebarTab('alerts');
    setSidebarOpen(true);
  };

  return (
    <div
      className={`absolute top-24 bottom-6 left-4 w-80 transition-transform duration-300 ease-in-out pointer-events-none z-20 ${
        isOpen ? 'translate-x-0' : '-translate-x-[120%]'
      }`}
    >
      <div className="h-full w-full bg-black/80 backdrop-blur-xl border border-zinc-800/80 rounded-2xl overflow-hidden flex flex-col shadow-xl pointer-events-auto">
        <div className="flex flex-col border-b border-zinc-800/60 bg-zinc-900/50">
          <div className="flex items-center justify-between p-3 border-b border-zinc-800/60">
            <div className="flex items-center gap-2 text-cyan-500">
              <Layers size={16} />
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-200">Context Layers</h2>
            </div>
            <button
              onClick={onClose}
              className="text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          <div className="flex w-full">
            <button
              onClick={() => setActiveTab('layers')}
              className={clsx(
                'flex-1 py-3 text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors',
                activeTab === 'layers' ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-500/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/30'
              )}
            >
              <Layers size={14} /> Layers
            </button>
            <button
              onClick={() => setActiveTab('filters')}
              className={clsx(
                'flex-1 py-3 text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors',
                activeTab === 'filters' ? 'text-purple-400 border-b-2 border-purple-400 bg-purple-500/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/30'
              )}
            >
              <Filter size={14} /> Filters
            </button>
            <button
              onClick={() => setActiveTab('context')}
              className={clsx(
                'flex-1 py-3 text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors',
                activeTab === 'context' ? 'text-emerald-400 border-b-2 border-emerald-400 bg-emerald-500/10' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/30'
              )}
            >
              <Info size={14} /> Context
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto overflow-x-hidden p-4">
          {activeTab === 'layers' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-zinc-400 text-xs font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                  <Map size={14} /> Active Overlays
                </h3>
                <div className="flex flex-wrap gap-2">
                  <LayerControl />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'filters' && (
            <div className="space-y-4">
              <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-3">
                <div className="text-[10px] uppercase tracking-widest text-zinc-500">Current Focus</div>
                {selectedId ? (
                  <div className="mt-2 text-sm text-zinc-100 font-semibold">
                    {selectedType?.toUpperCase()} - {selectedId}
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-zinc-500">No selected entity.</div>
                )}
              </div>

              <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-3">
                <div className="text-[10px] uppercase tracking-widest text-zinc-500 mb-2">Active Layer Snapshot</div>
                <div className="flex flex-wrap gap-2">
                  {activeLayerLabels.length ? (
                    activeLayerLabels.map((layer) => (
                      <span
                        key={layer}
                        className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-[10px] uppercase tracking-wider text-zinc-300"
                      >
                        {layer}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-zinc-500">No map layers active.</span>
                  )}
                  {activeLayers.size > 4 && (
                    <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-[10px] uppercase tracking-wider text-zinc-400">
                      +{activeLayers.size - 4} more
                    </span>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <button
                  onClick={openCountryResearch}
                  className="w-full rounded-xl border border-cyan-900/40 bg-cyan-950/20 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-cyan-300 transition-colors hover:border-cyan-700/60"
                >
                  Open Country Research
                </button>
                <button
                  onClick={openSignalResearch}
                  className="w-full rounded-xl border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-amber-300 transition-colors hover:border-amber-700/60"
                >
                  Open Signal Feed
                </button>
                <button
                  onClick={clearSelection}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-zinc-300 transition-colors hover:border-zinc-700"
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}

          {activeTab === 'context' && (
            <div className="space-y-4">
              {!selectedId && (
                <p className="text-zinc-500 text-sm italic py-4 text-center">
                  Select a country, signal, or booth to view mission context.
                </p>
              )}

              {selectedId && (
                <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-3">
                  <div className="text-[10px] uppercase tracking-widest text-zinc-500">Selected Entity</div>
                  <div className="mt-2 text-sm font-semibold text-zinc-100">{selectedId}</div>
                  <div className="mt-1 text-[10px] uppercase tracking-widest text-zinc-500">{selectedType || 'unknown'}</div>
                </div>
              )}

              {selectedType === 'country' && selectedId && (
                <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-3 space-y-2">
                  <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-emerald-300">
                    <Radar size={12} /> Country Brief
                  </div>

                  {loadingCountryAnalysis && (
                    <div className="text-xs text-zinc-400">Fetching AI country summary...</div>
                  )}

                  {countryAnalysis && (
                    <>
                      <div className="text-sm font-semibold text-zinc-100">{countryAnalysis.country.name}</div>
                      <div className="text-[11px] text-zinc-300 leading-relaxed">
                        {countryAnalysis.research_brief || countryAnalysis.summary}
                      </div>

                      {!!countryAnalysis.evidence_points?.length && (
                        <div className="rounded-lg border border-zinc-800/70 bg-zinc-950/60 p-2">
                          <div className="flex items-center gap-1 text-[9px] uppercase tracking-widest text-cyan-300 mb-1">
                            <Signal size={11} /> Evidence
                          </div>
                          <div className="text-[10px] text-zinc-300 leading-relaxed">
                            {countryAnalysis.evidence_points[0]}
                          </div>
                        </div>
                      )}

                      <button
                        onClick={openCountryResearch}
                        className="w-full rounded-lg border border-emerald-800/50 bg-emerald-950/20 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-emerald-300 transition-colors hover:border-emerald-700"
                      >
                        <span className="inline-flex items-center gap-1">
                          <Sparkles size={11} /> Open Full AI Summary
                        </span>
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};