// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — Officials Tab
// Government officials, political parties, and elections tracking
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crown,
  Users,
  Vote,
  Search,
  ChevronDown,
  ChevronUp,
  MapPin,
  Calendar,
  TrendingUp,
  Shield,
  AlertTriangle,
  Globe,
  Building2,
  User,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { useAppStore } from '@/store';

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface Official {
  id: string;
  name: string;
  country_id: string;
  role: string;
  title: string;
  party?: string;
  alignment?: string;
  in_office_since?: string;
  term_ends?: string;
  age?: number;
  prior_roles?: string[];
  key_policies?: string[];
  stance_on_india?: string;
  influence_score: number;
  stability_risk: number;
  lat?: number;
  lng?: number;
}

interface Party {
  id: string;
  name: string;
  country_id: string;
  abbreviation: string;
  alignment: string;
  seats_parliament: number;
  total_seats: number;
  seat_share_pct: number;
  governing: boolean;
  support_pct: number;
}

interface Election {
  id: string;
  country_id: string;
  election_type: string;
  date: string;
  status: string;
  turnout_pct?: number;
  leading_party?: string;
  projected_winner?: string;
  confidence: number;
  key_issues: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// API Functions
// ─────────────────────────────────────────────────────────────────────────────

const fetchOfficials = async (): Promise<Official[]> => {
  const res = await fetch('/api/v1/data/officials');
  const data = await res.json();
  return data.data || [];
};

const fetchParties = async (): Promise<Party[]> => {
  const res = await fetch('/api/v1/data/parties');
  const data = await res.json();
  return data.data || [];
};

const fetchElections = async (): Promise<Election[]> => {
  const res = await fetch('/api/v1/data/elections');
  const data = await res.json();
  return data.data || [];
};

const fetchIndiaRelations = async () => {
  const res = await fetch('/api/v1/data/officials/india-relations');
  const data = await res.json();
  return data.data || {};
};

// ─────────────────────────────────────────────────────────────────────────────
// Helper Components
// ─────────────────────────────────────────────────────────────────────────────

function StanceBadge({ stance }: { stance?: string }) {
  if (!stance) return null;

  const colors: Record<string, string> = {
    strong_ally: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    ally: 'bg-green-500/20 text-green-400 border-green-500/30',
    friendly: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    neutral: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    cautious: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    adversarial: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    hostile: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  const labels: Record<string, string> = {
    strong_ally: 'Strong Ally',
    ally: 'Ally',
    friendly: 'Friendly',
    neutral: 'Neutral',
    cautious: 'Cautious',
    adversarial: 'Adversarial',
    hostile: 'Hostile',
  };

  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${colors[stance] || colors.neutral}`}>
      {labels[stance] || stance}
    </span>
  );
}

function AlignmentBadge({ alignment }: { alignment?: string }) {
  if (!alignment) return null;

  const colors: Record<string, string> = {
    far_left: 'text-red-400',
    left: 'text-rose-400',
    center_left: 'text-pink-400',
    center: 'text-purple-400',
    center_right: 'text-blue-400',
    right: 'text-indigo-400',
    far_right: 'text-violet-400',
    nationalist: 'text-amber-400',
    technocrat: 'text-cyan-400',
  };

  const labels: Record<string, string> = {
    far_left: 'Far Left',
    left: 'Left',
    center_left: 'Center-Left',
    center: 'Center',
    center_right: 'Center-Right',
    right: 'Right',
    far_right: 'Far Right',
    nationalist: 'Nationalist',
    technocrat: 'Technocrat',
  };

  return (
    <span className={`text-[10px] ${colors[alignment] || 'text-slate-400'}`}>
      {labels[alignment] || alignment}
    </span>
  );
}

function InfluenceBar({ score, label }: { score: number; label: string }) {
  const color = score >= 0.8 ? 'bg-emerald-500' : score >= 0.6 ? 'bg-cyan-500' : score >= 0.4 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-500 w-16">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${score * 100}%` }} />
      </div>
      <span className="text-[10px] text-slate-400 w-8">{Math.round(score * 100)}</span>
    </div>
  );
}

function OfficialCard({ official, onSelect }: { official: Official; onSelect: () => void }) {
  const countryFlag: Record<string, string> = {
    'CTR-USA': '🇺🇸',
    'CTR-RUS': '🇷🇺',
    'CTR-CHN': '🇨🇳',
    'CTR-IND': '🇮🇳',
    'CTR-GBR': '🇬🇧',
    'CTR-FRA': '🇫🇷',
    'CTR-DEU': '🇩🇪',
    'CTR-JPN': '🇯🇵',
    'CTR-PAK': '🇵🇰',
    'CTR-IRN': '🇮🇷',
    'CTR-ISR': '🇮🇱',
    'CTR-UKR': '🇺🇦',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 hover:border-blue-500/30 cursor-pointer transition-colors"
      onClick={onSelect}
    >
      <div className="flex items-start gap-3">
        <div className="text-2xl">{countryFlag[official.country_id] || '🏳️'}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-slate-200 truncate">{official.name}</span>
            <StanceBadge stance={official.stance_on_india} />
          </div>
          <div className="text-xs text-slate-400 mb-2">{official.title}</div>
          <div className="flex items-center gap-3 text-[10px] text-slate-500">
            {official.party && (
              <span className="flex items-center gap-1">
                <Building2 className="w-3 h-3" />
                {official.party}
              </span>
            )}
            <AlignmentBadge alignment={official.alignment} />
          </div>
        </div>
      </div>
      <div className="mt-3 space-y-1.5">
        <InfluenceBar score={official.influence_score} label="Influence" />
        <InfluenceBar score={1 - official.stability_risk} label="Stability" />
      </div>
    </motion.div>
  );
}

function ElectionCard({ election }: { election: Election }) {
  const statusColors: Record<string, string> = {
    upcoming: 'bg-amber-500/20 text-amber-400',
    ongoing: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-emerald-500/20 text-emerald-400',
  };

  const countryFlag: Record<string, string> = {
    'CTR-USA': '🇺🇸',
    'CTR-IND': '🇮🇳',
    'CTR-GBR': '🇬🇧',
    'CTR-FRA': '🇫🇷',
    'CTR-DEU': '🇩🇪',
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{countryFlag[election.country_id] || '🏳️'}</span>
          <span className="text-sm font-semibold text-slate-200 capitalize">
            {election.election_type} Election
          </span>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] capitalize ${statusColors[election.status]}`}>
          {election.status}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
        <Calendar className="w-3 h-3" />
        {new Date(election.date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
      </div>
      {election.projected_winner && (
        <div className="text-xs text-slate-300">
          <span className="text-slate-500">Projected: </span>
          {election.projected_winner}
          {election.confidence > 0 && (
            <span className="text-slate-500 ml-1">({Math.round(election.confidence * 100)}% conf)</span>
          )}
        </div>
      )}
      {election.key_issues?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {election.key_issues.slice(0, 3)?.map((issue) => (
            <span key={issue} className="px-1.5 py-0.5 bg-slate-700/50 rounded text-[10px] text-slate-400">
              {issue}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function OfficialsTab() {
  const [activeSection, setActiveSection] = useState<'officials' | 'parties' | 'elections'>('officials');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOfficial, setSelectedOfficial] = useState<Official | null>(null);
  const [filterCountry, setFilterCountry] = useState<string>('all');

  const { setExpertMapLayers, setSelected } = useAppStore();

  const { data: officials = [], isLoading: loadingOfficials } = useQuery({
    queryKey: ['officials'],
    queryFn: fetchOfficials,
    staleTime: 5 * 60 * 1000,
  });

  const { data: parties = [], isLoading: loadingParties } = useQuery({
    queryKey: ['parties'],
    queryFn: fetchParties,
    staleTime: 5 * 60 * 1000,
  });

  const { data: elections = [], isLoading: loadingElections } = useQuery({
    queryKey: ['elections'],
    queryFn: fetchElections,
    staleTime: 5 * 60 * 1000,
  });

  const { data: indiaRelations } = useQuery({
    queryKey: ['india-relations'],
    queryFn: fetchIndiaRelations,
    staleTime: 5 * 60 * 1000,
  });

  const countries = useMemo(() => {
    const unique = new Set(officials?.map((o) => o.country_id));
    return Array.from(unique);
  }, [officials]);

  const filteredOfficials = useMemo(() => {
    return officials.filter((o) => {
      const matchesSearch = searchQuery === '' ||
        o.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        o.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCountry = filterCountry === 'all' || o.country_id === filterCountry;
      return matchesSearch && matchesCountry;
    });
  }, [officials, searchQuery, filterCountry]);

  const headsOfState = useMemo(() => {
    return officials.filter((o) => o.role === 'head_of_state' || o.role === 'head_of_government');
  }, [officials]);

  const upcomingElections = useMemo(() => {
    return elections.filter((e) => e.status === 'upcoming');
  }, [elections]);

  const handleSelectOfficial = (official: Official) => {
    setSelectedOfficial(official);
    if (official.lat && official.lng) {
      setSelected(official.country_id, 'country');
    }
  };

  const isLoading = loadingOfficials || loadingParties || loadingElections;

  return (
    <div className="h-full flex flex-col bg-transparent">
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center gap-2 mb-3">
          <Crown className="w-5 h-5 text-amber-400" />
          <span className="text-sm font-semibold text-slate-200">Government Officials</span>
        </div>

        {/* Section Tabs */}
        <div className="flex gap-1 mb-3">
          {[
            { key: 'officials', label: 'Leaders', icon: <User className="w-3 h-3" /> },
            { key: 'parties', label: 'Parties', icon: <Building2 className="w-3 h-3" /> },
            { key: 'elections', label: 'Elections', icon: <Vote className="w-3 h-3" /> },
          ]?.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveSection(tab.key as any)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded text-xs transition-colors ${activeSection === tab.key
                ? 'bg-amber-500/20 text-amber-400'
                : 'text-slate-400 hover:text-slate-300'
                }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search and Filter (for officials) */}
        {activeSection === 'officials' && (
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search officials..."
                className="w-full bg-slate-800 border border-slate-700 rounded pl-8 pr-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-500"
              />
            </div>
            <select
              value={filterCountry}
              onChange={(e) => setFilterCountry(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-300"
            >
              <option value="all">All Countries</option>
              {countries?.map((c) => (
                <option key={c} value={c}>
                  {c.replace('CTR-', '')}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 text-amber-400 animate-spin" />
          </div>
        ) : (
          <>
            {/* Officials Section */}
            {activeSection === 'officials' && (
              <div className="space-y-4">
                {/* India Relations Summary */}
                {indiaRelations && (
                  <div className="bg-gradient-to-br from-orange-900/30 to-green-900/30 rounded-lg p-3 border border-orange-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Globe className="w-4 h-4 text-orange-400" />
                      <span className="text-xs font-semibold text-orange-300">India Relations Overview</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className="text-lg font-bold text-emerald-400">
                          {indiaRelations.stance_distribution?.strong_ally || 0}
                        </div>
                        <div className="text-[10px] text-slate-400">Strong Allies</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-cyan-400">
                          {(indiaRelations.stance_distribution?.ally || 0) +
                            (indiaRelations.stance_distribution?.friendly || 0)}
                        </div>
                        <div className="text-[10px] text-slate-400">Friendly</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-amber-400">
                          {indiaRelations.stance_distribution?.cautious || 0}
                        </div>
                        <div className="text-[10px] text-slate-400">Cautious</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Heads of State */}
                {filterCountry === 'all' && searchQuery === '' && (
                  <div>
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Heads of State & Government
                    </div>
                    <div className="grid gap-3">
                      {headsOfState.slice(0, 6)?.map((official) => (
                        <OfficialCard
                          key={official.id}
                          official={official}
                          onSelect={() => handleSelectOfficial(official)}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Filtered List */}
                {(filterCountry !== 'all' || searchQuery !== '') && (
                  <div>
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Results ({filteredOfficials?.length})
                    </div>
                    <div className="grid gap-3">
                      {filteredOfficials?.map((official) => (
                        <OfficialCard
                          key={official.id}
                          official={official}
                          onSelect={() => handleSelectOfficial(official)}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {filteredOfficials?.length === 0 && (
                  <div className="text-center text-slate-500 py-8">No officials found</div>
                )}
              </div>
            )}

            {/* Parties Section */}
            {activeSection === 'parties' && (
              <div className="space-y-3">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Governing Parties
                </div>
                {parties
                  .filter((p) => p.governing)
                  ?.map((party) => (
                    <div
                      key={party.id}
                      className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <span className="text-sm font-semibold text-slate-200">{party.name}</span>
                          <span className="text-xs text-slate-500 ml-2">({party.abbreviation})</span>
                        </div>
                        <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-[10px]">
                          Governing
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400">
                        <span>
                          {party.seats_parliament}/{party.total_seats} seats ({party.seat_share_pct}%)
                        </span>
                        <AlignmentBadge alignment={party.alignment} />
                      </div>
                      <div className="mt-2">
                        <div className="text-[10px] text-slate-500 mb-1">Polling</div>
                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{ width: `${party.support_pct}%` }}
                          />
                        </div>
                        <div className="text-right text-[10px] text-slate-500 mt-0.5">
                          {party.support_pct}%
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}

            {/* Elections Section */}
            {activeSection === 'elections' && (
              <div className="space-y-4">
                {upcomingElections?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      Upcoming Elections
                    </div>
                    <div className="grid gap-3">
                      {upcomingElections?.map((election) => (
                        <ElectionCard key={election.id} election={election} />
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Recent Elections
                  </div>
                  <div className="grid gap-3">
                    {elections
                      .filter((e) => e.status === 'completed')
                      ?.map((election) => (
                        <ElectionCard key={election.id} election={election} />
                      ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Selected Official Detail */}
      <AnimatePresence>
        {selectedOfficial && (
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            className="absolute bottom-0 left-0 right-0 bg-black/80 backdrop-blur-md border-t border-white/10 p-4 max-h-[50%] overflow-y-auto"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-lg font-bold text-slate-200">{selectedOfficial.name}</div>
                <div className="text-sm text-slate-400">{selectedOfficial.title}</div>
              </div>
              <button
                onClick={() => setSelectedOfficial(null)}
                className="text-slate-500 hover:text-slate-300"
              >
                <ChevronDown className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-500">Party:</span>
                <span className="ml-2 text-slate-300">{selectedOfficial.party || 'Independent'}</span>
              </div>
              <div>
                <span className="text-slate-500">In Office:</span>
                <span className="ml-2 text-slate-300">{selectedOfficial.in_office_since}</span>
              </div>
              <div>
                <span className="text-slate-500">Age:</span>
                <span className="ml-2 text-slate-300">{selectedOfficial.age}</span>
              </div>
              <div>
                <span className="text-slate-500">India Stance:</span>
                <span className="ml-2">
                  <StanceBadge stance={selectedOfficial.stance_on_india} />
                </span>
              </div>
            </div>

            {selectedOfficial.key_policies && selectedOfficial.key_policies?.length > 0 && (
              <div className="mt-3">
                <div className="text-xs text-slate-500 mb-1">Key Policies</div>
                <div className="flex flex-wrap gap-1">
                  {selectedOfficial.key_policies?.map((policy) => (
                    <span
                      key={policy}
                      className="px-2 py-0.5 bg-slate-700/50 rounded text-[10px] text-slate-300"
                    >
                      {policy}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
