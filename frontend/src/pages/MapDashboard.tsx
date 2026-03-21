import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, CircleMarker, Popup, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Activity, Globe, Zap, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';

const fetchMapData = async () => {
    const { data } = await apiClient.get('/data/map');
    return data.data;
};

const getSentimentColor = (sentiment: number) => {
    if (sentiment < 35) return '#ef4444';
    if (sentiment < 50) return '#f59e0b';
    return '#10b981';
};

export const MapDashboard: React.FC = () => {
    const { data: points, isLoading } = useQuery({
        queryKey: ['map-data'],
        queryFn: fetchMapData,
        refetchInterval: 60000,
    });

    return (
        <div className="h-[calc(100vh-100px)] flex flex-col space-y-4 bg-background p-2">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

            {/* Header */}
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center space-x-3">
                    <div className="bg-primary/20 p-2 rounded-lg border border-primary/30">
                        <Globe className="text-primary-light animate-pulse" size={20} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-text-main tracking-tight uppercase">Civic Intelligence Map</h2>
                        <div className="flex items-center space-x-2 text-[10px] text-text-muted font-mono uppercase tracking-widest">
                            <span className="flex items-center"><span className="w-1.5 h-1.5 rounded-full bg-success mr-1"></span> {points?.length ?? '...'} Booths Mapped</span>
                            <span className="mx-2">|</span>
                            <span>Sentiment: Real-Time</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <SignalBadge label="Critical" color="bg-danger" />
                    <SignalBadge label="Watch" color="bg-warning" />
                    <SignalBadge label="Stable" color="bg-success" />
                </div>
            </div>

            {/* Map */}
            <div className="flex-1 min-h-[600px] glass-panel relative z-0 rounded-2xl overflow-hidden border border-border shadow-[0_0_50px_rgba(0,0,0,0.8)]">
                {isLoading && (
                    <div className="absolute inset-0 z-[500] bg-background/80 flex items-center justify-center">
                        <Loader2 className="animate-spin text-primary" size={32} />
                    </div>
                )}
                <MapContainer
                    center={[22.0, 78.0]}
                    zoom={5}
                    style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0, backgroundColor: '#050505' }}
                    zoomControl={false}
                >
                    <TileLayer
                        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    />
                    <ZoomControl position="bottomright" />

                    {points?.map((point: any) => (
                        <CircleMarker
                            key={point.id}
                            center={[point.lat, point.lng]}
                            radius={6 + (point.population / 80)}
                            pathOptions={{
                                fillColor: getSentimentColor(point.sentiment),
                                color: getSentimentColor(point.sentiment),
                                weight: 1,
                                fillOpacity: 0.5,
                            }}
                        >
                            <Popup>
                                <div className="p-4 min-w-[260px] bg-panel/95 backdrop-blur-xl border border-border rounded-xl text-text-main">
                                    <div className="flex justify-between items-center mb-3">
                                        <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase" style={{ backgroundColor: `${getSentimentColor(point.sentiment)}20`, color: getSentimentColor(point.sentiment) }}>
                                            {point.sentiment_label}
                                        </span>
                                        <span className="text-[10px] font-mono text-text-muted">{point.id}</span>
                                    </div>
                                    <h3 className="text-sm font-bold mb-1">{point.name}</h3>
                                    <p className="text-[11px] text-text-muted mb-3">{point.constituency}</p>
                                    <div className="grid grid-cols-3 gap-2 border-t border-border pt-3">
                                        <div className="text-center">
                                            <div className="text-[9px] text-text-muted uppercase">Sentiment</div>
                                            <div className="text-sm font-bold" style={{ color: getSentimentColor(point.sentiment) }}>{point.sentiment}%</div>
                                        </div>
                                        <div className="text-center">
                                            <div className="text-[9px] text-text-muted uppercase">Population</div>
                                            <div className="text-sm font-bold text-text-main">{point.population}</div>
                                        </div>
                                        <div className="text-center">
                                            <div className="text-[9px] text-text-muted uppercase">Key Voters</div>
                                            <div className="text-sm font-bold text-primary-light">{point.key_voters}</div>
                                        </div>
                                    </div>
                                    <div className="mt-3 p-2 bg-background/50 rounded-lg border border-border/50">
                                        <div className="text-[9px] text-text-muted uppercase mb-1">Top Issue</div>
                                        <div className="text-xs font-bold text-warning">{point.top_issue}</div>
                                        <div className="text-[10px] text-text-muted mt-1">{point.unresolved} unresolved complaints</div>
                                    </div>
                                </div>
                            </Popup>
                        </CircleMarker>
                    ))}
                </MapContainer>

                {/* Intelligence Brief Overlay */}
                <div className="absolute top-4 right-4 z-[400] w-72 pointer-events-none">
                    <div className="glass-panel p-4 pointer-events-auto border-primary/20 max-h-[400px] overflow-y-auto">
                        <div className="flex items-center justify-between mb-4 border-b border-border pb-2">
                            <h3 className="text-xs font-bold text-primary-light uppercase tracking-widest flex items-center">
                                <Activity size={12} className="mr-2" /> Booth Intelligence
                            </h3>
                            <span className="text-[10px] bg-primary/20 text-primary-light px-2 py-0.5 rounded">LIVE</span>
                        </div>
                        <div className="space-y-2">
                            {points?.filter((p: any) => p.sentiment < 40).slice(0, 6).map((p: any) => (
                                <div key={p.id} className="p-2 rounded bg-danger/5 border border-danger/20 text-[11px]">
                                    <div className="font-bold text-danger">{p.constituency} — {p.name}</div>
                                    <div className="text-text-muted mt-1">Sentiment: {p.sentiment}% | Issue: {p.top_issue}</div>
                                </div>
                            ))}
                            {(!points || points.filter((p: any) => p.sentiment < 40).length === 0) && (
                                <div className="text-[11px] text-text-muted text-center py-4">No critical alerts</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Legend */}
                <div className="absolute bottom-4 left-4 z-[400] glass-panel px-4 py-2 pointer-events-auto flex items-center space-x-6">
                    <LegendItem label="Critical (<35)" color="bg-danger" />
                    <LegendItem label="Watch (35-50)" color="bg-warning" />
                    <LegendItem label="Stable (>50)" color="bg-success" />
                    <div className="h-4 w-px bg-border mx-2"></div>
                    <div className="flex items-center text-[10px] font-mono text-primary-light">
                        <Zap size={12} className="mr-1 animate-pulse" /> {points?.length ?? 0} NODES
                    </div>
                </div>
            </div>
        </div>
    );
};

const SignalBadge = ({ label, color }: { label: string, color: string }) => (
    <div className={`flex items-center px-2 py-1 rounded border border-border bg-panel shadow-inner`}>
        <span className={`w-1.5 h-1.5 rounded-full ${color} mr-2`}></span>
        <span className="text-[10px] font-bold text-text-muted uppercase tracking-tighter">{label}</span>
    </div>
);

const LegendItem = ({ label, color }: { label: string, color: string }) => (
    <div className="flex items-center space-x-2">
        <span className={`w-2 h-2 rounded-full ${color}`}></span>
        <span className="text-[10px] text-text-muted font-bold uppercase">{label}</span>
    </div>
);
