// ─────────────────────────────────────────────────────────────────────────────
// Visual Intelligence Tab — Unified Visual + Data + Map Intelligence Interface
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  Image,
  Map,
  Lightbulb,
  Loader2,
  Send,
  Download,
  ExternalLink,
  ChevronRight,
  Globe2,
  Target,
  Clock,
  Database,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  TrendingUp,
  GitBranch,
} from 'lucide-react';
import { useAppStore } from '@/store';
import { postVisualIntelligence } from '@/services/api';
import type { VisualIntelligenceResponse, ViChartOutput, ViDiagramOutput, ViInsightSynthesis, ViParsedIntent } from '@/types';

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function TabButton({
  active,
  onClick,
  children,
  count,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  count?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all border-b-2 ${
        active
          ? 'border-cyan-500 text-cyan-400 bg-cyan-500/5'
          : 'border-transparent text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
      }`}
    >
      {children}
      {count !== undefined && count > 0 && (
        <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-slate-700 text-slate-300">
          {count}
        </span>
      )}
    </button>
  );
}

function ParsedIntentBadges({ intent }: { intent: ViParsedIntent }) {
  const domainColors: Record<string, string> = {
    economics: 'bg-green-500/20 text-green-400 border-green-500/30',
    trade: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    geopolitics: 'bg-red-500/20 text-red-400 border-red-500/30',
    climate: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    defense: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    infrastructure: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    energy: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    space: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  };

  return (
    <div className="p-3 border-b border-slate-700/50 bg-slate-800/30">
      <div className="flex flex-wrap gap-2 items-center text-xs">
        {/* Domain */}
        <span className={`px-2 py-1 rounded border ${domainColors[intent.primary_domain] || 'bg-slate-700/50 text-slate-400 border-slate-600'}`}>
          {intent.primary_domain}
        </span>

        {/* Intent Type */}
        <span className="px-2 py-1 rounded bg-slate-700/50 text-slate-300 border border-slate-600">
          {intent.intent_type.replace('_', ' ')}
        </span>

        {/* Countries */}
        {intent.countries.slice(0, 3).map((country) => (
          <span key={country} className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center gap-1">
            <Globe2 className="w-3 h-3" />
            {country}
          </span>
        ))}

        {/* Indicators */}
        {intent.indicators.slice(0, 2).map((ind) => (
          <span key={ind} className="px-2 py-1 rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">
            {ind}
          </span>
        ))}

        {/* Confidence */}
        <span className="ml-auto px-2 py-1 rounded bg-slate-700/50 text-slate-400 flex items-center gap-1">
          <Target className="w-3 h-3" />
          {(intent.parse_confidence * 100).toFixed(0)}% confidence
        </span>
      </div>
    </div>
  );
}

function ChartViewer({ charts }: { charts: ViChartOutput[] }) {
  const [selectedChart, setSelectedChart] = useState(0);

  if (charts.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500">
        <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No charts generated for this query</p>
      </div>
    );
  }

  const chart = charts[selectedChart];

  return (
    <div className="p-4 space-y-4">
      {/* Chart selector if multiple */}
      {charts.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {charts.map((c, i) => (
            <button
              key={i}
              onClick={() => setSelectedChart(i)}
              className={`px-3 py-1.5 rounded text-xs whitespace-nowrap transition-all ${
                i === selectedChart
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600'
              }`}
            >
              {c.title || `Chart ${i + 1}`}
            </button>
          ))}
        </div>
      )}

      {/* Chart display */}
      <motion.div
        key={selectedChart}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden"
      >
        <div className="p-3 border-b border-slate-700/50 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-200">{chart.title}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-400">
            {chart.chart_type}
          </span>
        </div>

        <div className="p-4">
          <img
            src={chart.chart_url}
            alt={chart.title}
            className="w-full rounded"
            loading="lazy"
          />
        </div>

        {/* Chart insight */}
        {chart.insight && (
          <div className="px-4 pb-3">
            <div className="flex items-start gap-2 p-3 rounded bg-cyan-500/10 border border-cyan-500/20">
              <Sparkles className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
              <p className="text-sm text-cyan-300">{chart.insight}</p>
            </div>
          </div>
        )}

        {/* Data summary */}
        <div className="px-4 pb-4">
          <p className="text-xs text-slate-500">{chart.data_summary}</p>
        </div>
      </motion.div>

      {/* Actions */}
      <div className="flex gap-2">
        <a
          href={chart.chart_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs px-3 py-1.5 rounded bg-slate-800 text-slate-400 hover:text-white border border-slate-700 hover:border-slate-600 flex items-center gap-1.5 transition-all"
        >
          <ExternalLink className="w-3 h-3" /> Open Full Size
        </a>
        <button className="text-xs px-3 py-1.5 rounded bg-slate-800 text-slate-400 hover:text-white border border-slate-700 hover:border-slate-600 flex items-center gap-1.5 transition-all">
          <Download className="w-3 h-3" /> Download
        </button>
      </div>
    </div>
  );
}

function DiagramViewer({ diagrams }: { diagrams: ViDiagramOutput[] }) {
  const [selectedDiagram, setSelectedDiagram] = useState(0);

  if (diagrams.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500">
        <Image className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No diagrams generated for this query</p>
      </div>
    );
  }

  const diagram = diagrams[selectedDiagram];

  return (
    <div className="p-4 space-y-4">
      {/* Diagram selector if multiple */}
      {diagrams.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {diagrams.map((d, i) => (
            <button
              key={i}
              onClick={() => setSelectedDiagram(i)}
              className={`px-3 py-1.5 rounded text-xs whitespace-nowrap transition-all ${
                i === selectedDiagram
                  ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                  : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600'
              }`}
            >
              {d.diagram_type.replace('_', ' ')} {i > 0 && `#${i + 1}`}
            </button>
          ))}
        </div>
      )}

      {/* Diagram display */}
      <motion.div
        key={selectedDiagram}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden"
      >
        <div className="p-3 border-b border-slate-700/50 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-200">
            {diagram.diagram_type.replace('_', ' ')} Diagram
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-violet-500/20 text-violet-400">
            AI Generated
          </span>
        </div>

        <div className="p-4">
          <img
            src={diagram.image_url}
            alt={diagram.description}
            className="w-full rounded"
            loading="lazy"
          />
        </div>

        {/* Description */}
        <div className="px-4 pb-4">
          <p className="text-sm text-slate-400">{diagram.description}</p>
        </div>
      </motion.div>

      {/* Actions */}
      <div className="flex gap-2">
        <a
          href={diagram.image_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs px-3 py-1.5 rounded bg-slate-800 text-slate-400 hover:text-white border border-slate-700 hover:border-slate-600 flex items-center gap-1.5 transition-all"
        >
          <ExternalLink className="w-3 h-3" /> Open Full Size
        </a>
      </div>
    </div>
  );
}

function InsightPanel({ insight }: { insight: ViInsightSynthesis }) {
  return (
    <div className="p-4 space-y-4 overflow-y-auto custom-scrollbar">
      {/* Executive Summary */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-cyan-400">Executive Summary</h3>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">{insight.executive_summary}</p>
      </div>

      {/* Key Findings */}
      {insight.key_findings.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <h3 className="text-sm font-semibold text-slate-200">Key Findings</h3>
          </div>
          <ul className="space-y-2">
            {insight.key_findings.map((finding, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Causal Chain */}
      {insight.causal_chain.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-3">
            <GitBranch className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-semibold text-slate-200">Causal Chain</h3>
          </div>
          <div className="space-y-2">
            {insight.causal_chain.map((step, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center text-xs">
                  {i + 1}
                </span>
                <span className="text-slate-400">{step}</span>
                {i < insight.causal_chain.length - 1 && (
                  <ChevronRight className="w-4 h-4 text-slate-600 ml-auto" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Domain Connections */}
      {insight.cross_domain_connections.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-3">
            <Globe2 className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-slate-200">Cross-Domain Connections</h3>
          </div>
          <ul className="space-y-2">
            {insight.cross_domain_connections.map((conn, i) => (
              <li key={i} className="text-sm text-slate-400 pl-4 border-l-2 border-blue-500/30">
                {conn}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {insight.recommendations.length > 0 && (
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-4 h-4 text-yellow-400" />
            <h3 className="text-sm font-semibold text-slate-200">Recommendations</h3>
          </div>
          <ul className="space-y-2">
            {insight.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                <span className="text-yellow-400">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Data Sources & Confidence */}
      <div className="flex items-center justify-between p-3 rounded bg-slate-800/30 border border-slate-700/30 text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5" />
          <span>Sources: {insight.data_sources.join(', ')}</span>
        </div>
        <div className="flex items-center gap-2">
          <Target className="w-3.5 h-3.5" />
          <span>Confidence: {(insight.confidence_score * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function VisualIntelligenceTab() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VisualIntelligenceResponse | null>(null);
  const [activeView, setActiveView] = useState<'charts' | 'diagrams' | 'insights'>('charts');

  const { setExpertMapLayers, setAffectedRegions } = useAppStore();

  const handleSubmit = useCallback(async () => {
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await postVisualIntelligence(query, {
        includeMap: true,
        includeExpertAnalysis: false,
      });

      setResult(response.data);

      // Update map with generated commands
      if (response.data.map_data?.commands?.length > 0) {
        // The map commands will be processed by the map engine
        console.log('Map commands generated:', response.data.map_data.commands.length);
      }

      setExpertMapLayers([], response.data.map_data?.affected_regions || []);
      if (response.data.map_data?.affected_regions?.length > 0) {
        setAffectedRegions(response.data.map_data.affected_regions);
      }

      // Auto-switch to charts if available
      if (response.data.charts?.length > 0) {
        setActiveView('charts');
      } else if (response.data.diagrams?.length > 0) {
        setActiveView('diagrams');
      } else {
        setActiveView('insights');
      }
    } catch (err) {
      console.error('Visual intelligence error:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [query, loading, setAffectedRegions, setExpertMapLayers]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/50">
      {/* Header & Input */}
      <div className="p-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Visual Intelligence</h2>
            <p className="text-xs text-slate-500">Charts, Diagrams & Insights</p>
          </div>
        </div>

        {/* Query Input */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Compare GDP growth of India and China..."
            className="w-full px-4 py-2.5 pr-12 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25"
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md bg-cyan-500 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-cyan-600 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Example Queries */}
        {!result && (
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              'India space missions economics trend',
              'Compare GDP of India and China',
              'Oil prices impact on supply chain',
            ].map((example) => (
              <button
                key={example}
                onClick={() => setQuery(example)}
                className="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mx-4 mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
            <p className="text-sm text-slate-400">Analyzing your query...</p>
            <p className="text-xs text-slate-500 mt-1">Generating charts, diagrams & insights</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          {/* Parsed Intent Display */}
          <ParsedIntentBadges intent={result.parsed_intent} />

          {/* Tab Navigation */}
          <div className="border-b border-slate-700/50">
            <div className="flex">
              <TabButton
                active={activeView === 'charts'}
                onClick={() => setActiveView('charts')}
                count={result.charts?.length}
              >
                <BarChart3 className="w-4 h-4" /> Charts
              </TabButton>
              <TabButton
                active={activeView === 'diagrams'}
                onClick={() => setActiveView('diagrams')}
                count={result.diagrams?.length}
              >
                <Image className="w-4 h-4" /> Diagrams
              </TabButton>
              <TabButton
                active={activeView === 'insights'}
                onClick={() => setActiveView('insights')}
              >
                <Lightbulb className="w-4 h-4" /> Insights
              </TabButton>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <AnimatePresence mode="wait">
              {activeView === 'charts' && (
                <motion.div
                  key="charts"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                >
                  <ChartViewer charts={result.charts || []} />
                </motion.div>
              )}
              {activeView === 'diagrams' && (
                <motion.div
                  key="diagrams"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                >
                  <DiagramViewer diagrams={result.diagrams || []} />
                </motion.div>
              )}
              {activeView === 'insights' && result.insight && (
                <motion.div
                  key="insights"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                >
                  <InsightPanel insight={result.insight} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer Stats */}
          <div className="p-3 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-500">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {result.processing_time_ms.toFixed(0)}ms
              </span>
              <span className="flex items-center gap-1">
                <Database className="w-3 h-3" />
                {result.data_sources?.length || 0} sources
              </span>
            </div>
            <span className="flex items-center gap-1">
              <Target className="w-3 h-3" />
              Quality: {((result.data_quality_score || 0) * 100).toFixed(0)}%
            </span>
          </div>
        </>
      )}

      {/* Empty State */}
      {!result && !loading && (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-sm">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-cyan-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-200 mb-2">
              Visual Strategic Intelligence
            </h3>
            <p className="text-sm text-slate-400 mb-4">
              Transform complex queries into data-driven charts, visual diagrams, and actionable insights.
            </p>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-2 rounded bg-slate-800/50 border border-slate-700/50">
                <BarChart3 className="w-5 h-5 text-green-400 mx-auto mb-1" />
                <p className="text-xs text-slate-400">Charts</p>
              </div>
              <div className="p-2 rounded bg-slate-800/50 border border-slate-700/50">
                <Image className="w-5 h-5 text-violet-400 mx-auto mb-1" />
                <p className="text-xs text-slate-400">Diagrams</p>
              </div>
              <div className="p-2 rounded bg-slate-800/50 border border-slate-700/50">
                <Map className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                <p className="text-xs text-slate-400">Maps</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
