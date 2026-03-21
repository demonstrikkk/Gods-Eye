import React, { useState } from 'react';
import { apiClient } from '../services/api';
import { ScenarioTree } from '../components/ScenarioTree';
import {
    Brain, Send, Loader2, AlertTriangle, Shield, TrendingUp, TrendingDown,
    Clock, Zap, Target, ChevronRight, BarChart3, Lightbulb, GitBranch, Repeat
} from 'lucide-react';

interface Scenario {
    name: string;
    probability: string;
    trigger: string;
    outcome: string;
    impact_severity: number;
}

interface RiskFactor {
    factor: string;
    severity: string;
    description: string;
}

interface TimelineEvent {
    day: number;
    event: string;
}

interface AnalysisResult {
    executive_summary: string;
    situation_analysis: string;
    key_risk_factors: RiskFactor[];
    impact_on_india: Record<string, string>;
    forecasts: Record<string, string>;
    scenarios: Scenario[];
    strategic_recommendations: string[];
    scenario_tree: any[];
    timeline: TimelineEvent[];
    _meta?: { tools_used: string[]; timestamp: string };
}

const EXAMPLE_QUERIES = [
    "According to current war situation how will India be affected in 45 days?",
    "What is the impact of rising oil prices on rural constituencies?",
    "How does negative sentiment in border states correlate with defense spending?",
    "If PM-Kisan coverage drops below 40%, what are the political consequences?",
    "Analyze the chain reaction of a monsoon failure on booth-level sentiment",
];

const getSeverityColor = (severity: string) => {
    switch (severity) {
        case 'Critical': return 'text-danger bg-danger/10 border-danger/30';
        case 'High': return 'text-warning bg-warning/10 border-warning/30';
        case 'Medium': return 'text-primary-light bg-primary/10 border-primary/30';
        case 'Low': return 'text-success bg-success/10 border-success/30';
        default: return 'text-text-muted bg-panel border-border';
    }
};

const getProbColor = (prob: string) => {
    switch (prob) {
        case 'High': return 'text-danger';
        case 'Medium': return 'text-warning';
        case 'Low': return 'text-success';
        default: return 'text-text-muted';
    }
};

export const StrategicDashboard: React.FC = () => {
    const [query, setQuery] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'scenarios' | 'timeline' | 'whatif'>('overview');

    // What-If state
    const [whatifQuery, setWhatifQuery] = useState('');
    const [whatifResult, setWhatifResult] = useState<any>(null);
    const [isSimulating, setIsSimulating] = useState(false);

    const handleAnalysis = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;
        setIsAnalyzing(true);
        setAnalysis(null);
        setWhatifResult(null);
        try {
            const { data } = await apiClient.post('/intelligence/strategic-analysis', { query });
            setAnalysis(data.data);
            setActiveTab('overview');
        } catch {
            setAnalysis({
                executive_summary: "Strategic engine offline. Check backend connectivity.",
                situation_analysis: "",
                key_risk_factors: [],
                impact_on_india: {},
                forecasts: {},
                scenarios: [],
                strategic_recommendations: [],
                scenario_tree: [],
                timeline: [],
            });
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleWhatIf = async () => {
        if (!whatifQuery.trim() || !analysis) return;
        setIsSimulating(true);
        try {
            const { data } = await apiClient.post('/intelligence/scenario-simulate', {
                original_context: analysis.executive_summary + " " + analysis.situation_analysis,
                whatif_query: whatifQuery,
                variables: {}
            });
            setWhatifResult(data.data);
        } catch {
            setWhatifResult({ revised_outcome: "Simulation engine requires backend connectivity." });
        } finally {
            setIsSimulating(false);
        }
    };

    return (
        <div className="space-y-6 bg-background p-2 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center space-x-4">
                <div className="bg-purple-500/20 p-3 rounded-2xl border border-purple-500/30 shadow-[0_0_20px_rgba(168,85,247,0.2)]">
                    <Brain className="text-purple-400" size={28} />
                </div>
                <div>
                    <h1 className="text-2xl font-black text-text-main tracking-tight uppercase">Strategic Intelligence Engine</h1>
                    <p className="text-xs text-text-muted uppercase tracking-[0.2em] font-mono mt-0.5">
                        Agentic Multi-Tool LLM System // Plan → Execute → Reason → Simulate
                    </p>
                </div>
            </div>

            {/* Query Interface */}
            <form onSubmit={handleAnalysis} className="glass-panel p-6 border-purple-500/30 bg-purple-500/5 relative overflow-hidden">
                <div className="absolute inset-0 opacity-[0.02] pointer-events-none bg-[radial-gradient(#a855f7_1px,transparent_1px)] [background-size:16px_16px]"></div>
                <label className="text-[10px] font-black tracking-[0.3em] text-purple-400 flex items-center mb-4 uppercase relative z-10">
                    <Zap size={14} className="mr-2 animate-pulse" /> Strategic Query — Ask Anything About Geopolitics, Economics, or Governance
                </label>
                <div className="flex space-x-3 relative z-10">
                    <input
                        type="text" value={query} onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g. According to current war situation how will India be affected in 45 days?"
                        className="flex-1 bg-background/80 border border-border text-text-main rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-purple-500 transition-all"
                    />
                    <button type="submit" disabled={isAnalyzing}
                        className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl px-8 font-bold transition-all disabled:opacity-50 shadow-[0_0_20px_rgba(168,85,247,0.3)] flex items-center space-x-2">
                        {isAnalyzing ? <Loader2 className="animate-spin" size={20} /> : <><Brain size={18} /><span>Analyze</span></>}
                    </button>
                </div>

                {/* Example Queries */}
                <div className="mt-4 flex flex-wrap gap-2 relative z-10">
                    {EXAMPLE_QUERIES.map((eq, i) => (
                        <button key={i} type="button" onClick={() => setQuery(eq)}
                            className="text-[10px] px-3 py-1 rounded-full border border-border/50 text-text-muted hover:text-purple-400 hover:border-purple-500/50 transition-colors bg-background/50">
                            {eq.slice(0, 50)}...
                        </button>
                    ))}
                </div>
            </form>

            {/* Loading State */}
            {isAnalyzing && (
                <div className="glass-panel p-12 flex flex-col items-center justify-center border-purple-500/20">
                    <Brain className="animate-pulse text-purple-400 mb-4" size={48} />
                    <div className="text-lg font-black text-text-main mb-2">Strategic Intelligence Engine Active</div>
                    <div className="text-xs text-text-muted font-mono uppercase tracking-[0.3em] animate-pulse">
                        Planning → Gathering Data → Reasoning → Generating Scenarios...
                    </div>
                    <div className="mt-6 flex space-x-3">
                        {['Planner', 'Tools', 'Reasoning', 'Scenarios'].map((step, i) => (
                            <div key={step} className="flex items-center text-[10px] uppercase tracking-wider">
                                <Loader2 className={`mr-1 text-purple-400 ${i === 0 ? 'animate-spin' : 'opacity-30'}`} size={12} />
                                <span className={i === 0 ? 'text-purple-400' : 'text-text-muted/50'}>{step}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Results */}
            {analysis && !isAnalyzing && (
                <>
                    {/* Tab Bar */}
                    <div className="flex space-x-1 bg-panel/30 border border-border/50 rounded-xl p-1">
                        {[
                            { id: 'overview', label: 'Strategic Overview', icon: <BarChart3 size={14} /> },
                            { id: 'scenarios', label: 'Scenario Analysis', icon: <GitBranch size={14} /> },
                            { id: 'timeline', label: 'Timeline', icon: <Clock size={14} /> },
                            { id: 'whatif', label: 'What-If Simulator', icon: <Repeat size={14} /> },
                        ].map(tab => (
                            <button key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                                    activeTab === tab.id
                                        ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                                        : 'text-text-muted hover:text-text-main hover:bg-panel/50'
                                }`}>
                                {tab.icon}
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Tab: Overview */}
                    {activeTab === 'overview' && (
                        <div className="space-y-6">
                            {/* Executive Summary */}
                            <div className="glass-panel p-6 border-l-4 border-l-purple-500">
                                <h3 className="text-xs font-black uppercase tracking-widest text-purple-400 mb-3 flex items-center">
                                    <Target size={14} className="mr-2" /> Executive Summary
                                </h3>
                                <p className="text-sm text-text-main leading-relaxed">{analysis.executive_summary}</p>
                            </div>

                            {/* Situation Analysis */}
                            {analysis.situation_analysis && (
                                <div className="glass-panel p-6">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-3">Situation Analysis</h3>
                                    <p className="text-[13px] text-text-main leading-relaxed">{analysis.situation_analysis}</p>
                                </div>
                            )}

                            {/* Risk Factors */}
                            {analysis.key_risk_factors?.length > 0 && (
                                <div className="glass-panel p-6">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-4 flex items-center">
                                        <AlertTriangle size={14} className="mr-2 text-warning" /> Key Risk Factors
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {analysis.key_risk_factors.map((risk, i) => (
                                            <div key={i} className={`p-4 rounded-xl border ${getSeverityColor(risk.severity)}`}>
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="font-bold text-sm">{risk.factor}</span>
                                                    <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded bg-background/50">{risk.severity}</span>
                                                </div>
                                                <p className="text-[11px] opacity-80 leading-relaxed">{risk.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Impact on India */}
                            {analysis.impact_on_india && Object.keys(analysis.impact_on_india).length > 0 && (
                                <div className="glass-panel p-6">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-4 flex items-center">
                                        <Shield size={14} className="mr-2 text-primary-light" /> Impact on India
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {Object.entries(analysis.impact_on_india).map(([domain, assessment]) => (
                                            <div key={domain} className="bg-panel/30 border border-border/50 rounded-xl p-4">
                                                <div className="text-[10px] font-black uppercase tracking-widest text-primary-light mb-2 flex items-center">
                                                    <ChevronRight size={12} className="mr-1" /> {domain}
                                                </div>
                                                <p className="text-xs text-text-main leading-relaxed">{assessment}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Forecasts */}
                            {analysis.forecasts && Object.keys(analysis.forecasts).length > 0 && (
                                <div className="glass-panel p-6">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-4 flex items-center">
                                        <TrendingUp size={14} className="mr-2 text-success" /> Strategic Forecasts
                                    </h3>
                                    <div className="space-y-3">
                                        {Object.entries(analysis.forecasts).map(([period, forecast]) => (
                                            <div key={period} className="flex items-start gap-4 p-3 rounded-xl bg-background/40 border border-border/30">
                                                <Clock size={14} className="text-primary-light mt-0.5 shrink-0" />
                                                <div>
                                                    <div className="text-[10px] font-black text-text-muted uppercase tracking-wider mb-1">
                                                        {period.replace(/_/g, ' ')}
                                                    </div>
                                                    <p className="text-xs text-text-main">{forecast}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Recommendations */}
                            {analysis.strategic_recommendations?.length > 0 && (
                                <div className="glass-panel p-6 border-success/20 bg-success/5">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-success mb-4 flex items-center">
                                        <Lightbulb size={14} className="mr-2" /> Strategic Recommendations
                                    </h3>
                                    <div className="space-y-2">
                                        {analysis.strategic_recommendations.map((rec, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-background/40 border border-border/30">
                                                <span className="text-success font-black text-sm mt-0.5">{i + 1}.</span>
                                                <span className="text-xs text-text-main leading-relaxed">{rec}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Meta */}
                            {analysis._meta && (
                                <div className="text-[10px] text-text-muted/40 text-right font-mono">
                                    Tools: {analysis._meta.tools_used?.join(', ')} | {analysis._meta.timestamp}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Tab: Scenarios */}
                    {activeTab === 'scenarios' && (
                        <div className="space-y-6">
                            {/* Scenario Cards */}
                            {analysis.scenarios?.length > 0 && (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    {analysis.scenarios.map((s, i) => (
                                        <div key={i} className={`glass-panel p-6 border-t-4 ${
                                            s.name === 'Best Case' ? 'border-t-success' : s.name === 'Worst Case' ? 'border-t-danger' : 'border-t-warning'
                                        }`}>
                                            <div className="flex justify-between items-start mb-3">
                                                <h4 className="text-sm font-black text-text-main">{s.name}</h4>
                                                <span className={`text-[10px] font-black ${getProbColor(s.probability)}`}>{s.probability} Prob</span>
                                            </div>
                                            <div className="text-[10px] text-text-muted uppercase mb-2 font-bold">Trigger</div>
                                            <p className="text-xs text-text-main mb-3">{s.trigger}</p>
                                            <div className="text-[10px] text-text-muted uppercase mb-2 font-bold">Outcome</div>
                                            <p className="text-xs text-text-main mb-4">{s.outcome}</p>
                                            <div className="flex items-center justify-between pt-3 border-t border-border/30">
                                                <span className="text-[10px] text-text-muted uppercase">Impact Severity</span>
                                                <div className="flex items-center gap-1">
                                                    {Array.from({ length: 10 }).map((_, j) => (
                                                        <div key={j} className={`w-2 h-4 rounded-sm ${j < s.impact_severity
                                                            ? (s.impact_severity >= 7 ? 'bg-danger' : s.impact_severity >= 4 ? 'bg-warning' : 'bg-success')
                                                            : 'bg-border/30'}`}></div>
                                                    ))}
                                                    <span className="text-xs font-black ml-2">{s.impact_severity}/10</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Scenario Tree */}
                            {analysis.scenario_tree?.length > 0 && (
                                <div className="glass-panel p-6">
                                    <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-4 flex items-center">
                                        <GitBranch size={14} className="mr-2 text-purple-400" /> Scenario Chain Reaction Tree
                                    </h3>
                                    <ScenarioTree data={analysis.scenario_tree} />
                                </div>
                            )}
                        </div>
                    )}

                    {/* Tab: Timeline */}
                    {activeTab === 'timeline' && analysis.timeline?.length > 0 && (
                        <div className="glass-panel p-6">
                            <h3 className="text-xs font-black uppercase tracking-widest text-text-muted mb-6 flex items-center">
                                <Clock size={14} className="mr-2 text-primary-light" /> Projected Event Timeline
                            </h3>
                            <div className="relative">
                                {/* Vertical line */}
                                <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-purple-500 via-primary to-success"></div>
                                <div className="space-y-6">
                                    {analysis.timeline.map((evt, i) => (
                                        <div key={i} className="flex items-start gap-6 relative">
                                            <div className="w-12 h-12 rounded-full bg-panel border-2 border-primary/50 flex items-center justify-center text-xs font-black text-primary-light shrink-0 z-10 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                                                D{evt.day}
                                            </div>
                                            <div className="flex-1 bg-background/40 border border-border/40 rounded-xl p-4 hover:border-primary/30 transition-colors">
                                                <div className="text-[10px] text-text-muted uppercase font-bold tracking-widest mb-1">Day {evt.day}</div>
                                                <p className="text-sm text-text-main font-medium">{evt.event}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Tab: What-If */}
                    {activeTab === 'whatif' && (
                        <div className="space-y-6">
                            <div className="glass-panel p-6 border-purple-500/30 bg-purple-500/5">
                                <h3 className="text-xs font-black uppercase tracking-widest text-purple-400 mb-4 flex items-center">
                                    <Repeat size={14} className="mr-2" /> What-If Scenario Simulator
                                </h3>
                                <p className="text-xs text-text-muted mb-4">
                                    Modify variables and assumptions from the original analysis. The AI will recompute outcomes dynamically.
                                </p>
                                <div className="flex space-x-3">
                                    <input
                                        type="text" value={whatifQuery} onChange={(e) => setWhatifQuery(e.target.value)}
                                        placeholder="e.g. What if oil prices increase by 30%? What if India cuts defense spending?"
                                        className="flex-1 bg-background/80 border border-border text-text-main rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-purple-500"
                                    />
                                    <button onClick={handleWhatIf} disabled={isSimulating}
                                        className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl px-6 font-bold transition-all disabled:opacity-50 flex items-center space-x-2">
                                        {isSimulating ? <Loader2 className="animate-spin" size={18} /> : <><Repeat size={16} /><span>Simulate</span></>}
                                    </button>
                                </div>
                            </div>

                            {/* What-If Results */}
                            {whatifResult && (
                                <div className="space-y-4">
                                    {whatifResult.simulation_title && (
                                        <div className="glass-panel p-6 border-l-4 border-l-purple-500">
                                            <h4 className="text-sm font-black text-purple-400 mb-2">{whatifResult.simulation_title}</h4>
                                            <p className="text-xs text-text-main leading-relaxed">{whatifResult.revised_outcome}</p>
                                        </div>
                                    )}

                                    {whatifResult.impact_delta && (
                                        <div className="glass-panel p-6">
                                            <h4 className="text-xs font-black uppercase tracking-widest text-text-muted mb-3">Impact Delta (Changes)</h4>
                                            <div className="grid grid-cols-2 gap-3">
                                                {Object.entries(whatifResult.impact_delta).map(([k, v]) => (
                                                    <div key={k} className="bg-panel/30 border border-border/50 rounded-xl p-3">
                                                        <div className="text-[10px] font-black uppercase text-primary-light mb-1">{k}</div>
                                                        <p className="text-xs text-text-main">{v as string}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {whatifResult.chain_reactions?.length > 0 && (
                                        <div className="glass-panel p-6">
                                            <h4 className="text-xs font-black uppercase tracking-widest text-text-muted mb-3 flex items-center">
                                                <TrendingDown size={14} className="mr-2 text-danger" /> Chain Reactions
                                            </h4>
                                            {whatifResult.chain_reactions.map((cr: any, i: number) => (
                                                <div key={i} className="mb-3 p-3 border border-border/30 rounded-xl bg-background/40">
                                                    <div className="text-xs font-bold text-warning mb-2">⚡ {cr.trigger}</div>
                                                    <div className="space-y-1 ml-4">
                                                        {cr.effects?.map((eff: string, j: number) => (
                                                            <div key={j} className="text-xs text-text-main flex items-center">
                                                                <ChevronRight size={12} className="text-danger mr-1" /> {eff}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
};
