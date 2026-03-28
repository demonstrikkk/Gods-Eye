import React, { useState, useEffect } from 'react';
import { Globe, AlertTriangle, Clock, Map, Layers, Zap, Shield } from 'lucide-react';
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
    activeView,
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
    <div className="flex h-16 w-full items-center justify-between border-b border-zinc-500/20 bg-black/60 px-3 lg:px-4 text-xs font-medium text-zinc-300 backdrop-blur-xl">
      
      {/* LEFT: Branding & Mode Switcher */}
      <div className="flex items-center space-x-3 lg:space-x-5 min-w-0">
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-blue-500" />
          <span className="text-sm font-bold tracking-wider text-emerald-50">GoDs-<span className="text-blue-500 opacity-80">EyE</span></span>
        </div>

        <div className="hidden sm:block h-5 w-px bg-zinc-700"></div>

        {/* View Switcher (formerly ViewNav) */}
        <div className="flex space-x-1 rounded-lg bg-zinc-900/50 p-1 border border-white/5">
          <button
            onClick={() => handleModeSwitch('observation')}
            className={`rounded px-3 py-1.5 transition-all ${
              mode === 'observation' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'hover:bg-zinc-800'
            }`}
          >
            Observation Mode
          </button>
          <button
            onClick={() => handleModeSwitch('analysis')}
            className={`rounded px-3 py-1.5 transition-all ${
              mode === 'analysis' ? 'bg-cyan-600/20 text-cyan-400 border border-cyan-500/30' : 'hover:bg-zinc-800'
            }`}
          >
            Unified AI Mode
          </button>
          <button
             onClick={() => handleModeSwitch('simulation')}
             className={`rounded px-3 py-1.5 transition-all ${
               mode === 'simulation' ? 'bg-amber-600/20 text-amber-400 border border-amber-500/30' : 'hover:bg-zinc-800'
             }`}
          >
            Simulation Mode
          </button>
        </div>

        {/* Map Toggle (2D/3D) */}
        <div className="flex space-x-1 rounded-lg bg-zinc-900/50 p-1 border border-white/5">
          <button
            onClick={() => setMapMode('flat')}
            className={`flex items-center gap-1 rounded px-3 py-1.5 transition-all ${
              mapMode === 'flat' ? 'bg-zinc-800 text-white border border-white/10' : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
            }`}
            title="2D Map View"
          >
            <Map className="w-3.5 h-3.5" />
            <span>2D</span>
          </button>
          <button
            onClick={() => setMapMode('globe')}
            className={`flex items-center gap-1 rounded px-3 py-1.5 transition-all ${
              mapMode === 'globe' ? 'bg-zinc-800 text-white border border-white/10' : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
            }`}
            title="3D Globe View"
            disabled={liteMode}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>3D</span>
          </button>
        </div>

        <button
          onClick={() => setLiteMode(!liteMode)}
          className={`hidden md:inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 transition-all ${
            liteMode
              ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
              : 'border-white/10 bg-zinc-900/40 text-zinc-300 hover:bg-zinc-800'
          }`}
          title="Toggle lite mode (Alt+L)"
        >
          <Shield className="h-3.5 w-3.5" />
          <span>{liteMode ? 'Lite ON' : 'Lite OFF'}</span>
        </button>
      <div className="flex flex-1 items-center justify-center px-3 lg:px-6 min-w-0 overflow-hidden">
        <div className="flex w-full max-w-none items-center rounded-lg border border-red-500/20 bg-red-500/5 px-3 lg:px-4 py-2 overflow-hidden">
           <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mr-3 animate-pulse" />
           <div className="min-w-0 flex-1 text-red-200 leading-tight">
             <span className="font-bold mr-2 whitespace-nowrap">PRIORITY ALERT:</span>
             <span
               className="inline-block align-top max-w-full overflow-x-auto whitespace-nowrap"
               title={currentAlert?.text}
             >
               {currentAlert?.text}
             </span>
           </div>
        </div>
      </div>
      </div>

      {/* CENTER: Smart Ticker (formerly LiveFeedTicker + Alert popups) */}

      {/* RIGHT: System Status / Profile (formerly StatusBar / KPIBar) */}
      <div className="flex items-center space-x-3 lg:space-x-5 shrink-0">
        
        {/* Country Search */}
        <div className="flex items-center">
          <CountrySearchCommand />
        </div>

        {/* Quick Stats */}
        <div className="hidden xl:flex items-center space-x-4 pr-4 border-r border-zinc-700">
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-zinc-500">Global Threat Level</span>
            <span className="text-amber-400 font-mono">ELEVATED (7.2)</span>
          </div>
        </div>

        {/* System Health */}
        <div className="flex items-center space-x-3 text-[10px] text-zinc-400">
           <div className="flex items-center gap-1.5">
             <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse-slow"></div>
             <span>SYS: NML</span>
           </div>
           <div className="flex items-center gap-1.5">
             <Clock className="h-3.5 w-3.5 text-zinc-500" />
             <span className="font-mono">LIVE SYNC</span>
           </div>
           <div className="hidden lg:flex items-center gap-1.5 text-zinc-500">
             <Zap className="h-3.5 w-3.5" />
             <span>Alt+L Lite • Alt+M Map • Alt+I Panel</span>
           </div>
        </div>

      </div>

    </div>
  );
};
