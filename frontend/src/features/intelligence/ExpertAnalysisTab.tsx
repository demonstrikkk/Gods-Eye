// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — Expert Analysis Tab
// Multi-agent expert reasoning with debate, consensus, and uncertainty
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Loader2,
  Send,
  Scale,
  TrendingUp,
  Shield,
  Zap,
  MessageSquare,
  BarChart3,
  Target,
  Info,
  Map,
} from 'lucide-react';
import { postExpertAnalysis } from '@/services/api';
import { useAppStore } from '@/store';
import type {
  ExpertAnalysisResponse,
  Disagreement,
  MinorityOpinion,
  AgentContribution,
  DebateSummary,
} from '@/types';

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

interface ConfidenceIndicatorProps {
  level: string;
  score: number;
}

function ConfidenceIndicator({ level, score }: ConfidenceIndicatorProps) {
  const getColor = () => {
    if (score >= 0.75) return 'text-emerald-400 bg-emerald-500/20';
    if (score >= 0.5) return 'text-amber-400 bg-amber-500/20';
    if (score >= 0.25) return 'text-orange-400 bg-orange-500/20';
    return 'text-red-400 bg-red-500/20';
  };

  const getIcon = () => {
    if (score >= 0.75) return <CheckCircle className="w-4 h-4" />;
    if (score >= 0.5) return <Target className="w-4 h-4" />;
    return <AlertTriangle className="w-4 h-4" />;
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${getColor()}`}>
      {getIcon()}
      <span>{level}</span>
      <span className="opacity-70">({(score * 100).toFixed(0)}%)</span>
    </div>
  );
}

interface ConsensusStrengthBadgeProps {
  strength: string;
}

function ConsensusStrengthBadge({ strength }: ConsensusStrengthBadgeProps) {
  const config: Record<string, { color: string; icon: React.ReactNode }> = {
    unanimous: { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: <CheckCircle className="w-3 h-3" /> },
    strong: { color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: <CheckCircle className="w-3 h-3" /> },
    moderate: { color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: <Scale className="w-3 h-3" /> },
    weak: { color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: <AlertTriangle className="w-3 h-3" /> },
    divergent: { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: <XCircle className="w-3 h-3" /> },
    no_consensus: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', icon: <Info className="w-3 h-3" /> },
  };

  const { color, icon } = config[strength] || config.moderate;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs ${color}`}>
      {icon}
      {strength.replace('_', ' ')}
    </span>
  );
}

interface AgentCardProps {
  name: string;
  contribution: AgentContribution;
}

function AgentCard({ name, contribution }: AgentCardProps) {
  const getDomainIcon = (domain: string) => {
    const icons: Record<string, React.ReactNode> = {
      economics: <TrendingUp className="w-4 h-4" />,
      geopolitics: <Shield className="w-4 h-4" />,
      social_dynamics: <Users className="w-4 h-4" />,
      climate_environment: <Zap className="w-4 h-4" />,
      policy: <Scale className="w-4 h-4" />,
      risk: <AlertTriangle className="w-4 h-4" />,
      simulation: <BarChart3 className="w-4 h-4" />,
    };
    return icons[domain] || <Brain className="w-4 h-4" />;
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
      <div className="flex items-center gap-2 mb-2">
        <div className="p-1.5 rounded bg-cyan-500/20 text-cyan-400">
          {getDomainIcon(contribution.domain)}
        </div>
        <div>
          <div className="text-sm font-medium text-slate-200">{contribution.name}</div>
          <div className="text-xs text-slate-500 capitalize">{contribution.domain.replace('_', ' ')}</div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="text-center">
          <div className="text-cyan-400 font-semibold">{(contribution.confidence * 100).toFixed(0)}%</div>
          <div className="text-slate-500">Confidence</div>
        </div>
        <div className="text-center">
          <div className="text-amber-400 font-semibold">{contribution.key_claims}</div>
          <div className="text-slate-500">Claims</div>
        </div>
        <div className="text-center">
          <div className="text-emerald-400 font-semibold">{contribution.data_sources}</div>
          <div className="text-slate-500">Sources</div>
        </div>
      </div>
    </div>
  );
}

interface DisagreementCardProps {
  disagreement: Disagreement;
}

function DisagreementCard({ disagreement }: DisagreementCardProps) {
  const [expanded, setExpanded] = useState(false);

  const severityColors: Record<string, string> = {
    minor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    moderate: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    major: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    fundamental: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <div className="bg-slate-800/50 rounded-lg border border-red-500/20 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <XCircle className="w-4 h-4 text-red-400" />
          <div className="text-left">
            <div className="text-sm text-slate-200">{disagreement.topic}</div>
            <div className="text-xs text-slate-500">{disagreement.agents.join(' vs ')}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded border text-xs ${severityColors[disagreement.severity]}`}>
            {disagreement.severity}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-700/50"
          >
            <div className="p-3 space-y-3">
              <div>
                <div className="text-xs text-slate-500 mb-1">Positions</div>
                {Object.entries(disagreement.positions)?.map(([agentId, position]) => (
                  <div key={agentId} className="text-xs text-slate-300 mb-1">
                    <span className="text-cyan-400">{agentId}:</span> {position.slice(0, 150)}...
                  </div>
                ))}
              </div>
              {disagreement.conflicting_evidence?.length > 0 && (
                <div>
                  <div className="text-xs text-slate-500 mb-1">Conflicting Evidence</div>
                  {disagreement.conflicting_evidence?.map((ev, i) => (
                    <div key={i} className="text-xs text-orange-300">- {ev}</div>
                  ))}
                </div>
              )}
              <div className="text-xs text-slate-500">
                Impact on conclusion: <span className="text-amber-400">{disagreement.impact_on_conclusion}</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface MinorityOpinionCardProps {
  opinion: MinorityOpinion;
}

function MinorityOpinionCard({ opinion }: MinorityOpinionCardProps) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-3 border border-amber-500/20">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-medium text-slate-200">{opinion.agent}</span>
          <span className="text-xs text-slate-500 capitalize">({opinion.domain})</span>
        </div>
        <span className="text-xs text-amber-400">{(opinion.probability * 100).toFixed(0)}% probability</span>
      </div>
      <p className="text-xs text-slate-300 mb-2">{opinion.position.slice(0, 200)}...</p>
      <div className="text-xs text-slate-500">
        Differs from consensus by: <span className="text-amber-400">{(opinion.difference_from_consensus * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}

interface DebateSummaryViewProps {
  debate: DebateSummary;
}

function DebateSummaryView({ debate }: DebateSummaryViewProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-slate-800/50 rounded-lg border border-purple-500/30 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Users className="w-5 h-5 text-purple-400" />
          <div className="text-left">
            <div className="text-sm font-medium text-slate-200">Agent Debate Summary</div>
            <div className="text-xs text-slate-500">{debate.rounds_conducted} rounds conducted</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs ${debate.convergence_achieved ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
            }`}>
            {debate.convergence_achieved ? 'Converged' : 'Divergent'}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-700/50"
          >
            <div className="p-3 space-y-3">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <div className="text-lg font-semibold text-cyan-400">{debate.total_arguments}</div>
                  <div className="text-xs text-slate-500">Arguments</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-amber-400">{debate.total_rebuttals}</div>
                  <div className="text-xs text-slate-500">Rebuttals</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-purple-400">{(debate.final_convergence * 100).toFixed(0)}%</div>
                  <div className="text-xs text-slate-500">Convergence</div>
                </div>
              </div>

              {debate.consensus_view && (
                <div className="bg-emerald-500/10 rounded p-2 border border-emerald-500/20">
                  <div className="text-xs text-emerald-400 mb-1">Consensus View</div>
                  <div className="text-xs text-slate-300">{debate.consensus_view.statement}</div>
                </div>
              )}

              <div>
                <div className="text-xs text-slate-500 mb-2">Agent Positions</div>
                <div className="space-y-1">
                  {debate.position_summary?.map((pos, i) => (
                    <div key={i} className="flex items-center justify-between text-xs bg-slate-700/30 rounded px-2 py-1">
                      <span className="text-slate-300">{pos.agent}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">{pos.stance}</span>
                        <span className="text-cyan-400">{(pos.probability * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface UncertaintyPanelProps {
  uncertainty: ExpertAnalysisResponse['uncertainty_quantification'];
}

function UncertaintyPanel({ uncertainty }: UncertaintyPanelProps) {
  if (!uncertainty) return null;

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-medium text-slate-200">Uncertainty Analysis</span>
        <ConfidenceIndicator level={uncertainty.confidence_level} score={uncertainty.overall_confidence} />
      </div>

      {uncertainty.uncertainty_factors?.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-slate-500 mb-1">Uncertainty Factors</div>
          <div className="space-y-1">
            {uncertainty.uncertainty_factors?.map((factor, i) => (
              <div key={i} className="text-xs text-amber-300 flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">!</span>
                {factor}
              </div>
            ))}
          </div>
        </div>
      )}

      {uncertainty.key_assumptions?.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-slate-500 mb-1">Key Assumptions</div>
          <div className="space-y-1">
            {uncertainty.key_assumptions?.map((assumption, i) => (
              <div key={i} className="text-xs text-slate-400 flex items-start gap-2">
                <span className="text-slate-500 mt-0.5">*</span>
                {assumption}
              </div>
            ))}
          </div>
        </div>
      )}

      {uncertainty.data_gaps?.length > 0 && (
        <div>
          <div className="text-xs text-slate-500 mb-1">Data Gaps</div>
          <div className="space-y-1">
            {uncertainty.data_gaps?.map((gap, i) => (
              <div key={i} className="text-xs text-red-300 flex items-start gap-2">
                <span className="text-red-500 mt-0.5">-</span>
                {gap}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  analysis?: ExpertAnalysisResponse;
  timestamp: number;
}

export default function ExpertAnalysisTab() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<ExpertAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'consensus' | 'agents' | 'disagreements' | 'uncertainty'>('consensus');
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [showConversation, setShowConversation] = useState(false);

  // Store for map visualization
  const { setExpertMapLayers, clearExpertMapLayers } = useAppStore();

  // Update map layers when analysis changes
  useEffect(() => {
    if (analysis?.map_visualization?.layers) {
      setExpertMapLayers(
        analysis.map_visualization.layers,
        analysis.map_visualization.affected_regions || []
      );
    }
    return () => {
      // Clear layers when component unmounts
      clearExpertMapLayers();
    };
  }, [analysis, setExpertMapLayers, clearExpertMapLayers]);

  const handleSubmit = useCallback(async () => {
    if (!query.trim() || loading) return;

    const userMessage: ConversationMessage = {
      role: 'user',
      content: query,
      timestamp: Date.now(),
    };

    setConversation((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);
    setQuery(''); // Clear input immediately

    try {
      const response = await postExpertAnalysis(query);
      if (response.status === 'success') {
        setAnalysis(response.data);

        const assistantMessage: ConversationMessage = {
          role: 'assistant',
          content: response.data.executive_summary,
          analysis: response.data,
          timestamp: Date.now(),
        };

        setConversation((prev) => [...prev, assistantMessage]);
        setShowConversation(true);
      } else {
        setError('Analysis failed. Please try again.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  }, [query, loading]);

  const sampleQueries = [
    "What happens to India if oil prices rise 20%?",
    "Analyze Middle East tensions impact on trade",
    "Assess China-India border situation",
    "Evaluate inflation trajectory for next 6 months",
  ];

  return (
    <div className="h-full flex flex-col bg-transparent">
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-5 h-5 text-purple-400" />
          <span className="text-sm font-semibold text-slate-200">Expert Multi-Agent Analysis</span>
        </div>

        {/* Input */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder={conversation?.length > 0 ? "Ask a follow-up question..." : "Ask a strategic question..."}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 pr-12 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded bg-purple-500 hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            ) : (
              <Send className="w-4 h-4 text-white" />
            )}
          </button>
        </div>

        {/* Sample queries */}
        {!analysis && conversation?.length === 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {sampleQueries?.map((sq, i) => (
              <button
                key={i}
                onClick={() => setQuery(sq)}
                className="text-xs px-2 py-1 rounded bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-purple-500/50 transition-colors"
              >
                {sq.slice(0, 40)}...
              </button>
            ))}
          </div>
        )}

        {/* Conversation Toggle */}
        {conversation?.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowConversation(!showConversation)}
              className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              {showConversation ? 'Hide' : 'Show'} conversation history ({conversation?.length} messages)
              {showConversation ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}
      </div>

      {/* Conversation History */}
      {showConversation && conversation?.length > 0 && (
        <div className="border-b border-slate-700/50 bg-slate-800/30 max-h-64 overflow-y-auto custom-scrollbar">
          <div className="p-3 space-y-2">
            {conversation?.map((msg, i) => (
              <div
                key={i}
                className={`text-xs rounded-lg p-2.5 ${msg.role === 'user'
                  ? 'bg-purple-500/10 border border-purple-500/30 text-purple-200'
                  : 'bg-slate-700/50 border border-slate-600/30 text-slate-300'
                  }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {msg.role === 'user' ? (
                    <MessageSquare className="w-3 h-3 text-purple-400" />
                  ) : (
                    <Brain className="w-3 h-3 text-cyan-400" />
                  )}
                  <span className="font-medium text-[10px] uppercase tracking-wider opacity-70">
                    {msg.role === 'user' ? 'You' : 'Expert Agents'}
                  </span>
                  <span className="text-[9px] text-slate-500 ml-auto">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="pl-5 leading-relaxed">{msg.content}</p>
                {msg.analysis && (
                  <button
                    onClick={() => setAnalysis(msg.analysis!)}
                    className="mt-2 pl-5 text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                  >
                    View full analysis →
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-500/10 border-b border-red-500/30">
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <XCircle className="w-4 h-4" />
            {error}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-3" />
            <div className="text-sm text-slate-400">Running expert analysis...</div>
            <div className="text-xs text-slate-500 mt-1">Agents debating and building consensus</div>
          </div>
        </div>
      )}

      {/* Results */}
      {analysis && !loading && (
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="pb-6">
            {/* Executive Summary */}
            <div className="p-4 border-b border-slate-700/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-200">Executive Summary</span>
                {analysis.expert_assessment?.confidence && (
                  <ConfidenceIndicator
                    level={analysis.expert_assessment.confidence.level}
                    score={analysis.expert_assessment.confidence.score}
                  />
                )}
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">{analysis.executive_summary}</p>

              {/* Meta info */}
              {analysis._meta && (
                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  {analysis._meta.debate_conducted && (
                    <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">
                      Debate Conducted
                    </span>
                  )}
                  {analysis._meta.consensus_strength && (
                    <ConsensusStrengthBadge strength={analysis._meta.consensus_strength} />
                  )}
                  {analysis._meta.expert_agents_consulted && (
                    <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-400">
                      {analysis._meta.expert_agents_consulted?.length} agents
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Section Tabs */}
            <div className="border-b border-slate-700/50">
              <div className="flex">
                {(['consensus', 'agents', 'disagreements', 'uncertainty'] as const)?.map((section) => (
                  <button
                    key={section}
                    onClick={() => setActiveSection(section)}
                    className={`flex-1 px-4 py-2 text-xs font-medium transition-colors ${activeSection === section
                      ? 'text-purple-400 border-b-2 border-purple-500'
                      : 'text-slate-500 hover:text-slate-300'
                      }`}
                  >
                    {section.charAt(0).toUpperCase() + section.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Section Content */}
            <div className="p-4 space-y-4">
              {activeSection === 'consensus' && (
                <>
                  {/* Consensus View */}
                  {analysis.expert_assessment?.consensus_view && (
                    <div className="bg-emerald-500/10 rounded-lg p-4 border border-emerald-500/30">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm font-medium text-emerald-400">Consensus View</span>
                      </div>
                      <p className="text-sm text-slate-300">{analysis.expert_assessment.consensus_view}</p>
                    </div>
                  )}

                  {/* Key Findings */}
                  {analysis.expert_assessment?.key_findings && analysis.expert_assessment.key_findings?.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-slate-200 mb-2">Key Findings</div>
                      <div className="space-y-2">
                        {analysis.expert_assessment.key_findings?.map((finding, i) => (
                          <div key={i} className="text-sm text-slate-300 flex items-start gap-2 bg-slate-800/30 rounded p-2">
                            <span className="text-cyan-400 mt-0.5">-</span>
                            {finding}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Debate Summary */}
                  {analysis.debate_summary && (
                    <DebateSummaryView debate={analysis.debate_summary} />
                  )}

                  {/* Recommendations */}
                  {analysis.strategic_recommendations && analysis.strategic_recommendations?.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-slate-200 mb-2">Strategic Recommendations</div>
                      <div className="space-y-2">
                        {analysis.strategic_recommendations?.map((rec, i) => (
                          <div key={i} className="text-sm text-slate-300 flex items-start gap-2 bg-slate-800/30 rounded p-2">
                            <span className="text-emerald-400 font-semibold">{i + 1}.</span>
                            {rec}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {activeSection === 'agents' && (
                <>
                  {analysis.agent_contributions && Object.entries(analysis.agent_contributions)?.length > 0 ? (
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(analysis.agent_contributions)?.map(([id, contrib]) => (
                        <AgentCard key={id} name={id} contribution={contrib} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center text-slate-500 py-8">
                      No agent contribution data available
                    </div>
                  )}

                  {/* Data Sources */}
                  {analysis.expert_assessment?.data_sources_cited && analysis.expert_assessment.data_sources_cited?.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-medium text-slate-200 mb-2">Data Sources Cited</div>
                      <div className="flex flex-wrap gap-2">
                        {analysis.expert_assessment.data_sources_cited?.map((src, i) => (
                          <span key={i} className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                            {src}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {activeSection === 'disagreements' && (
                <>
                  {analysis.expert_assessment?.disagreements && analysis.expert_assessment.disagreements?.length > 0 ? (
                    <div className="space-y-3">
                      {analysis.expert_assessment.disagreements?.map((d, i) => (
                        <DisagreementCard key={i} disagreement={d} />
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                      <div className="text-sm text-slate-400">No significant disagreements</div>
                      <div className="text-xs text-slate-500">All agents reached consensus</div>
                    </div>
                  )}

                  {/* Minority Opinions */}
                  {analysis.expert_assessment?.minority_opinions && analysis.expert_assessment.minority_opinions?.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-medium text-slate-200 mb-2">Minority Opinions</div>
                      <div className="space-y-3">
                        {analysis.expert_assessment.minority_opinions?.map((op, i) => (
                          <MinorityOpinionCard key={i} opinion={op} />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}

              {activeSection === 'uncertainty' && (
                <>
                  <UncertaintyPanel uncertainty={analysis.uncertainty_quantification} />

                  {/* Probabilistic Scenarios */}
                  {analysis.probabilistic_scenarios && Object.keys(analysis.probabilistic_scenarios)?.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-medium text-slate-200 mb-2">Probabilistic Scenarios</div>
                      <div className="space-y-2">
                        {Object.entries(analysis.probabilistic_scenarios)?.map(([name, scenario]) => (
                          <div
                            key={name}
                            className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-slate-200 capitalize">{name.replace('_', ' ')}</span>
                              <span className="text-sm text-cyan-400">{(scenario.probability * 100).toFixed(0)}%</span>
                            </div>
                            <p className="text-xs text-slate-400">{scenario.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Causal Chain */}
                  {analysis.causal_reasoning_chain && analysis.causal_reasoning_chain?.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-medium text-slate-200 mb-2">Causal Reasoning Chain</div>
                      <div className="relative pl-4 border-l-2 border-purple-500/30 space-y-2">
                        {analysis.causal_reasoning_chain?.map((step, i) => (
                          <div key={i} className="relative">
                            <div className="absolute -left-[1.35rem] w-3 h-3 rounded-full bg-purple-500 border-2 border-slate-900" />
                            <div className="text-xs text-slate-300 bg-slate-800/30 rounded p-2">{step}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!analysis && !loading && !error && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center px-4">
            <Brain className="w-12 h-12 text-purple-400/50 mx-auto mb-3" />
            <div className="text-sm text-slate-400 mb-1">Expert Multi-Agent Analysis</div>
            <div className="text-xs text-slate-500 max-w-xs mx-auto">
              Ask a strategic question and our expert agents will debate, cite sources, quantify uncertainty, and build consensus.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
