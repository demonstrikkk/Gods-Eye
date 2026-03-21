import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Activity, ShieldAlert, Users, Loader2, Sparkles, Send, Zap, Briefcase, TrendingUp, Database, Globe } from 'lucide-react';
import { apiClient } from '../services/api';
import { Globe3D } from '../components/Globe3D';

const fetchExecutiveKPIs = async () => {
    const { data } = await apiClient.get('/intelligence/dashboard/executive');
    return data.kpis;
};

const fetchMapPoints = async () => {
    const { data } = await apiClient.get('/data/map');
    return data.data;
};

const fetchSentimentTimeline = async () => {
    const { data } = await apiClient.get('/data/sentiment/timeline?hours=24');
    return data.data;
};

export const ExecutiveDashboard: React.FC = () => {
    const [nlQuery, setNlQuery] = useState('');
    const [nlResponse, setNlResponse] = useState('');
    const [isQuerying, setIsQuerying] = useState(false);

    const { data: kpis, isLoading } = useQuery({
        queryKey: ['executive-kpis'],
        queryFn: fetchExecutiveKPIs,
        refetchInterval: 30000,
    });

    const { data: mapPoints } = useQuery({
        queryKey: ['map-points'],
        queryFn: fetchMapPoints,
    });

    const { data: timelineData } = useQuery({
        queryKey: ['sentiment-timeline'],
        queryFn: fetchSentimentTimeline,
        refetchInterval: 60000,
    });

    const handleNLQuery = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!nlQuery.trim()) return;
        setIsQuerying(true);
        setNlResponse('');
        try {
            const { data } = await apiClient.post('/intelligence/query', { query: nlQuery });
            setNlResponse(data.answer);
        } catch {
            setNlResponse("Intelligence Engine offline. Check backend connection.");
        } finally {
            setIsQuerying(false);
        }
    };

    const criticalBooths = mapPoints?.filter((p: any) => p.sentiment < 40) || [];

    return (
        <div className="space-y-6 bg-background p-2">

            {/* HERO 3D GLOBE */}
            <div className="glass-panel p-0 overflow-hidden relative h-[450px] border-primary/20 shadow-[0_0_40px_rgba(59,130,246,0.1)] rounded-2xl flex items-center justify-center">
                <div className="absolute top-4 left-6 z-10 pointer-events-none">
                    <h2 className="text-2xl font-black text-text-main flex items-center tracking-tight drop-shadow-md">
                        <Globe className="mr-3 text-primary-light animate-pulse" size={24} /> National Intelligence Graph
                    </h2>
                    <p className="text-xs text-text-muted mt-1 uppercase tracking-[0.2em] font-bold">Real-time civic ontology projection</p>
                </div>
                {mapPoints ? (
                    <Globe3D data={mapPoints} />
                ) : (
                    <div className="flex flex-col items-center justify-center text-text-muted">
                        <Loader2 className="animate-spin mb-3 text-primary" size={32} />
                        <div className="text-xs font-mono uppercase tracking-widest animate-pulse">Initializing Data Spheres...</div>
                    </div>
                )}
            </div>

            {/* KPI Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KPICard title="National Sentiment" value={kpis?.national_sentiment ?? '--'} suffix="%" icon={<Activity size={18} />} color="text-primary-light" loading={isLoading} />
                <KPICard title="Critical Booths" value={kpis?.active_alerts ?? '--'} icon={<ShieldAlert size={18} />} color="text-danger" loading={isLoading} />
                <KPICard title="Workers Online" value={kpis?.field_workers_online ?? '--'} icon={<Users size={18} />} color="text-success" loading={isLoading} />
                <KPICard title="Scheme Coverage" value={kpis?.scheme_coverage_pct ?? '--'} suffix="%" icon={<Database size={18} />} color="text-warning" loading={isLoading} />
            </div>

            {/* Secondary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MiniStat label="Citizens Profiled" value={kpis?.total_citizens?.toLocaleString() ?? '--'} />
                <MiniStat label="Booths Monitored" value={kpis?.total_booths ?? '--'} />
                <MiniStat label="Schemes Tracked" value={kpis?.total_schemes ?? '--'} />
                <MiniStat label="Open Complaints" value={kpis?.unresolved_complaints?.toLocaleString() ?? '--'} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left: Chart + Query */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Sentiment Pulse */}
                    <div className="glass-panel p-6 relative overflow-hidden">
                        <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:20px_20px]"></div>
                        <div className="flex items-center justify-between mb-6 relative z-10">
                            <div>
                                <h2 className="text-lg font-bold text-text-main flex items-center">
                                    <TrendingUp className="mr-2 text-primary-light" size={18} /> Sentiment Pulse (24h)
                                </h2>
                                <p className="text-[10px] text-text-muted mt-1 uppercase tracking-widest">Real-time national signal synthesis</p>
                            </div>
                            <span className="bg-primary/20 text-primary-light text-[10px] font-bold px-3 py-1 rounded-full border border-primary/30">
                                {kpis?.total_citizens?.toLocaleString() ?? '...'} citizens tracked
                            </span>
                        </div>
                        <div className="h-56 relative z-10">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={timelineData || []} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1f1f23" vertical={false} />
                                    <XAxis dataKey="time" stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#52525b" fontSize={10} tickLine={false} axisLine={false} />
                                    <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '12px', fontSize: '12px' }} />
                                    <Area type="monotone" dataKey="sentiment" stroke="#60a5fa" strokeWidth={3} fillOpacity={1} fill="url(#sentGrad)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* NL Intelligence Search */}
                    <form onSubmit={handleNLQuery} className="glass-panel p-6 border-primary/30 bg-primary/5">
                        <label className="text-[10px] font-bold tracking-[0.2em] text-primary-light flex items-center mb-4 uppercase">
                            <Sparkles size={14} className="mr-2 animate-pulse" /> Ontology Intelligence Query
                        </label>
                        <div className="flex space-x-3">
                            <input
                                type="text" value={nlQuery} onChange={(e) => setNlQuery(e.target.value)}
                                placeholder="Try: 'Show booths with negative sentiment' or 'What are the water complaints?'"
                                className="flex-1 bg-background/80 border border-border text-text-main rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-primary transition-all"
                            />
                            <button type="submit" disabled={isQuerying}
                                className="bg-primary hover:bg-primary-dark text-white rounded-xl px-6 font-bold transition-all disabled:opacity-50 shadow-glow">
                                {isQuerying ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                            </button>
                        </div>
                        {(nlResponse || isQuerying) && (
                            <div className={`mt-4 p-4 rounded-xl bg-panel/80 border text-[13px] leading-relaxed whitespace-pre-line ${isQuerying ? 'border-primary/50 text-text-muted animate-pulse' : 'border-success/50 text-text-main border-l-4 border-l-success'}`}>
                                <div className="flex items-start">
                                    <Zap size={16} className={`mr-3 mt-0.5 shrink-0 ${isQuerying ? 'text-primary' : 'text-success'}`} />
                                    <div>{isQuerying ? "Querying civic ontology graph..." : nlResponse}</div>
                                </div>
                            </div>
                        )}
                    </form>
                </div>

                {/* Right: Live Alerts */}
                <div className="glass-panel p-6 flex flex-col overflow-hidden">
                    <h3 className="text-sm font-bold text-text-main mb-4 flex items-center uppercase tracking-wider">
                        <Briefcase className="mr-3 text-primary-light" size={16} /> Critical Booth Alerts
                    </h3>
                    <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                        {criticalBooths.length > 0 ? criticalBooths.slice(0, 8).map((b: any) => (
                            <div key={b.id} className="p-3 rounded-xl bg-danger/5 border border-danger/20 hover:border-danger/40 transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="text-[10px] font-black text-danger uppercase">{b.constituency}</span>
                                    <span className="text-[10px] bg-danger/20 text-danger px-1.5 py-0.5 rounded font-bold">{b.sentiment}%</span>
                                </div>
                                <div className="text-xs font-bold text-text-main">{b.name}</div>
                                <div className="text-[10px] text-text-muted mt-1">Top Issue: {b.top_issue} | {b.unresolved} unresolved</div>
                            </div>
                        )) : (
                            <div className="text-xs text-text-muted text-center py-8">
                                <Globe className="mx-auto mb-2 opacity-30" size={24} />
                                No critical alerts detected
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

const KPICard = ({ title, value, suffix = '', icon, color, loading }: any) => (
    <div className="glass-panel p-5 border-b-2 border-transparent hover:border-primary transition-all group">
        <div className="flex justify-between items-start mb-3">
            <div className={`p-2 rounded-xl bg-panel group-hover:bg-primary/10 transition-colors ${color}`}>{icon}</div>
            <span className="text-[9px] bg-background border border-border px-2 py-0.5 rounded uppercase font-bold text-text-muted">Live</span>
        </div>
        <div className="text-3xl font-black text-text-main tracking-tight">
            {loading ? <Loader2 className="animate-spin text-primary" size={24} /> : `${value}${suffix}`}
        </div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted/60">{title}</span>
    </div>
);

const MiniStat = ({ label, value }: any) => (
    <div className="bg-panel/40 border border-border/40 rounded-xl px-4 py-3 flex justify-between items-center">
        <span className="text-[10px] font-bold text-text-muted uppercase tracking-tight">{label}</span>
        <span className="text-sm font-black text-text-main">{value}</span>
    </div>
);
