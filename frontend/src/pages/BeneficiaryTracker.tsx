import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Database, AlertTriangle, UserCheck, Search, Building, Zap, Briefcase, Megaphone } from 'lucide-react';
import { apiClient } from '../services/api';

const fetchSchemes = async () => {
    const { data } = await apiClient.get('/data/schemes');
    return data.data;
};

const fetchConstituencies = async () => {
    const { data } = await apiClient.get('/data/constituencies');
    return data.data;
};

const fetchBooths = async (conId: string) => {
    const { data } = await apiClient.get(`/data/constituency/${conId}/booths`);
    return data.data;
};

// Component for a single Booth Row to handle its own scheme & gap loading
const BoothGapRow: React.FC<{ booth: any; schemeId: string; schemeName: string }> = ({ booth, schemeId, schemeName }) => {
    const { data: schemes } = useQuery({
        queryKey: ['booth-schemes', booth.id],
        queryFn: async () => {
            const { data } = await apiClient.get(`/data/booth/${booth.id}/schemes`);
            return data.schemes;
        },
    });

    const { data: gapData, isLoading: gapLoading } = useQuery({
        queryKey: ['booth-gap', booth.id, schemeId],
        queryFn: async () => {
            const { data } = await apiClient.get(`/data/booth/${booth.id}/schemes/${schemeId}/gap`);
            return data;
        },
        enabled: !!schemeId,
    });

    const enrolled = schemes?.find((s: any) => s.name === schemeName)?.enrolled || 0;
    const gap = gapData?.unenrolled_eligible || 0;

    return (
        <div className="bg-panel/30 border border-border/50 rounded-xl p-4 flex items-center justify-between hover:bg-panel/50 hover:border-text-muted transition-all">
            <div className="flex-1">
                <div className="text-sm font-bold text-text-main flex items-center">
                    <Building size={14} className="mr-2 text-primary-light" /> Booth {booth.name}
                </div>
                <div className="text-[10px] text-text-muted mt-1 uppercase tracking-widest font-mono">
                    Total Pop: {booth.population} | Key Voters: {booth.key_voters}
                </div>
            </div>

            <div className="flex-1 flex items-center justify-center">
                <div className="text-center px-6 border-r border-border/40">
                    <div className="text-[10px] uppercase text-text-muted mb-1 font-bold tracking-widest">Enrolled</div>
                    <div className="text-xl font-black text-success flex justify-center items-center">
                        <UserCheck size={16} className="mr-1" /> {enrolled}
                    </div>
                </div>
                <div className="text-center px-6">
                    <div className="text-[10px] uppercase text-text-muted mb-1 font-bold tracking-widest text-warning">Gap Matrix (Eligible)</div>
                    <div className="text-xl font-black text-warning flex justify-center items-center">
                        {gapLoading ? <Briefcase size={16} className="animate-spin mr-1" /> : <AlertTriangle size={16} className="mr-1" />}
                        {gapLoading ? '...' : gap}
                    </div>
                </div>
            </div>

            <div className="flex-1 flex justify-end">
                <button
                    disabled={gap === 0}
                    className="bg-primary/20 hover:bg-primary disabled:opacity-30 disabled:hover:bg-primary/20 text-white text-xs font-bold px-4 py-2 rounded border border-primary/50 transition-all flex items-center"
                    onClick={() => alert(`Launched awareness campaign via SMS/WhatsApp to ${gap} eligible citizens in Booth ${booth.name}.`)}
                >
                    <Megaphone size={14} className="mr-2" /> Target Gap
                </button>
            </div>
        </div>
    );
};

export const BeneficiaryTracker: React.FC = () => {
    const [selectedConId, setSelectedConId] = useState('CON-01');
    const [selectedSchemeId, setSelectedSchemeId] = useState('');

    const { data: schemes } = useQuery({ queryKey: ['schemes-list'], queryFn: fetchSchemes });
    const { data: constituencies } = useQuery({ queryKey: ['constituencies-list'], queryFn: fetchConstituencies });
    const { data: booths } = useQuery({
        queryKey: ['booths-list', selectedConId],
        queryFn: () => fetchBooths(selectedConId),
        enabled: !!selectedConId,
    });

    // Auto-select first scheme when loaded
    if (schemes && !selectedSchemeId) {
        setSelectedSchemeId(schemes[0].id);
    }

    const currentScheme = schemes?.find((s: any) => s.id === selectedSchemeId);

    return (
        <div className="space-y-6 bg-background p-2 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center space-x-4">
                    <div className="bg-success/10 p-3 rounded-2xl border border-success/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                        <Database className="text-success" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-text-main tracking-tighter uppercase">Beneficiary Linkage</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono tracking-[0.2em] uppercase">
                            <Zap size={12} className="text-success" />
                            <span>Scheme Gap Analysis Engine</span>
                        </div>
                    </div>
                </div>

                <div className="flex space-x-3">
                    <select
                        value={selectedConId}
                        onChange={(e) => setSelectedConId(e.target.value)}
                        className="bg-panel border border-border text-xs text-text-main px-4 py-2 rounded-xl focus:border-primary focus:outline-none max-w-[200px]"
                    >
                        {constituencies?.map((c: any) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>

                    <select
                        value={selectedSchemeId}
                        onChange={(e) => setSelectedSchemeId(e.target.value)}
                        className="bg-panel border border-border text-xs text-text-main px-4 py-2 rounded-xl focus:border-primary focus:outline-none font-bold"
                    >
                        <option value="" disabled>Select Target Scheme</option>
                        {schemes?.map((s: any) => (
                            <option key={s.id} value={s.id}>{s.name} ({s.target_segment})</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Selected Scheme Intel */}
            {currentScheme && (
                <div className="glass-panel p-6 border-success/30 bg-success/5 relative overflow-hidden">
                    <div className="absolute right-0 top-0 bottom-0 w-64 bg-gradient-to-l from-success/10 to-transparent pointer-events-none"></div>
                    <h3 className="text-lg font-black text-text-main">{currentScheme.name}</h3>
                    <p className="text-sm text-text-muted mt-2 max-w-3xl leading-relaxed">{currentScheme.description}</p>
                    <div className="mt-4 flex space-x-2">
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-panel border border-border text-text-muted">Target: {currentScheme.target_segment}</span>
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-panel border border-border text-text-muted">ID: {currentScheme.id}</span>
                    </div>
                </div>
            )}

            {/* Booth Breakdown List */}
            <div className="glass-panel p-6">
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-border/40">
                    <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest flex items-center">
                        <Search size={14} className="mr-2 text-primary-light" /> Booth-Level Gap Matrix
                    </h3>
                    <span className="text-[10px] font-black text-primary-light bg-primary/20 px-2 py-1 rounded">
                        {booths?.length || 0} Nodes Scanned
                    </span>
                </div>

                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                    {booths?.slice(0, 15)?.map((booth: any) => (
                        <BoothGapRow
                            key={booth.id}
                            booth={booth}
                            schemeId={selectedSchemeId}
                            schemeName={currentScheme?.name || ''}
                        />
                    ))}
                    {booths && booths?.length > 15 && (
                        <div className="p-4 text-center text-xs text-text-muted font-bold tracking-widest uppercase italic border border-dashed border-border/50 rounded-xl">
                            + {booths?.length - 15} more booths accessible via deep terminal dump.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
