import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { Target, Users, AlertTriangle, Search, Database, ChevronRight, Binary, Activity, Zap, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';

const SEGMENT_COLORS: Record<string, string> = {
    Youth: '#3b82f6',
    Farmer: '#10b981',
    Women: '#a855f7',
    Business: '#f59e0b',
    Senior: '#ec4899',
    General: '#6b7280',
};

const fetchConstituencies = async () => {
    const { data } = await apiClient.get('/data/constituencies');
    return data.data;
};

const fetchBooths = async (conId: string) => {
    const { data } = await apiClient.get(`/data/constituency/${conId}/booths`);
    return data.data;
};

const fetchBoothSegments = async (boothId: string) => {
    const { data } = await apiClient.get(`/data/booth/${boothId}/segments`);
    return data.segments;
};

const fetchBoothSchemes = async (boothId: string) => {
    const { data } = await apiClient.get(`/data/booth/${boothId}/schemes`);
    return data.schemes;
};

export const ConstituencyLens: React.FC = () => {
    const [selectedConId, setSelectedConId] = useState('CON-01');
    const [selectedBoothId, setSelectedBoothId] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');

    const { data: constituencies } = useQuery({
        queryKey: ['constituencies'],
        queryFn: fetchConstituencies,
    });

    const { data: booths, isLoading: boothsLoading } = useQuery({
        queryKey: ['booths', selectedConId],
        queryFn: () => fetchBooths(selectedConId),
        enabled: !!selectedConId,
    });

    const currentBooth = booths?.find((b: any) => b.id === selectedBoothId) || booths?.[0];
    const effectiveBoothId = currentBooth?.id;

    const { data: segments } = useQuery({
        queryKey: ['segments', effectiveBoothId],
        queryFn: () => fetchBoothSegments(effectiveBoothId),
        enabled: !!effectiveBoothId,
    });

    const { data: schemes } = useQuery({
        queryKey: ['schemes', effectiveBoothId],
        queryFn: () => fetchBoothSchemes(effectiveBoothId),
        enabled: !!effectiveBoothId,
    });

    const filteredBooths = booths?.filter((b: any) =>
        b.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        b.id.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    const segmentChartData = segments?.map((s: any) => ({
        ...s,
        color: SEGMENT_COLORS[s.name] || '#6b7280',
    })) || [];

    return (
        <div className="space-y-6 bg-background p-2">
            {/* Header */}
            <div className="flex items-center justify-between mb-4 px-2">
                <div className="flex items-center space-x-4">
                    <div className="bg-primary/10 p-3 rounded-2xl border border-primary/20 shadow-glow">
                        <Target className="text-primary-light" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-text-main tracking-tighter uppercase">Constituency Intelligence</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono tracking-[0.2em] uppercase">
                            <Binary size={12} className="text-primary-light" />
                            <span>Booth-Level Telemetry // Voter Segmentation Active</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center space-x-3">
                    {/* Constituency Selector */}
                    <select
                        value={selectedConId}
                        onChange={(e) => { setSelectedConId(e.target.value); setSelectedBoothId(null); }}
                        className="bg-panel border border-border text-xs text-text-main px-3 py-2.5 rounded-xl focus:outline-none focus:border-primary"
                    >
                        {constituencies?.map((c: any) => (
                            <option key={c.id} value={c.id}>{c.name} ({c.state})</option>
                        ))}
                    </select>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={14} />
                        <input
                            type="text" placeholder="Search Booth..."
                            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="bg-panel/50 border border-border text-xs text-text-main pl-9 pr-4 py-2.5 rounded-xl focus:outline-none focus:border-primary w-52 transition-all"
                        />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Booth Roster */}
                <div className="lg:col-span-1 glass-panel flex flex-col h-[700px]">
                    <div className="p-4 border-b border-border/40 flex justify-between items-center bg-panel/30">
                        <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Target Roster</span>
                        <span className="text-[10px] bg-primary/20 text-primary-light px-2 py-0.5 rounded">{filteredBooths?.length} Nodes</span>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-2">
                        {boothsLoading ? (
                            <div className="flex items-center justify-center py-12"><Loader2 className="animate-spin text-primary" size={24} /></div>
                        ) : filteredBooths?.map((booth: any) => (
                            <div
                                key={booth.id}
                                onClick={() => setSelectedBoothId(booth.id)}
                                className={`p-4 rounded-xl cursor-pointer transition-all border flex items-center justify-between group ${currentBooth?.id === booth.id
                                    ? 'bg-primary-dark/20 border-primary shadow-glow ring-1 ring-primary/20'
                                    : 'bg-background/40 border-border/50 hover:border-text-muted hover:bg-panel/30'
                                    }`}
                            >
                                <div>
                                    <div className="text-xs font-bold text-text-main group-hover:text-primary-light transition-colors">{booth.name}</div>
                                    <div className="text-[10px] text-text-muted mt-1 font-mono uppercase tracking-tighter">
                                        {booth.top_issues?.[0]?.issue || 'Stable'} | Pop: {booth.population}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-xs font-black ${booth.avg_sentiment < 40 ? 'text-danger' : (booth.avg_sentiment > 60 ? 'text-success' : 'text-warning')}`}>
                                        {booth.avg_sentiment}%
                                    </div>
                                    <ChevronRight className={`transition-transform duration-300 ${currentBooth?.id === booth.id ? 'rotate-90 text-primary-light' : 'text-text-muted opacity-0 group-hover:opacity-100'}`} size={14} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Intelligence Workspace */}
                <div className="lg:col-span-3 space-y-6">
                    {/* Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <BoothStatBox title="Avg Sentiment" value={`${currentBooth?.avg_sentiment ?? '--'}%`} icon={<Activity size={18} />} color="text-primary-light" />
                        <BoothStatBox title="Population" value={currentBooth?.population?.toLocaleString() ?? '--'} icon={<Users size={18} />} color="text-success" />
                        <BoothStatBox title="Open Issues" value={currentBooth?.unresolved_complaints ?? '--'} icon={<AlertTriangle size={18} />} color="text-danger" />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Voter Segmentation */}
                        <div className="glass-panel p-6">
                            <h3 className="text-xs font-bold text-text-muted uppercase tracking-[0.2em] mb-6 flex items-center">
                                <Database size={14} className="mr-2 text-primary-light" /> Voter Segmentation (Auto-Classified)
                            </h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="h-52">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie data={segmentChartData} innerRadius={40} outerRadius={65} paddingAngle={3} dataKey="count" stroke="none">
                                                {segmentChartData?.map((entry: any, index: number) => (
                                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                                ))}
                                            </Pie>
                                            <Tooltip contentStyle={{ backgroundColor: '#141416', border: 'none', borderRadius: '8px', fontSize: '11px' }} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="flex flex-col justify-center space-y-2.5">
                                    {segmentChartData?.map((s: any) => (
                                        <div key={s.name} className="flex items-center justify-between">
                                            <div className="flex items-center space-x-2">
                                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }}></div>
                                                <span className="text-[10px] text-text-muted font-bold uppercase">{s.name}</span>
                                            </div>
                                            <span className="text-[10px] font-mono text-text-main">{s.percentage}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Scheme Coverage */}
                        <div className="glass-panel p-6">
                            <h3 className="text-xs font-bold text-text-muted uppercase tracking-[0.2em] mb-6 flex items-center">
                                <Zap size={14} className="mr-2 text-primary-light" /> Beneficiary Linkage (Schemes)
                            </h3>
                            <div className="h-52">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={schemes?.slice(0, 6) || []} layout="vertical" margin={{ left: 10, right: 30 }}>
                                        <XAxis type="number" hide />
                                        <YAxis dataKey="name" type="category" stroke="#a1a1aa" fontSize={9} axisLine={false} tickLine={false} width={90} />
                                        <Tooltip contentStyle={{ backgroundColor: '#141416', border: '1px solid #27272a', borderRadius: '12px', fontSize: '11px' }} />
                                        <Bar dataKey="enrolled" radius={[0, 4, 4, 0]} barSize={12}>
                                            {(schemes?.slice(0, 6) || [])?.map((_: any, index: number) => (
                                                <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#3b82f6' : '#10b981'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Issue Breakdown from real data */}
                    <div className="glass-panel p-6 bg-primary/5 border-primary/20">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xs font-bold text-primary-light uppercase tracking-[0.3em] flex items-center">
                                <Zap size={14} className="mr-2 animate-pulse" /> AI-Generated Strategic Brief
                            </h3>
                        </div>
                        <div className="p-4 bg-background/60 border border-border/50 rounded-2xl">
                            <p className="text-[13px] text-text-main leading-relaxed">
                                {currentBooth ? (
                                    <>
                                        <span className={`font-black uppercase mr-2 ${currentBooth.avg_sentiment < 40 ? 'text-danger' : 'text-success'}`}>
                                            [{currentBooth.sentiment_label}]
                                        </span>
                                        Booth <span className="text-primary-light font-bold">{currentBooth.name}</span> in {currentBooth.constituency_name} has{' '}
                                        <span className="font-bold">{currentBooth.population}</span> registered voters with an average sentiment of{' '}
                                        <span className={`font-bold ${currentBooth.avg_sentiment < 40 ? 'text-danger' : 'text-success'}`}>{currentBooth.avg_sentiment}%</span>.{' '}
                                        Top issue: <span className="text-warning font-bold">{currentBooth.top_issues?.[0]?.issue}</span> ({currentBooth.top_issues?.[0]?.count} affected).{' '}
                                        There are <span className="text-danger font-bold">{currentBooth.unresolved_complaints}</span> unresolved complaints and{' '}
                                        <span className="text-primary-light font-bold">{currentBooth.key_voters}</span> identified key voters.
                                    </>
                                ) : 'Select a booth to view strategic intelligence.'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const BoothStatBox = ({ title, value, icon, color }: any) => (
    <div className="glass-panel p-5 border-l-4 border-l-border/30 hover:border-l-primary transition-all group bg-panel/20">
        <div className="flex items-center justify-between mb-4">
            <div className={`p-2 rounded-xl bg-background border border-border/60 ${color} group-hover:shadow-glow transition-all`}>{icon}</div>
        </div>
        <div className="text-2xl font-black text-text-main tracking-tighter">{value}</div>
        <div className="text-[10px] font-black uppercase text-text-muted/60 mt-1 tracking-widest">{title}</div>
    </div>
);
