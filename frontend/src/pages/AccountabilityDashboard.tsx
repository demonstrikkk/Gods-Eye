import { useQuery } from '@tanstack/react-query';
import { CheckCircle, Clock, Loader2, Hammer, MapPin, IndianRupee, Eye } from 'lucide-react';
import { apiClient } from '../services/api';
import { BeforeAfterSlider } from '../components/BeforeAfterSlider';

const fetchProjects = async () => {
    const { data } = await apiClient.get('/data/projects');
    return data.data;
};

const STATUS_COLORS: Record<string, string> = {
    Completed: 'text-success bg-success/20 border-success/30',
    'In Progress': 'text-warning bg-warning/20 border-warning/30',
    Pending: 'text-text-muted bg-panel border-border',
};

export const AccountabilityDashboard: React.FC = () => {
    const { data: projects, isLoading } = useQuery({
        queryKey: ['projects'],
        queryFn: fetchProjects,
        refetchInterval: 60000,
    });

    const completed = projects?.filter((p: any) => p.status === 'Completed') || [];
    const inProgress = projects?.filter((p: any) => p.status === 'In Progress') || [];
    const pending = projects?.filter((p: any) => p.status === 'Pending') || [];
    const totalBudget = projects?.reduce((a: number, p: any) => a + p.budget, 0) || 0;

    return (
        <div className="space-y-6 bg-background p-2">
            {/* Header */}
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center space-x-4">
                    <div className="bg-warning/20 p-3 rounded-2xl border border-warning/30 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
                        <Hammer className="text-warning" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-text-main tracking-tighter uppercase">Micro-Accountability Engine</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono tracking-[0.2em] uppercase">
                            <Eye size={12} className="text-warning" />
                            <span>Before/After Proof System // {projects?.length ?? '...'} Projects Tracked</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <ProjStat title="Total Projects" value={projects?.length ?? '--'} icon={<Hammer size={18} />} color="text-primary-light" />
                <ProjStat title="Completed" value={completed.length} icon={<CheckCircle size={18} />} color="text-success" />
                <ProjStat title="In Progress" value={inProgress.length} icon={<Clock size={18} />} color="text-warning" />
                <ProjStat title="Total Budget" value={`₹${(totalBudget / 10000000).toFixed(1)}Cr`} icon={<IndianRupee size={18} />} color="text-primary-light" />
            </div>

            {/* Project Cards */}
            <div className="glass-panel p-6">
                <div className="flex items-center justify-between mb-6 border-b border-border/30 pb-4">
                    <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest">Infrastructure Project Tracker</h3>
                    <div className="flex space-x-2">
                        <span className="text-[10px] bg-success/20 text-success px-2 py-0.5 rounded border border-success/30">{completed.length} Done</span>
                        <span className="text-[10px] bg-warning/20 text-warning px-2 py-0.5 rounded border border-warning/30">{inProgress.length} Active</span>
                        <span className="text-[10px] bg-panel text-text-muted px-2 py-0.5 rounded border border-border">{pending.length} Pending</span>
                    </div>
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center py-12"><Loader2 className="animate-spin text-primary" size={32} /></div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {projects?.map((proj: any) => (
                            <div key={proj.id} className="bg-background/40 border border-border/50 rounded-xl p-5 hover:border-primary/40 transition-all group relative overflow-hidden">
                                {proj.status === 'Completed' && (
                                    <div className="absolute top-0 right-0 w-20 h-20 bg-success/5 blur-[30px] rounded-full -translate-y-1/2 translate-x-1/2"></div>
                                )}
                                <div className="flex justify-between items-start mb-3 relative z-10">
                                    <div>
                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${STATUS_COLORS[proj.status]}`}>{proj.status}</span>
                                        <h4 className="text-sm font-bold text-text-main mt-2 group-hover:text-primary-light transition-colors">{proj.name}</h4>
                                    </div>
                                    <span className="text-xs font-black text-primary-light">{proj.budget_display}</span>
                                </div>

                                <div className="grid grid-cols-2 gap-3 text-[10px] text-text-muted mb-4 relative z-10">
                                    <div className="flex items-center"><MapPin size={10} className="mr-1" /> {proj.street}, {proj.ward_name}</div>
                                    <div className="flex items-center"><Clock size={10} className="mr-1" /> {proj.start_date}</div>
                                </div>

                                {/* Before / After Sentiment Slider */}
                                {proj.status === 'Completed' ? (
                                    <BeforeAfterSlider 
                                        project={proj}
                                        beforeImage="https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=800"
                                        afterImage="https://images.unsplash.com/photo-1574007557239-acf6eeff2c68?auto=format&fit=crop&q=80&w=800"
                                    />
                                ) : (
                                    <div className="mt-3 text-[10px] text-text-muted">
                                        <span className="text-primary-light font-bold">{proj.affected_residents}</span> residents affected in <span className="text-warning">{proj.street}</span>
                                    </div>
                                )}

                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const ProjStat = ({ title, value, icon, color }: any) => (
    <div className="glass-panel p-5 group hover:border-primary/30 transition-all">
        <div className="flex items-center justify-between mb-3">
            <div className={`p-2 rounded-xl bg-panel ${color}`}>{icon}</div>
        </div>
        <div className="text-2xl font-black text-text-main tracking-tight">{value}</div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted/60">{title}</span>
    </div>
);
