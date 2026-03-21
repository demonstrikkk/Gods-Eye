import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { OntologyGraph } from '../components/OntologyGraph';
import { Loader2, Network } from 'lucide-react';

const fetchOntologyGraph = async () => {
    // Limits: 5 booths, 150 citizens to maintain browser performance while looking impressive
    const { data } = await apiClient.get('/data/graph/ontology?booths=5&citizens=150');
    return data.data;
};

export const OntologyDashboard: React.FC = () => {
    const { data: graphData, isLoading } = useQuery({
        queryKey: ['ontology-graph'],
        queryFn: fetchOntologyGraph,
        refetchInterval: 60000, // Refresh every minute
    });

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-center mb-4">
                <Network className="mr-3 text-primary-light" size={24} />
                <div>
                    <h1 className="text-2xl font-black text-text-main tracking-tight">Ontology Intelligence Engine</h1>
                    <p className="text-xs text-text-muted uppercase tracking-widest mt-0.5">Live neural projection of civic connections</p>
                </div>
            </div>

            <div className="glass-panel flex-1 relative overflow-hidden flex flex-col items-center justify-center p-0 border-primary/20 shadow-[0_0_40px_rgba(59,130,246,0.1)]">
                <div className="absolute inset-0 opacity-[0.02] pointer-events-none bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:20px_20px]"></div>
                
                {isLoading || !graphData ? (
                    <div className="flex flex-col items-center justify-center text-primary z-10">
                        <Loader2 className="animate-spin mb-4" size={48} />
                        <span className="font-mono text-xs uppercase tracking-[0.3em] font-bold">Synthesizing Data Graph...</span>
                    </div>
                ) : (
                    <OntologyGraph data={graphData} />
                )}
            </div>
        </div>
    );
};
