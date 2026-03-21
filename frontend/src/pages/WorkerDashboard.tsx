import { useQuery } from '@tanstack/react-query';
import { Users, Target, MapPin, Loader2, Award, CheckCircle, Clock, AlertTriangle, Activity } from 'lucide-react';
import { apiClient } from '../services/api';

const fetchWorkers = async () => {
    const { data } = await apiClient.get('/data/workers');
    return data;
};

export const WorkerDashboard: React.FC = () => {
    const { data, isLoading } = useQuery({
        queryKey: ['workers'],
        queryFn: fetchWorkers,
        refetchInterval: 30000,
    });

    const workers = data?.data || [];
    const onlineCount = data?.online || 0;

    const avgPerformance = workers.length > 0
        ? Math.round(workers.reduce((a: number, w: any) => a + w.performance_score, 0) / workers.length)
        : 0;

    const totalHouseholds = workers.reduce((a: number, w: any) => a + w.daily_households_visited, 0);

    return (
        <div className="space-y-6 bg-background p-2">
            {/* Header */}
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center space-x-4">
                    <div className="bg-success/20 p-3 rounded-2xl border border-success/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                        <Users className="text-success" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-text-main tracking-tighter uppercase">Field Worker Operations</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono tracking-[0.2em] uppercase">
                            <Activity size={12} className="text-success" />
                            <span>{workers.length} Workers Deployed // {onlineCount} Online Now</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <WorkerStat title="Total Workers" value={workers.length} icon={<Users size={18} />} color="text-primary-light" />
                <WorkerStat title="Online Now" value={onlineCount} icon={<Target size={18} />} color="text-success" />
                <WorkerStat title="Avg Performance" value={`${avgPerformance}%`} icon={<Award size={18} />} color="text-warning" />
                <WorkerStat title="Households Today" value={totalHouseholds.toLocaleString()} icon={<MapPin size={18} />} color="text-primary-light" />
            </div>

            {/* Worker Table */}
            <div className="glass-panel p-6">
                <div className="flex items-center justify-between mb-6 border-b border-border/30 pb-4">
                    <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest">Active Worker Roster</h3>
                    <span className="text-[10px] font-mono text-success">{onlineCount}/{workers.length} Online</span>
                </div>

                {isLoading ? (
                    <div className="flex items-center justify-center py-12"><Loader2 className="animate-spin text-primary" size={32} /></div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-[10px] font-bold text-text-muted uppercase tracking-widest border-b border-border/30">
                                    <th className="text-left pb-3 px-2">Worker</th>
                                    <th className="text-left pb-3 px-2">Role</th>
                                    <th className="text-left pb-3 px-2">Booth</th>
                                    <th className="text-center pb-3 px-2">Status</th>
                                    <th className="text-center pb-3 px-2">Tasks</th>
                                    <th className="text-center pb-3 px-2">Performance</th>
                                    <th className="text-center pb-3 px-2">Households</th>
                                    <th className="text-right pb-3 px-2">Last Check-in</th>
                                </tr>
                            </thead>
                            <tbody className="text-xs">
                                {workers.slice(0, 25).map((worker: any) => (
                                    <tr key={worker.id} className="border-b border-border/20 hover:bg-panel/40 transition-colors">
                                        <td className="py-3 px-2">
                                            <div className="font-bold text-text-main">{worker.name}</div>
                                            <div className="text-[10px] text-text-muted font-mono mt-0.5">{worker.id}</div>
                                        </td>
                                        <td className="py-3 px-2 text-text-muted">{worker.role}</td>
                                        <td className="py-3 px-2 text-text-muted font-mono text-[10px]">{worker.assigned_booth}</td>
                                        <td className="py-3 px-2 text-center">
                                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded inline-flex items-center ${worker.status === 'Online' ? 'bg-success/20 text-success' :
                                                    worker.status === 'Offline' ? 'bg-danger/20 text-danger' :
                                                        'bg-warning/20 text-warning'
                                                }`}>
                                                <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${worker.status === 'Online' ? 'bg-success animate-pulse' :
                                                        worker.status === 'Offline' ? 'bg-danger' : 'bg-warning'
                                                    }`}></span>
                                                {worker.status}
                                            </span>
                                        </td>
                                        <td className="py-3 px-2 text-center">
                                            <span className="text-text-main font-bold">{worker.tasks_completed}</span>
                                            <span className="text-text-muted">/{worker.tasks_assigned}</span>
                                        </td>
                                        <td className="py-3 px-2 text-center">
                                            <span className={`font-bold ${worker.performance_score >= 80 ? 'text-success' : worker.performance_score >= 60 ? 'text-warning' : 'text-danger'}`}>
                                                {worker.performance_score}%
                                            </span>
                                        </td>
                                        <td className="py-3 px-2 text-center text-text-main font-bold">{worker.daily_households_visited}</td>
                                        <td className="py-3 px-2 text-right text-[10px] text-text-muted font-mono">
                                            {new Date(worker.last_checkin).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Bottom Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <AlertCard icon={<CheckCircle size={16} />} color="text-success border-success/20 bg-success/5" title="High Performers" count={workers.filter((w: any) => w.performance_score >= 80).length} label="Workers above 80% score" />
                <AlertCard icon={<Clock size={16} />} color="text-warning border-warning/20 bg-warning/5" title="On Leave" count={workers.filter((w: any) => w.status === 'On Leave').length} label="Workers currently on leave" />
                <AlertCard icon={<AlertTriangle size={16} />} color="text-danger border-danger/20 bg-danger/5" title="Low Performers" count={workers.filter((w: any) => w.performance_score < 50).length} label="Workers below 50% score" />
            </div>
        </div>
    );
};

const WorkerStat = ({ title, value, icon, color }: any) => (
    <div className="glass-panel p-5 group hover:border-primary/30 transition-all">
        <div className="flex items-center justify-between mb-3">
            <div className={`p-2 rounded-xl bg-panel ${color}`}>{icon}</div>
            <span className="text-[9px] bg-background border border-border px-2 py-0.5 rounded uppercase font-bold text-text-muted">Live</span>
        </div>
        <div className="text-2xl font-black text-text-main tracking-tight">{value}</div>
        <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted/60">{title}</span>
    </div>
);

const AlertCard = ({ icon, color, title, count, label }: any) => (
    <div className={`glass-panel p-4 border ${color} flex items-center space-x-4`}>
        <div className={`p-2 rounded-xl ${color}`}>{icon}</div>
        <div>
            <div className="text-xs font-bold text-text-main">{title}: <span className="text-lg font-black">{count}</span></div>
            <div className="text-[10px] text-text-muted">{label}</div>
        </div>
    </div>
);
