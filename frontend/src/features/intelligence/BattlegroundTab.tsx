// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — Virtual Battleground Tab
// Strategic simulation and military comparison interface
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Swords,
  Shield,
  Target,
  Users,
  Plane,
  Anchor,
  Loader2,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Scale,
  Zap,
  Globe,
  Clock,
  DollarSign,
  ChevronDown,
  ChevronUp,
  Network,
} from 'lucide-react';
import { useAppStore } from '@/store';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface MilitaryStrength {
  country_id: string;
  name: string;
  power_index: number;
  rank?: number;
  active_personnel: number;
  reserve_personnel: number;
  aircraft: number;
  tanks: number;
  naval_vessels: number;
  nuclear_warheads: number;
  defense_budget_usd: number;
  tech_level: number;
  projection_capability: number;
  nuclear_power: boolean;
  nato_member: boolean;
}

interface ForceComparison {
  country_a: {
    id: string;
    name: string;
    power_index: number;
    total_personnel: number;
    aircraft: number;
    tanks: number;
    naval_vessels: number;
    nuclear_capable: boolean;
    tech_level: number;
    allies?: Array<{ id: string; alliance: string; strength: number }>;
  };
  country_b: {
    id: string;
    name: string;
    power_index: number;
    total_personnel: number;
    aircraft: number;
    tanks: number;
    naval_vessels: number;
    nuclear_capable: boolean;
    tech_level: number;
    allies?: Array<{ id: string; alliance: string; strength: number }>;
  };
  analysis: {
    power_ratio: number;
    advantage: string;
    advantage_level: string;
    air_superiority: string;
    naval_superiority: string;
    tech_advantage: string;
    nuclear_parity: boolean;
  };
  alliance_analysis?: {
    alliance_count_a: number;
    alliance_count_b: number;
    combined_strength_a: number;
    combined_strength_b: number;
    alliance_advantage: string;
  };
}

interface ConflictSimulation {
  scenario: {
    type: string;
    duration_days: number;
    actors: string[];
  };
  force_comparison: ForceComparison;
  outcome_probabilities: Record<string, number>;
  timeline: Array<{
    day: number;
    phase: string;
    event: string;
    description: string;
    impact: string;
  }>;
  impacts: {
    economic_impact_usd: number;
    estimated_military_casualties: { low: number; high: number };
    estimated_civilian_casualties: { low: number; high: number };
    displaced_persons_estimate: number;
    global_trade_disruption_pct: number;
    energy_price_impact_pct: number;
  };
  warnings: string[];
  map_visualization: Array<{
    type: string;
    name: string;
    data: unknown;
    color: string;
  }>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Country Selector
// ─────────────────────────────────────────────────────────────────────────────

const COUNTRIES = [
  { id: 'CTR-USA', name: 'United States', flag: '🇺🇸' },
  { id: 'CTR-RUS', name: 'Russia', flag: '🇷🇺' },
  { id: 'CTR-CHN', name: 'China', flag: '🇨🇳' },
  { id: 'CTR-IND', name: 'India', flag: '🇮🇳' },
  { id: 'CTR-GBR', name: 'United Kingdom', flag: '🇬🇧' },
  { id: 'CTR-FRA', name: 'France', flag: '🇫🇷' },
  { id: 'CTR-DEU', name: 'Germany', flag: '🇩🇪' },
  { id: 'CTR-JPN', name: 'Japan', flag: '🇯🇵' },
  { id: 'CTR-PAK', name: 'Pakistan', flag: '🇵🇰' },
  { id: 'CTR-IRN', name: 'Iran', flag: '🇮🇷' },
  { id: 'CTR-ISR', name: 'Israel', flag: '🇮🇱' },
  { id: 'CTR-UKR', name: 'Ukraine', flag: '🇺🇦' },
];

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function StatBar({
  label,
  valueA,
  valueB,
  nameA,
  nameB,
  format = 'number',
}: {
  label: string;
  valueA: number;
  valueB: number;
  nameA: string;
  nameB: string;
  format?: 'number' | 'percent' | 'currency';
}) {
  const total = valueA + valueB || 1;
  const pctA = (valueA / total) * 100;
  const pctB = (valueB / total) * 100;

  const formatValue = (v: number) => {
    if (format === 'percent') return `${v.toFixed(1)}%`;
    if (format === 'currency') return `$${(v / 1e9).toFixed(0)}B`;
    return v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v.toString();
  };

  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1 text-xs">
        <span className="text-slate-400">{label}</span>
        <div className="flex gap-4">
          <span className="text-blue-400">{formatValue(valueA)}</span>
          <span className="text-red-400">{formatValue(valueB)}</span>
        </div>
      </div>
      <div className="flex h-2 rounded-full overflow-hidden bg-slate-800">
        <div
          className="bg-blue-500 transition-all duration-500"
          style={{ width: `${pctA}%` }}
        />
        <div
          className="bg-red-500 transition-all duration-500"
          style={{ width: `${pctB}%` }}
        />
      </div>
    </div>
  );
}

function OutcomeProbability({
  outcomes,
  nameA,
  nameB,
}: {
  outcomes: Record<string, number>;
  nameA: string;
  nameB: string;
}) {
  const entries = Object.entries(outcomes).filter(([k]) => !k.includes('intervention') && !k.includes('escalation'));

  return (
    <div className="space-y-2">
      {entries?.map(([key, value]) => {
        let label = key.replace(/_/g, ' ').replace(nameA, '').replace(nameB, '').trim();
        let color = 'bg-slate-600';

        if (key.includes('decisive') && key.includes(nameA)) {
          label = `Decisive ${nameA} Victory`;
          color = 'bg-blue-500';
        } else if (key.includes('limited') && key.includes(nameA)) {
          label = `Limited ${nameA} Victory`;
          color = 'bg-blue-400';
        } else if (key.includes('stalemate')) {
          label = 'Stalemate / Ceasefire';
          color = 'bg-amber-500';
        } else if (key.includes('limited') && key.includes(nameB)) {
          label = `Limited ${nameB} Victory`;
          color = 'bg-red-400';
        } else if (key.includes('decisive') && key.includes(nameB)) {
          label = `Decisive ${nameB} Victory`;
          color = 'bg-red-500';
        }

        return (
          <div key={key}>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-300">{label}</span>
              <span className="text-slate-400">{(value * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full ${color} transition-all duration-500`}
                style={{ width: `${value * 100}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TimelineEvent({
  event,
}: {
  event: { day: number; phase: string; event: string; description: string; impact: string };
}) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
          D{event.day}
        </div>
        <div className="flex-1 w-0.5 bg-slate-700 my-1" />
      </div>
      <div className="flex-1 pb-4">
        <div className="text-xs text-amber-400 font-semibold mb-0.5">{event.phase}</div>
        <div className="text-sm text-slate-200">{event.event}</div>
        <div className="text-xs text-slate-400 mt-1">{event.description}</div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function BattlegroundTab() {
  const [countryA, setCountryA] = useState('CTR-IND');
  const [countryB, setCountryB] = useState('CTR-CHN');
  const [includeAllies, setIncludeAllies] = useState(false);
  const [duration, setDuration] = useState(30);
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<ForceComparison | null>(null);
  const [simulation, setSimulation] = useState<ConflictSimulation | null>(null);
  const [activeView, setActiveView] = useState<'comparison' | 'simulation'>('comparison');
  const [expandedSection, setExpandedSection] = useState<string | null>('outcomes');

  const { setExpertMapLayers, clearExpertMapLayers } = useAppStore();

  const runComparison = useCallback(async () => {
    setLoading(true);
    setSimulation(null);

    try {
      const response = await fetch('/api/v1/intelligence/battleground/compare-forces', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_a: countryA,
          country_b: countryB,
          include_allies: includeAllies,
        }),
      });

      const data = await response.json();
      if (data.status === 'success') {
        setComparison(data.data);
      }
    } catch (error) {
      console.error('Comparison failed:', error);
    } finally {
      setLoading(false);
    }
  }, [countryA, countryB, includeAllies]);

  const runSimulation = useCallback(async () => {
    setLoading(true);

    try {
      const response = await fetch('/api/v1/intelligence/battleground/simulate-conflict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_a: countryA,
          country_b: countryB,
          scenario_type: 'conventional',
          duration_days: duration,
        }),
      });

      const data = await response.json();
      if (data.status === 'success') {
        setSimulation(data.data);
        setComparison(data.data.force_comparison);
        setActiveView('simulation');

        // Update map with conflict visualization
        if (data.data.map_visualization) {
          setExpertMapLayers(data.data.map_visualization, [countryA, countryB]);
        }
      }
    } catch (error) {
      console.error('Simulation failed:', error);
    } finally {
      setLoading(false);
    }
  }, [countryA, countryB, duration, setExpertMapLayers]);

  const getCountryName = (id: string) => COUNTRIES.find((c) => c.id === id)?.name || id;
  const getCountryFlag = (id: string) => COUNTRIES.find((c) => c.id === id)?.flag || '🏳️';

  return (
    <div className="h-full flex flex-col bg-transparent">
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center gap-2 mb-3">
          <Swords className="w-5 h-5 text-red-400" />
          <span className="text-sm font-semibold text-slate-200">Virtual Battleground</span>
        </div>

        {/* Country Selectors */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">Country A</label>
            <select
              value={countryA}
              onChange={(e) => setCountryA(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200"
            >
              {COUNTRIES?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.flag} {c.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 block">Country B</label>
            <select
              value={countryB}
              onChange={(e) => setCountryB(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-200"
            >
              {COUNTRIES?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.flag} {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Options */}
        <div className="flex items-center gap-4 mb-3">
          <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={includeAllies}
              onChange={(e) => setIncludeAllies(e.target.checked)}
              className="rounded bg-slate-800 border-slate-600"
            />
            Include Allies
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Duration:</span>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300"
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={runComparison}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm py-2 rounded transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />}
            Compare Forces
          </button>
          <button
            onClick={runSimulation}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm py-2 rounded transition-colors"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Swords className="w-4 h-4" />}
            Simulate Conflict
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {loading && (
          <div className="flex items-center justify-center h-48">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-red-400 animate-spin mx-auto mb-2" />
              <div className="text-sm text-slate-400">Running simulation...</div>
            </div>
          </div>
        )}

        {!loading && comparison && (
          <div className="p-4 space-y-4">
            {/* Warnings */}
            {simulation?.warnings && simulation.warnings?.length > 0 && (
              <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-3">
                {simulation.warnings?.map((w, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-red-300">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    {w}
                  </div>
                ))}
              </div>
            )}

            {/* Force Comparison Header */}
            <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
              <div className="flex items-center justify-between mb-4">
                <div className="text-center flex-1">
                  <div className="text-2xl mb-1">{getCountryFlag(comparison.country_a.id)}</div>
                  <div className="text-sm font-semibold text-blue-400">{comparison.country_a.name}</div>
                  <div className="text-xs text-slate-500">Power Index: {comparison.country_a.power_index}</div>
                </div>
                <div className="px-4">
                  <div className="text-xl text-slate-500">VS</div>
                </div>
                <div className="text-center flex-1">
                  <div className="text-2xl mb-1">{getCountryFlag(comparison.country_b.id)}</div>
                  <div className="text-sm font-semibold text-red-400">{comparison.country_b.name}</div>
                  <div className="text-xs text-slate-500">Power Index: {comparison.country_b.power_index}</div>
                </div>
              </div>

              {/* Advantage Badge */}
              <div className="text-center mb-4">
                <span
                  className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${comparison.analysis.advantage === comparison.country_a.name
                    ? 'bg-blue-500/20 text-blue-400'
                    : comparison.analysis.advantage === comparison.country_b.name
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-amber-500/20 text-amber-400'
                    }`}
                >
                  {comparison.analysis.advantage_level === 'balanced' ? (
                    <Scale className="w-3 h-3" />
                  ) : comparison.analysis.advantage === comparison.country_a.name ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {comparison.analysis.advantage} ({comparison.analysis.advantage_level})
                </span>
              </div>

              {/* Stats Bars */}
              <StatBar
                label="Total Personnel"
                valueA={comparison.country_a.total_personnel}
                valueB={comparison.country_b.total_personnel}
                nameA={comparison.country_a.name}
                nameB={comparison.country_b.name}
              />
              <StatBar
                label="Aircraft"
                valueA={comparison.country_a.aircraft}
                valueB={comparison.country_b.aircraft}
                nameA={comparison.country_a.name}
                nameB={comparison.country_b.name}
              />
              <StatBar
                label="Tanks"
                valueA={comparison.country_a.tanks}
                valueB={comparison.country_b.tanks}
                nameA={comparison.country_a.name}
                nameB={comparison.country_b.name}
              />
              <StatBar
                label="Naval Vessels"
                valueA={comparison.country_a.naval_vessels}
                valueB={comparison.country_b.naval_vessels}
                nameA={comparison.country_a.name}
                nameB={comparison.country_b.name}
              />
              <StatBar
                label="Tech Level"
                valueA={comparison.country_a.tech_level}
                valueB={comparison.country_b.tech_level}
                nameA={comparison.country_a.name}
                nameB={comparison.country_b.name}
              />

              {/* Nuclear Status */}
              <div className="flex justify-around mt-4 pt-3 border-t border-slate-700/50">
                <div className="text-center">
                  <div className={`text-lg ${comparison.country_a.nuclear_capable ? 'text-yellow-400' : 'text-slate-600'}`}>
                    ☢️
                  </div>
                  <div className="text-[10px] text-slate-500">Nuclear</div>
                </div>
                <div className="text-center">
                  <div className={`text-lg ${comparison.analysis.nuclear_parity ? 'text-amber-400' : 'text-slate-600'}`}>
                    <Shield className="w-5 h-5 mx-auto" />
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {comparison.analysis.nuclear_parity ? 'MAD Active' : 'No Parity'}
                  </div>
                </div>
                <div className="text-center">
                  <div className={`text-lg ${comparison.country_b.nuclear_capable ? 'text-yellow-400' : 'text-slate-600'}`}>
                    ☢️
                  </div>
                  <div className="text-[10px] text-slate-500">Nuclear</div>
                </div>
              </div>
            </div>

            {/* Simulation Results */}
            {simulation && (
              <>
                {/* Outcome Probabilities */}
                <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                  <button
                    onClick={() => setExpandedSection(expandedSection === 'outcomes' ? null : 'outcomes')}
                    className="w-full p-3 flex items-center justify-between hover:bg-slate-700/30"
                  >
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-amber-400" />
                      <span className="text-sm font-medium text-slate-200">Outcome Probabilities</span>
                    </div>
                    {expandedSection === 'outcomes' ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                  {expandedSection === 'outcomes' && (
                    <div className="p-4 pt-0">
                      <OutcomeProbability
                        outcomes={simulation.outcome_probabilities}
                        nameA={comparison.country_a.name}
                        nameB={comparison.country_b.name}
                      />
                    </div>
                  )}
                </div>

                {/* Timeline */}
                <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                  <button
                    onClick={() => setExpandedSection(expandedSection === 'timeline' ? null : 'timeline')}
                    className="w-full p-3 flex items-center justify-between hover:bg-slate-700/30"
                  >
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-cyan-400" />
                      <span className="text-sm font-medium text-slate-200">Projected Timeline</span>
                    </div>
                    {expandedSection === 'timeline' ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                  {expandedSection === 'timeline' && (
                    <div className="p-4 pt-0">
                      {simulation.timeline?.map((event, i) => (
                        <TimelineEvent key={i} event={event} />
                      ))}
                    </div>
                  )}
                </div>

                {/* Impacts */}
                <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
                  <button
                    onClick={() => setExpandedSection(expandedSection === 'impacts' ? null : 'impacts')}
                    className="w-full p-3 flex items-center justify-between hover:bg-slate-700/30"
                  >
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-red-400" />
                      <span className="text-sm font-medium text-slate-200">Impact Assessment</span>
                    </div>
                    {expandedSection === 'impacts' ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </button>
                  {expandedSection === 'impacts' && (
                    <div className="p-4 pt-0 space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 flex items-center gap-1">
                          <DollarSign className="w-3 h-3" /> Economic Impact
                        </span>
                        <span className="text-red-400 font-semibold">
                          ${(simulation.impacts.economic_impact_usd / 1e12).toFixed(2)}T
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Users className="w-3 h-3" /> Military Casualties
                        </span>
                        <span className="text-amber-400">
                          {simulation.impacts.estimated_military_casualties.low.toLocaleString()} -{' '}
                          {simulation.impacts.estimated_military_casualties.high.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Users className="w-3 h-3" /> Civilian Casualties
                        </span>
                        <span className="text-orange-400">
                          {simulation.impacts.estimated_civilian_casualties.low.toLocaleString()} -{' '}
                          {simulation.impacts.estimated_civilian_casualties.high.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Globe className="w-3 h-3" /> Trade Disruption
                        </span>
                        <span className="text-cyan-400">{simulation.impacts.global_trade_disruption_pct.toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Zap className="w-3 h-3" /> Energy Price Impact
                        </span>
                        <span className="text-yellow-400">+{simulation.impacts.energy_price_impact_pct.toFixed(1)}%</span>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* Alliance Info */}
            {comparison.alliance_analysis && (
              <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-3">
                  <Network className="w-4 h-4 text-purple-400" />
                  <span className="text-sm font-medium text-slate-200">Alliance Analysis</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <div className="text-slate-500 mb-1">{comparison.country_a.name} Allies</div>
                    <div className="text-blue-400 font-semibold">{comparison.alliance_analysis.alliance_count_a} nations</div>
                    {comparison.country_a.allies?.slice(0, 3)?.map((ally) => (
                      <div key={ally.id} className="text-slate-400">• {ally.alliance}</div>
                    ))}
                  </div>
                  <div>
                    <div className="text-slate-500 mb-1">{comparison.country_b.name} Allies</div>
                    <div className="text-red-400 font-semibold">{comparison.alliance_analysis.alliance_count_b} nations</div>
                    {comparison.country_b.allies?.slice(0, 3)?.map((ally) => (
                      <div key={ally.id} className="text-slate-400">• {ally.alliance}</div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !comparison && (
          <div className="flex items-center justify-center h-48">
            <div className="text-center px-4">
              <Swords className="w-12 h-12 text-red-400/50 mx-auto mb-3" />
              <div className="text-sm text-slate-400 mb-1">Virtual Battleground</div>
              <div className="text-xs text-slate-500 max-w-xs mx-auto">
                Select two countries and run a force comparison or conflict simulation to analyze strategic scenarios.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
