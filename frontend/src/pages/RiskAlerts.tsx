import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ShieldAlert, Zap, Clock, MapPin, Search, ShieldCheck, ArrowUpRight, Activity, Bell, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';

const fetchAlerts = async () => {
    const [complaintsRes, boothsRes] = await Promise.all([
        apiClient.get('/data/complaints?sentiment=Negative&limit=20'),
        apiClient.get('/data/map'),
    ]);
    const complaints = complaintsRes.data.data;
    const booths = boothsRes.data.data;
    const criticalBooths = booths.filter((b: any) => b.sentiment < 40);

    // Generate alerts from real negative complaints + critical booths
    const alerts = complaints.slice(0, 8).map((c: any, i: number) => {
        const booth = booths.find((b: any) => b.id === c.booth_id);
        return {
            id: `ALT-${i + 1}`,
            type: c.sentiment_score < 25 ? 'Critical' : 'Warning',
            area: booth?.constituency || 'Unknown',
            booth: booth?.name || c.booth_id,
            issue: c.issue_category,
            text: c.text,
            time: getTimeAgo(c.timestamp),
            score: Math.round(100 - c.sentiment_score),
        };
    });

    return { alerts, criticalBooths, totalNegative: complaints.length };
};

function getTimeAgo(timestamp: string): string {
    const diff = Date.now() - new Date(timestamp).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return `${Math.floor(diff / 60000)}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

export const RiskAlerts: React.FC = () => {
    const { data, isLoading } = useQuery({
        queryKey: ['risk-alerts'],
        queryFn: fetchAlerts,
        refetchInterval: 30000,
    });

    const alerts = data?.alerts || [];
    const criticalBooths = data?.criticalBooths || [];

    return (
        <div className="space-y-6 bg-background p-2">
            {/* Header */}
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center space-x-4">
                    <div className="bg-danger/20 p-3 rounded-2xl border border-danger/30 shadow-[0_0_20px_rgba(239,68,68,0.2)] animate-pulse">
                        <ShieldAlert className="text-danger" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-text-main tracking-tighter uppercase">Risk & Incident Alerts</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono tracking-[0.2em] uppercase">
                            <Activity size={12} className="text-danger" />
                            <span>Sentinel Mode: Active // {alerts.length} Incidents Open</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center space-x-3">
                    <button className="bg-danger hover:bg-red-700 text-white px-6 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center">
                        <Bell size={18} className="mr-2" /> Acknowledge All
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Alert Stream */}
                <div className="lg:col-span-2 space-y-4">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-16"><Loader2 className="animate-spin text-primary" size={32} /></div>
                    ) : alerts.map((alert: any) => (
                        <div key={alert.id} className="glass-panel p-6 border-l-4 border-l-danger hover:scale-[1.005] transition-transform cursor-pointer group relative overflow-hidden">
                            {alert.type === 'Critical' && (
                                <div className="absolute top-0 right-0 w-32 h-32 bg-danger/5 blur-[40px] rounded-full -translate-y-1/2 translate-x-1/2"></div>
                            )}
                            <div className="flex justify-between items-start relative z-10">
                                <div className="flex items-start space-x-4">
                                    <div className={`p-3 rounded-xl bg-background border ${alert.type === 'Critical' ? 'border-danger/30 text-danger' : 'border-warning/30 text-warning'}`}>
                                        <AlertTriangle size={24} />
                                    </div>
                                    <div>
                                        <div className="flex items-center space-x-2">
                                            <span className={`text-[10px] font-black px-2 py-0.5 rounded uppercase ${alert.type === 'Critical' ? 'bg-danger/20 text-danger' : 'bg-warning/20 text-warning'}`}>{alert.type}</span>
                                            <span className="text-[10px] font-mono text-text-muted">ID: {alert.id}</span>
                                        </div>
                                        <h3 className="text-lg font-bold text-text-main mt-1 group-hover:text-danger transition-colors">{alert.issue} — {alert.booth}</h3>
                                        <div className="flex items-center space-x-4 mt-2">
                                            <div className="flex items-center text-[11px] text-text-muted"><MapPin size={12} className="mr-1" /> {alert.area}</div>
                                            <div className="flex items-center text-[11px] text-text-muted"><Clock size={12} className="mr-1" /> {alert.time}</div>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-[10px] uppercase font-bold text-text-muted tracking-widest opacity-50">Threat Score</div>
                                    <div className={`text-3xl font-black ${alert.score > 70 ? 'text-danger' : 'text-warning'}`}>{alert.score}</div>
                                </div>
                            </div>
                            <div className="mt-4 p-4 bg-background/40 border border-border/40 rounded-xl relative z-10">
                                <div className="text-[10px] font-black uppercase text-primary-light mb-1 flex items-center tracking-widest">
                                    <Zap size={10} className="mr-1" /> Citizen Report:
                                </div>
                                <p className="text-xs text-text-muted leading-relaxed italic">"{alert.text}"</p>
                            </div>
                            <div className="mt-4 flex justify-end items-center space-x-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button className="text-[10px] font-bold text-text-muted uppercase hover:text-text-main px-3 py-1.5 border border-border rounded-lg">Silence</button>
                                <button className="text-[10px] font-bold text-white bg-danger/80 py-1.5 px-4 rounded-lg flex items-center">
                                    Deploy Response <ArrowUpRight size={12} className="ml-1" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Right Panel */}
                <div className="lg:col-span-1 space-y-6">
                    {/* Integrity Gauge */}
                    <div className="glass-panel p-6 border-danger/20 bg-danger/[0.02]">
                        <h3 className="text-xs font-bold text-text-main uppercase tracking-widest mb-6 flex items-center">
                            <ShieldCheck size={14} className="mr-2 text-success" /> Booth Vulnerability Index
                        </h3>
                        <div className="flex flex-col items-center text-center space-y-4 py-4">
                            <div className="relative w-36 h-36 border-8 border-border rounded-full flex items-center justify-center">
                                <div className="absolute inset-0 border-8 border-danger rounded-full border-t-transparent -rotate-45"></div>
                                <div>
                                    <div className="text-4xl font-black text-danger leading-none">{criticalBooths.length}</div>
                                    <div className="text-[9px] font-bold uppercase text-text-muted mt-1">Critical Booths</div>
                                </div>
                            </div>
                            <p className="text-[11px] text-text-muted leading-relaxed px-4">
                                {criticalBooths.length} booths are below the 40% sentiment threshold. These require immediate outreach.
                            </p>
                        </div>
                    </div>

                    {/* Urgent Directives */}
                    <div className="glass-panel p-6">
                        <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest mb-4">Auto-Generated Directives</h3>
                        <div className="space-y-3">
                            {criticalBooths.slice(0, 3).map((b: any) => (
                                <div key={b.id} className="p-3 bg-danger/5 border border-danger/20 rounded-xl text-xs text-text-main flex items-start">
                                    <div className="w-1.5 h-1.5 rounded-full bg-danger mt-1.5 mr-3 shrink-0"></div>
                                    Deploy awareness campaign for <span className="text-warning font-bold mx-1">{b.top_issue}</span> in {b.name}, {b.constituency}. Sentiment at <span className="text-danger font-bold ml-1">{b.sentiment}%</span>.
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
