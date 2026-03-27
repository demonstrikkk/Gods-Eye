import React, { useState, useEffect } from 'react';
import { Globe, AlertTriangle, Clock, Map, Zap, Shield } from 'lucide-react';
import { useAppStore } from '@/store';
import { CountrySearchCommand } from '@/features/map/CountrySearchCommand';

// Simulated Ticker Items 
const alerts = [
  { id: 1, text: "NSA issues warning on state-sponsored cyber operations targeting critical infrastructure.", severity: 'high' },
  { id: 2, text: "Joint naval exercises commence in contested waters, escalating regional tensions.", severity: 'medium' },
  { id: 3, text: "Global supply chain disruption imminent due to semiconductor shortage.", severity: 'high' },
];

export const UnifiedTopHUD: React.FC = () => {
  const {
    sidebarTab,
    setActiveView,
    setSidebarTab,
    setSidebarOpen,
    mapMode,
    setMapMode,
    liteMode,
    setLiteMode,
  } = useAppStore();
  const [tickerIndex, setTickerIndex] = useState(0);

  const mode =
    sidebarTab === 'battleground'
      ? 'simulation'
      : sidebarTab === 'unified'
        ? 'analysis'
        : 'observation';

  const handleModeSwitch = (targetMode: 'observation' | 'analysis' | 'simulation') => {
    setSidebarOpen(true);

    if (targetMode === 'observation') {
      setActiveView('cockpit');
      setSidebarTab('global');
      return;
    }

    if (targetMode === 'analysis') {
      setActiveView('cockpit');
      setSidebarTab('unified');
      return;
    }

    setActiveView('cockpit');
    setSidebarTab('battleground');
  };

  // Auto-rotate ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % alerts.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const currentAlert = alerts[tickerIndex];

  return (
    <header className="w-full border-b border-zinc-500/20 bg-black/65 px-2 py-1.5 text-xs font-medium text-zinc-300 backdrop-blur-xl lg:px-3">
      <div className="flex h-11 w-full items-center gap-2">
        <div className="flex shrink-0 items-center gap-1.5 pr-2">
          <Globe className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-bold tracking-wide text-emerald-50">GoDs-<span className="text-blue-500 opacity-85">EyE</span></span>
        </div>

        <div className="min-w-0 flex-1 overflow-x-auto">
          <div className="inline-flex min-w-max items-center gap-1">
            <div className="inline-flex items-center gap-1 rounded-md border border-white/10 bg-zinc-900/55 p-0.5">
              <button
                onClick={() => handleModeSwitch('observation')}
                className={`rounded px-2 py-1 leading-none transition-all ${
                  mode === 'observation' ? 'bg-blue-600/20 text-blue-300' : 'text-zinc-300 hover:bg-zinc-800'
                }`}
              >
                OBS
              </button>
              <button
                onClick={() => handleModeSwitch('analysis')}
                className={`rounded px-2 py-1 leading-none transition-all ${
                  mode === 'analysis' ? 'bg-cyan-600/20 text-cyan-300' : 'text-zinc-300 hover:bg-zinc-800'
                }`}
              >
                AI
              </button>
              <button
                onClick={() => handleModeSwitch('simulation')}
                className={`rounded px-2 py-1 leading-none transition-all ${
                  mode === 'simulation' ? 'bg-amber-600/20 text-amber-300' : 'text-zinc-300 hover:bg-zinc-800'
                }`}
              >
                SIM
              </button>
            </div>

            <div className="hidden md:inline-flex items-center gap-1 rounded-md border border-white/10 bg-zinc-900/55 p-0.5">
              <button
                onClick={() => setMapMode('flat')}
                className={`flex items-center gap-1 rounded px-2 py-1 leading-none transition-all ${
                  mapMode === 'flat' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white'
                }`}
                title="2D Map View"
              >
                <Map className="h-3 w-3" />
                <span>2D</span>
              </button>
              <button
                onClick={() => setMapMode('globe')}
                className={`flex items-center gap-1 rounded px-2 py-1 leading-none transition-all ${
                  mapMode === 'globe' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white'
                }`}
                title="3D Globe View"
                disabled={liteMode}
              >
                <Globe className="h-3 w-3" />
                <span>3D</span>
              </button>
            </div>

          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          <div className="hidden xl:flex w-[300px] 2xl:w-[380px] items-center rounded-md border border-red-500/20 bg-red-500/5 px-2 py-1 text-[11px] text-red-100">
            <AlertTriangle className="mr-1.5 h-3 w-3 shrink-0 text-red-400" />
            <span className="mr-1 shrink-0 font-semibold text-red-300">ALERT:</span>
            <span className="truncate" title={currentAlert?.text}>{currentAlert?.text}</span>
          </div>

          <div className="hidden lg:block w-[240px]">
            <CountrySearchCommand />
          </div>

          <button
            onClick={() => setLiteMode(!liteMode)}
            className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 leading-none transition-all ${
              liteMode
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                : 'border-white/10 bg-zinc-900/40 text-zinc-300 hover:bg-zinc-800'
            }`}
            title="Toggle lite mode (Alt+L)"
          >
            <Shield className="h-3 w-3" />
            <span className="hidden sm:inline">Lite</span>
          </button>

          <div className="hidden 2xl:flex items-center gap-1 text-[11px] text-zinc-500">
            <div className="h-2 w-2 animate-pulse-slow rounded-full bg-emerald-500"></div>
            <Clock className="h-3 w-3" />
            <span className="font-mono">LIVE</span>
            <Zap className="h-3 w-3" />
          </div>
        </div>
      </div>
    </header>
  );
};
