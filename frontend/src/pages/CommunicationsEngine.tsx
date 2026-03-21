import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Send, Users, ShieldCheck, Zap, Clock, Plus, Activity, Mail, Phone, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';

const fetchCommsData = async () => {
    const [statsRes, complaintsRes] = await Promise.all([
        apiClient.get('/data/stats'),
        apiClient.get('/data/complaints?limit=10'),
    ]);
    return {
        stats: statsRes.data.data,
        complaints: complaintsRes.data.data,
    };
};

const mockCampaigns = [
    { id: 'C1', name: 'Road Repair Awareness - Ward 8', channel: 'WhatsApp', status: 'Active', reached: '1,240', conversion: '62%', sentiment_delta: '+8%', color: 'text-success' },
    { id: 'C2', name: 'Water Supply Restoration Update', channel: 'SMS', status: 'Scheduled', reached: '4,500', conversion: '--', sentiment_delta: '--', color: 'text-primary-light' },
    { id: 'C3', name: 'PM-Kisan Enrollment Drive', channel: 'Voice/IVR', status: 'Active', reached: '2,800', conversion: '34%', sentiment_delta: '+5%', color: 'text-success' },
    { id: 'C4', name: 'Mudra Yojana Outreach - Youth', channel: 'WhatsApp', status: 'Draft', reached: '--', conversion: '--', sentiment_delta: '--', color: 'text-text-muted' },
];

export const CommunicationsEngine: React.FC = () => {
    const [activeTab, setActiveTab] = useState('campaigns');
    const [messageDraft, setMessageDraft] = useState('');

    const { data, isLoading } = useQuery({
        queryKey: ['comms-data'],
        queryFn: fetchCommsData,
        refetchInterval: 30000,
    });

    const recentComplaints = data?.complaints || [];
    const stats = data?.stats;

    return (
        <div className="space-y-6 bg-background p-2 max-w-[1600px] mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center space-x-4">
                    <div className="bg-primary/20 p-3 rounded-2xl border border-primary/30 shadow-glow animate-pulse">
                        <MessageSquare className="text-primary-light" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-text-main tracking-tighter uppercase">Communications Engine</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono tracking-[0.2em] uppercase">
                            <Zap size={12} className="text-success" />
                            <span>Hyper-Local Content Delivery // Multi-Channel Outreach</span>
                        </div>
                    </div>
                </div>
                <div className="flex space-x-3">
                    <button className="bg-primary hover:bg-primary-dark text-white px-6 py-2.5 rounded-xl font-bold text-sm transition-all shadow-glow flex items-center">
                        <Plus size={18} className="mr-2" /> Start Campaign
                    </button>
                    <div className="bg-panel border border-border p-1 rounded-xl flex">
                        <TabItem label="Campaigns" active={activeTab === 'campaigns'} onClick={() => setActiveTab('campaigns')} />
                        <TabItem label="Inbox" active={activeTab === 'inbox'} onClick={() => setActiveTab('inbox')} />
                        <TabItem label="Analytics" active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')} />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    {/* Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <CommStat title="Citizens Reachable" value={stats?.total_citizens?.toLocaleString() ?? '--'} detail="Across all booths" icon={<Users size={18} />} loading={isLoading} />
                        <CommStat title="Complaints to Address" value={stats?.total_complaints?.toLocaleString() ?? '--'} detail="Multi-channel queue" icon={<Activity size={18} />} loading={isLoading} />
                        <CommStat title="Scheme Communication" value={`${stats?.total_schemes ?? '--'} Active`} detail="Enrollment awareness" icon={<ShieldCheck size={18} />} loading={isLoading} />
                    </div>

                    {/* Campaign Roster */}
                    <div className="glass-panel p-6">
                        <div className="flex items-center justify-between mb-6 border-b border-border/30 pb-4">
                            <h3 className="text-xs font-bold text-text-muted uppercase tracking-[0.2em] flex items-center">
                                <Clock size={14} className="mr-2 text-primary-light" /> Active Outreach Campaigns
                            </h3>
                        </div>
                        <div className="space-y-3">
                            {mockCampaigns.map(camp => (
                                <div key={camp.id} className="bg-background/40 border border-border/50 rounded-xl p-4 flex items-center justify-between group hover:border-primary/40 transition-all cursor-pointer">
                                    <div className="flex items-center space-x-4">
                                        <div className={`p-2 rounded-lg bg-panel ${camp.status === 'Active' ? 'shadow-[0_0_10px_rgba(16,185,129,0.2)]' : ''}`}>
                                            {camp.channel === 'WhatsApp' ? <Send size={16} className="text-success" /> : <Mail size={16} className="text-primary-light" />}
                                        </div>
                                        <div>
                                            <div className="text-sm font-bold text-text-main group-hover:text-primary-light transition-colors">{camp.name}</div>
                                            <div className="flex items-center space-x-2 mt-1">
                                                <span className="text-[10px] font-mono text-text-muted uppercase">{camp.channel}</span>
                                                <span className="text-[10px] text-text-muted">•</span>
                                                <span className={`text-[10px] font-bold uppercase ${camp.status === 'Active' ? 'text-success' : 'text-primary-light'}`}>{camp.status}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-3 gap-8 text-right pr-6">
                                        <CampaignMetric label="Reached" value={camp.reached} />
                                        <CampaignMetric label="Conv." value={camp.conversion} />
                                        <CampaignMetric label="Δ Sent." value={camp.sentiment_delta} color={camp.color} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Live Citizen Pulse */}
                <div className="lg:col-span-1 glass-panel flex flex-col h-[700px] border-primary/10">
                    <div className="p-5 border-b border-border/40 flex justify-between items-center bg-primary/5">
                        <h3 className="text-xs font-bold text-primary-light uppercase tracking-widest flex items-center">
                            Citizen Feedback Pulse <span className="ml-2 w-1.5 h-1.5 rounded-full bg-success animate-ping"></span>
                        </h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {isLoading ? (
                            <div className="flex items-center justify-center py-8"><Loader2 className="animate-spin text-primary" size={24} /></div>
                        ) : recentComplaints.map((msg: any) => (
                            <div key={msg.id} className="p-4 rounded-2xl bg-background/80 border border-border/60 hover:border-primary/30 transition-all shadow-glass">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-[10px] font-black text-text-muted uppercase tracking-tighter">{msg.citizen_name}</span>
                                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${msg.sentiment === 'Positive' ? 'bg-success/20 text-success' : msg.sentiment === 'Negative' ? 'bg-danger/20 text-danger' : 'bg-warning/20 text-warning'}`}>
                                        {msg.sentiment}
                                    </span>
                                </div>
                                <p className="text-[12px] text-text-main leading-relaxed italic">"{msg.text}"</p>
                                <div className="flex justify-between mt-3 text-[9px] text-text-muted/50 font-mono">
                                    <span>{msg.issue_category}</span>
                                    <span>{msg.language}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="p-4 bg-panel/80 border-t border-border/40 backdrop-blur-xl">
                        <div className="relative">
                            <textarea
                                value={messageDraft} onChange={(e) => setMessageDraft(e.target.value)}
                                placeholder="Type intelligence broadcast or citizen response..."
                                className="w-full min-h-[80px] bg-background/50 border border-border rounded-xl p-3 text-xs text-text-main focus:outline-none focus:border-primary transition-all resize-none"
                            />
                            <div className="absolute bottom-3 right-3 flex items-center space-x-1.5">
                                <SendButton icon={<Phone size={14} />} color="text-success" />
                                <SendButton icon={<Zap size={14} />} color="text-warning" primary />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const TabItem = ({ label, active, onClick }: any) => (
    <button onClick={onClick} className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${active ? 'bg-primary-dark/20 text-primary-light shadow-inner' : 'text-text-muted hover:text-text-main'}`}>
        {label}
    </button>
);

const CommStat = ({ title, value, detail, icon, loading }: any) => (
    <div className="glass-panel p-5 border-l-2 border-primary/20 hover:border-primary transition-colors bg-panel/20 group">
        <div className="flex items-center justify-between mb-4">
            <div className="p-2 rounded-xl bg-background border border-border/60 text-primary-light group-hover:shadow-glow transition-all">{icon}</div>
            <div className="text-[10px] font-mono text-text-muted flex items-center">LIVE <span className="ml-1.5 w-1.5 h-1.5 rounded-full bg-success"></span></div>
        </div>
        <div className="text-2xl font-black text-text-main tracking-tighter">{loading ? <Loader2 className="animate-spin text-primary" size={20} /> : value}</div>
        <div className="mt-1">
            <div className="text-[10px] font-black uppercase text-text-muted opacity-60 tracking-widest">{title}</div>
            <div className="text-[10px] font-bold text-success mt-0.5">{detail}</div>
        </div>
    </div>
);

const CampaignMetric = ({ label, value, color = 'text-text-main' }: any) => (
    <div>
        <div className="text-[9px] font-bold text-text-muted uppercase tracking-tighter mb-1 opacity-50">{label}</div>
        <div className={`text-xs font-black ${color}`}>{value}</div>
    </div>
);

const SendButton = ({ icon, color, primary }: any) => (
    <button className={`p-2 rounded-lg border transition-all ${primary ? 'bg-primary border-primary text-white shadow-glow hover:bg-primary-dark scale-110' : `bg-background border-border ${color} hover:border-primary/50`}`}>
        {icon}
    </button>
);
