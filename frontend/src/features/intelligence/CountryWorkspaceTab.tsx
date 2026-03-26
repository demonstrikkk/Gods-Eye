import React, { useState, useEffect, useCallback } from 'react';
import {
  Globe,
  Users,
  Shield,
  TrendingUp,
  AlertTriangle,
  Calendar,
  Zap,
  Target,
  ArrowRight,
  Loader2,
  ChevronDown,
  ChevronUp,
  Crown,
  Flag,
  Swords,
  Activity,
  Info,
} from 'lucide-react';

interface CountryWorkspace {
  country_id: string;
  country_name: string;
  overview: {
    region: string;
    macro_region?: string;
    risk_index: number;
    influence_index: number;
    sentiment: number;
    stability: string;
    pressure: string;
    active_signals: number;
    capital?: string;
    population?: number;
  };
  government: {
    head_of_state?: {
      id: string;
      name: string;
      role: string;
      party_affiliation?: string;
      influence_score: number;
      stability_risk: number;
      stance_on_india?: string;
      key_policies?: string[];
    };
    cabinet_members: Array<{
      id: string;
      name: string;
      role: string;
      portfolio?: string;
      influence_score: number;
      party_affiliation?: string;
    }>;
  };
  political_landscape: {
    parties: Array<{
      id: string;
      name: string;
      ideology: string;
      seats_held?: number;
      total_seats?: number;
      influence_score: number;
      leader?: string;
      coalition_status?: string;
    }>;
    parliamentary_composition?: {
      total_seats: number;
      ruling_coalition_seats: number;
      opposition_seats: number;
    };
  };
  electoral_calendar: {
    upcoming_elections: Array<{
      id: string;
      type: string;
      scheduled_date: string;
      status: string;
      election_name: string;
      stakes: string;
    }>;
    recent_elections: Array<{
      id: string;
      type: string;
      date: string;
      status: string;
      election_name: string;
      winner?: string;
      turnout?: number;
    }>;
  };
  military_capabilities: {
    overall_strength: number;
    active_personnel: number;
    reserve_personnel: number;
    defense_budget_usd: number;
    nuclear_capable: boolean;
    modernization_index: number;
    force_readiness: number;
    key_assets: Array<{
      category: string;
      count: number;
      capability: string;
    }>;
  };
  intelligence: {
    recent_signals: Array<{
      id: string;
      title: string;
      category: string;
      severity: string;
      time: string;
      summary: string;
    }>;
    risk_factors: Array<{
      factor: string;
      severity: string;
      description: string;
    }>;
  };
  relationships: {
    allies: Array<{
      country_id: string;
      country_name: string;
      relationship_strength: number;
      relationship_type: string;
    }>;
    adversaries: Array<{
      country_id: string;
      country_name: string;
      relationship_strength: number;
      relationship_type: string;
    }>;
    neutral: Array<{
      country_id: string;
      country_name: string;
      relationship_strength: number;
      relationship_type: string;
    }>;
  };
  key_rivals: Array<{
    country_id: string;
    country_name: string;
    rivalry_score: number;
    primary_domains: string[];
    threat_level: string;
  }>;
}

export function CountryWorkspaceTab() {
  const [workspace, setWorkspace] = useState<CountryWorkspace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState('CTR-CHN');
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    government: true,
    political: false,
    electoral: false,
    military: false,
    intelligence: true,
    relationships: false,
    rivals: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const loadWorkspace = useCallback(async (countryId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/data/country-workspace/${countryId}`);
      if (!response.ok) throw new Error('Failed to load workspace');
      const data = await response.json();
      setWorkspace(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkspace(selectedCountry);
  }, [selectedCountry, loadWorkspace]);

  const countryOptions = [
    { id: 'CTR-CHN', name: 'China' },
    { id: 'CTR-USA', name: 'United States' },
    { id: 'CTR-RUS', name: 'Russia' },
    { id: 'CTR-IND', name: 'India' },
    { id: 'CTR-PAK', name: 'Pakistan' },
    { id: 'CTR-GBR', name: 'United Kingdom' },
    { id: 'CTR-FRA', name: 'France' },
    { id: 'CTR-DEU', name: 'Germany' },
    { id: 'CTR-JPN', name: 'Japan' },
    { id: 'CTR-IRN', name: 'Iran' },
    { id: 'CTR-ISR', name: 'Israel' },
    { id: 'CTR-UKR', name: 'Ukraine' },
  ];

  const getRiskColor = (risk: number) => {
    if (risk >= 0.7) return 'text-red-400';
    if (risk >= 0.5) return 'text-orange-400';
    if (risk >= 0.3) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getSeverityColor = (severity: string) => {
    const s = severity.toLowerCase();
    if (s === 'high' || s === 'critical') return 'text-red-400';
    if (s === 'medium' || s === 'moderate') return 'text-orange-400';
    return 'text-yellow-400';
  };

  const getStanceColor = (stance?: string) => {
    if (!stance) return 'text-slate-400';
    if (stance === 'strong_ally' || stance === 'ally') return 'text-green-400';
    if (stance === 'neutral' || stance === 'complex') return 'text-blue-400';
    if (stance === 'adversary' || stance === 'hostile') return 'text-red-400';
    return 'text-slate-400';
  };

  const formatStance = (stance?: string) => {
    if (!stance) return 'Unknown';
    return stance.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  if (loading && !workspace) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-400">
        <AlertTriangle className="w-5 h-5 mr-2" />
        {error}
      </div>
    );
  }

  if (!workspace) return null;

  return (
    <div className="space-y-4 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-slate-200">Country Workspace</h2>
        </div>
        <select
          value={selectedCountry}
          onChange={(e) => setSelectedCountry(e.target.value)}
          className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-slate-300 focus:outline-none focus:border-blue-500"
        >
          {countryOptions?.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.name}
            </option>
          ))}
        </select>
      </div>

      {/* Overview Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('overview')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-semibold text-slate-300">Overview</span>
          </div>
          {expandedSections.overview ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections.overview && (
          <div className="p-4 bg-slate-900/30">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Region</div>
                <div className="text-sm text-slate-300">
                  {workspace.overview.region}
                  {workspace.overview.macro_region && ` • ${workspace.overview.macro_region}`}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Capital</div>
                <div className="text-sm text-slate-300">
                  {workspace.overview.capital || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Risk Index</div>
                <div className={`text-sm font-semibold ${getRiskColor(workspace.overview.risk_index)}`}>
                  {(workspace.overview.risk_index * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Influence Index</div>
                <div className="text-sm font-semibold text-purple-400">
                  {(workspace.overview.influence_index * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Stability</div>
                <div className="text-sm text-slate-300">{workspace.overview.stability}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Active Signals</div>
                <div className="text-sm font-semibold text-cyan-400">
                  {workspace.overview.active_signals}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Government Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('government')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Crown className="w-4 h-4 text-yellow-400" />
            <span className="text-sm font-semibold text-slate-300">Government Leadership</span>
          </div>
          {expandedSections.government ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections.government && (
          <div className="p-4 bg-slate-900/30 space-y-3">
            {workspace.government.head_of_state && (
              <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-3">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="text-sm font-semibold text-slate-200">
                      {workspace.government.head_of_state.name}
                    </div>
                    <div className="text-xs text-slate-400">
                      {workspace.government.head_of_state.role.replace(/_/g, ' ').toUpperCase()}
                      {workspace.government.head_of_state.party_affiliation && (
                        <span className="ml-2 text-blue-400">
                          • {workspace.government.head_of_state.party_affiliation}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-500">Influence</div>
                    <div className="text-sm font-semibold text-purple-400">
                      {(workspace.government.head_of_state.influence_score * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500">Stability Risk: </span>
                    <span className={getRiskColor(workspace.government.head_of_state.stability_risk)}>
                      {(workspace.government.head_of_state.stability_risk * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">India Stance: </span>
                    <span className={getStanceColor(workspace.government.head_of_state.stance_on_india)}>
                      {formatStance(workspace.government.head_of_state.stance_on_india)}
                    </span>
                  </div>
                </div>
                {workspace.government.head_of_state.key_policies && workspace.government.head_of_state.key_policies?.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-slate-700/50">
                    <div className="text-xs text-slate-500 mb-1">Key Policies:</div>
                    <div className="flex flex-wrap gap-1">
                      {workspace.government.head_of_state.key_policies?.map((policy, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 bg-blue-900/30 text-blue-300 rounded"
                        >
                          {policy}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {workspace?.government?.cabinet_members?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Cabinet Members ({workspace?.government?.cabinet_members?.length})
                </div>
                <div className="space-y-1.5">
                  {workspace?.government?.cabinet_members?.slice(0, 5)?.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between bg-slate-800/30 rounded px-2 py-1.5"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-xs text-slate-300 truncate">{member.name}</div>
                        <div className="text-[10px] text-slate-500">
                          {member.portfolio || member.role.replace(/_/g, ' ')}
                        </div>
                      </div>
                      <div className="text-xs text-purple-400 ml-2">
                        {(member.influence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Political Landscape Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('political')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Flag className="w-4 h-4 text-green-400" />
            <span className="text-sm font-semibold text-slate-300">Political Landscape</span>
          </div>
          {expandedSections.political ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections.political && (
          <div className="p-4 bg-slate-900/30">
            {workspace.political_landscape.parliamentary_composition && (
              <div className="mb-3 bg-slate-800/50 rounded-lg p-3">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Parliamentary Composition
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-lg font-bold text-blue-400">
                      {workspace.political_landscape.parliamentary_composition.total_seats}
                    </div>
                    <div className="text-[10px] text-slate-500">Total Seats</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-green-400">
                      {workspace.political_landscape.parliamentary_composition.ruling_coalition_seats}
                    </div>
                    <div className="text-[10px] text-slate-500">Ruling Coalition</div>
                  </div>
                  <div>
                    <div className="text-lg font-bold text-orange-400">
                      {workspace.political_landscape.parliamentary_composition.opposition_seats}
                    </div>
                    <div className="text-[10px] text-slate-500">Opposition</div>
                  </div>
                </div>
              </div>
            )}
            <div className="space-y-2">
              {workspace.political_landscape.parties?.map((party) => (
                <div
                  key={party.id}
                  className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-2.5"
                >
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-200">{party.name}</div>
                      <div className="text-xs text-slate-400">{party.ideology}</div>
                    </div>
                    {party.seats_held !== undefined && party.total_seats && (
                      <div className="text-right ml-2">
                        <div className="text-sm font-semibold text-cyan-400">
                          {party.seats_held}/{party.total_seats}
                        </div>
                        <div className="text-[10px] text-slate-500">seats</div>
                      </div>
                    )}
                  </div>
                  {party.leader && (
                    <div className="text-xs text-slate-500">
                      Leader: <span className="text-slate-400">{party.leader}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Electoral Calendar Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('electoral')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-semibold text-slate-300">Electoral Calendar</span>
          </div>
          {expandedSections.electoral ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections.electoral && (
          <div className="p-4 bg-slate-900/30 space-y-3">
            {workspace.electoral_calendar.upcoming_elections?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Upcoming Elections
                </div>
                <div className="space-y-1.5">
                  {workspace.electoral_calendar.upcoming_elections?.map((election) => (
                    <div
                      key={election.id}
                      className="bg-blue-900/20 border border-blue-500/30 rounded p-2"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-sm text-slate-200">{election.election_name}</div>
                          <div className="text-xs text-slate-400">
                            {election.type.replace(/_/g, ' ').toUpperCase()}
                          </div>
                        </div>
                        <div className="text-xs text-cyan-400">{election.scheduled_date}</div>
                      </div>
                      <div className="text-xs text-slate-500 mt-1">{election.stakes}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {workspace.electoral_calendar.recent_elections?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Recent Elections
                </div>
                <div className="space-y-1.5">
                  {workspace.electoral_calendar.recent_elections?.map((election) => (
                    <div
                      key={election.id}
                      className="bg-slate-800/30 border border-slate-700/50 rounded p-2"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-sm text-slate-300">{election.election_name}</div>
                          <div className="text-xs text-slate-500">{election.type.replace(/_/g, ' ')}</div>
                        </div>
                        <div className="text-xs text-slate-400">{election.date}</div>
                      </div>
                      {election.winner && (
                        <div className="text-xs text-green-400 mt-1">Winner: {election.winner}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Military Capabilities Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('military')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Swords className="w-4 h-4 text-red-400" />
            <span className="text-sm font-semibold text-slate-300">Military Capabilities</span>
          </div>
          {expandedSections.military ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections.military && (
          <div className="p-4 bg-slate-900/30">
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="bg-slate-800/50 rounded p-2">
                <div className="text-xs text-slate-500">Overall Strength</div>
                <div className="text-lg font-bold text-red-400">
                  {(workspace.military_capabilities.overall_strength * 100).toFixed(0)}%
                </div>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <div className="text-xs text-slate-500">Force Readiness</div>
                <div className="text-lg font-bold text-orange-400">
                  {(workspace.military_capabilities.force_readiness * 100).toFixed(0)}%
                </div>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <div className="text-xs text-slate-500">Active Personnel</div>
                <div className="text-sm font-semibold text-slate-300">
                  {workspace.military_capabilities.active_personnel.toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-800/50 rounded p-2">
                <div className="text-xs text-slate-500">Nuclear Capable</div>
                <div className="text-sm font-semibold text-yellow-400">
                  {workspace.military_capabilities.nuclear_capable ? 'Yes' : 'No'}
                </div>
              </div>
            </div>
            {workspace.military_capabilities.key_assets?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Key Assets</div>
                <div className="grid grid-cols-2 gap-2">
                  {workspace.military_capabilities.key_assets?.map((asset, i) => (
                    <div key={i} className="bg-slate-800/30 rounded p-2">
                      <div className="text-xs text-slate-400">{asset.category}</div>
                      <div className="text-sm font-semibold text-slate-200">{asset.count}</div>
                      <div className="text-[10px] text-slate-500">{asset.capability}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Intelligence Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('intelligence')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-semibold text-slate-300">
              Recent Intelligence ({workspace?.intelligence?.recent_signals?.length})
            </span>
          </div>
          {expandedSections?.intelligence ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections?.intelligence && (
          <div className="p-4 bg-slate-900/30 space-y-2">
            {workspace.intelligence.recent_signals?.map((signal) => (
              <div
                key={signal.id}
                className="bg-slate-800/30 border border-slate-700/50 rounded p-2.5"
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex-1">
                    <div className="text-sm text-slate-200">{signal.title}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{signal.summary}</div>
                  </div>
                  <div className={`text-xs font-semibold ml-2 ${getSeverityColor(signal.severity)}`}>
                    {signal.severity}
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">{signal.category}</span>
                  <span className="text-slate-600">{signal.time}</span>
                </div>
              </div>
            ))}
            {workspace?.intelligence.risk_factors?.length > 0 && (
              <div className="mt-3 pt-3 border-t border-slate-700/50">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Risk Factors
                </div>
                <div className="space-y-1.5">
                  {workspace.intelligence.risk_factors?.map((risk, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <AlertTriangle className={`w-3 h-3 mt-0.5 flex-shrink-0 ${getSeverityColor(risk.severity)}`} />
                      <div className="flex-1">
                        <div className="text-xs text-slate-300">{risk.factor}</div>
                        <div className="text-[10px] text-slate-500">{risk.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Relationships Section */}
      <div className="border border-slate-700 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('relationships')}
          className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
        >
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-semibold text-slate-300">Relationships</span>
          </div>
          {expandedSections.relationships ? (
            <ChevronUp className="w-4 h-4 text-slate-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500" />
          )}
        </button>
        {expandedSections.relationships && (
          <div className="p-4 bg-slate-900/30 space-y-3">
            {workspace.relationships.allies?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Allies ({workspace.relationships.allies?.length})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {workspace.relationships.allies?.map((ally) => (
                    <span
                      key={ally.country_id}
                      className="text-xs px-2 py-1 bg-green-900/30 text-green-300 border border-green-500/30 rounded"
                    >
                      {ally.country_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {workspace.relationships.adversaries?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Adversaries ({workspace.relationships.adversaries?.length})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {workspace.relationships.adversaries?.map((adv) => (
                    <span
                      key={adv.country_id}
                      className="text-xs px-2 py-1 bg-red-900/30 text-red-300 border border-red-500/30 rounded"
                    >
                      {adv.country_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {workspace.relationships.neutral?.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  Neutral ({workspace.relationships.neutral?.length})
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {workspace.relationships.neutral?.map((neu) => (
                    <span
                      key={neu.country_id}
                      className="text-xs px-2 py-1 bg-blue-900/30 text-blue-300 border border-blue-500/30 rounded"
                    >
                      {neu.country_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Key Rivals Section */}
      {workspace.key_rivals?.length > 0 && (
        <div className="border border-slate-700 rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('rivals')}
            className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 flex items-center justify-between transition-colors"
          >
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-red-400" />
              <span className="text-sm font-semibold text-slate-300">
                Key Rivals ({workspace.key_rivals?.length})
              </span>
            </div>
            {expandedSections.rivals ? (
              <ChevronUp className="w-4 h-4 text-slate-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-500" />
            )}
          </button>
          {expandedSections.rivals && (
            <div className="p-4 bg-slate-900/30 space-y-2">
              {workspace.key_rivals?.map((rival) => (
                <div
                  key={rival.country_id}
                  className="bg-red-900/20 border border-red-500/30 rounded-lg p-3"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="text-sm font-semibold text-slate-200">
                        {rival.country_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        Threat Level: <span className="text-red-400">{rival.threat_level}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-slate-500">Rivalry Score</div>
                      <div className="text-sm font-bold text-red-400">
                        {(rival.rivalry_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {rival.primary_domains?.map((domain, i) => (
                      <span
                        key={i}
                        className="text-[10px] px-1.5 py-0.5 bg-red-900/40 text-red-300 rounded"
                      >
                        {domain}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
