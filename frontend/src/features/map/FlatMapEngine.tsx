import React, { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, ZoomControl, useMap } from 'react-leaflet';
import { useQuery } from '@tanstack/react-query';
import 'leaflet/dist/leaflet.css';
import {
  fetchSentimentHeatmap, fetchEvents, fetchFires, fetchEarthquakes, fetchNews,
} from '@/services/api';
import { useAppStore } from '@/store';
import { useLastUpdated } from '@/hooks/useLastUpdated';

const sentColor = (s: number) => s < 35 ? '#ef4444' : s < 55 ? '#f59e0b' : '#10b981';

// Ensures Leaflet repaints correctly after React mounts it
function MapResizer() {
  const map = useMap();
  useEffect(() => {
    // Multiple delays to handle flex/absolute sizing race conditions
    const t1 = setTimeout(() => map.invalidateSize(), 100);
    const t2 = setTimeout(() => map.invalidateSize(), 400);
    const onResize = () => map.invalidateSize();
    window.addEventListener('resize', onResize);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      window.removeEventListener('resize', onResize);
    };
  }, [map]);
  return null;
}

export const FlatMapEngine: React.FC = () => {
  const { activeLayers, setSelected, setSidebarTab } = useAppStore();

  const { data: heatmap = [], dataUpdatedAt: hmAt } = useQuery({
    queryKey: ['heatmap'], queryFn: fetchSentimentHeatmap, refetchInterval: 60_000,
  });
  const { data: events = [] } = useQuery({
    queryKey: ['events'], queryFn: fetchEvents, refetchInterval: 120_000, enabled: activeLayers.has('events'),
  });
  const { data: firesRaw } = useQuery({
    queryKey: ['fires'], queryFn: fetchFires, refetchInterval: 120_000, enabled: activeLayers.has('fires'),
  });
  const { data: quakes = [] } = useQuery({
    queryKey: ['earthquakes'], queryFn: fetchEarthquakes, refetchInterval: 120_000, enabled: activeLayers.has('earthquakes'),
  });

  const fires = useMemo(() => firesRaw?.hotspots ?? (Array.isArray(firesRaw) ? firesRaw : []), [firesRaw]);
  const lastUpdated = useLastUpdated(hmAt);

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#050505', overflow: 'hidden' }}>
      <MapContainer
        center={[22.5, 80.5]}
        zoom={5}
        style={{ width: '100%', height: '100%', background: '#050505' }}
        zoomControl={false}
      >
        <MapResizer />
        <TileLayer
          attribution='© <a href="https://carto.com/">CARTO</a> © <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        <ZoomControl position="bottomright" />

        {/* Sentiment Heatmap — Intricate detailed bubbles */}
        {activeLayers.has('sentiment') && Array.isArray(heatmap) && heatmap.map((p: any) => (
          <CircleMarker
            key={p.id}
            center={[p.lat, p.lng]}
            radius={6 + (p.population ?? 5000) / 15000}
            pathOptions={{
              fillColor: sentColor(p.sentiment),
              color: '#ffffff',
              fillOpacity: 0.4,
              weight: 0.8,
              className: 'sentinel-pulse'
            }}
            eventHandlers={{
              click: () => { setSelected(p.id, 'booth'); setSidebarTab('booths'); },
            }}
          >
            <Popup className="intricate-popup">
              <div className="p-1 space-y-2">
                <div className="flex justify-between items-center border-b border-zinc-800 pb-1">
                  <span className="font-bold text-zinc-100 text-sm tracking-tight">{p.name}</span>
                  <span className="text-[10px] font-mono text-zinc-500 uppercase">{p.id}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
                  <span className="text-zinc-500">Sentiment</span>
                  <span className="font-bold tabular-nums" style={{ color: sentColor(p.sentiment) }}>{p.sentiment}%</span>
                  <span className="text-zinc-500">Population</span>
                  <span className="text-zinc-300 tabular-nums">{p.population?.toLocaleString()}</span>
                  <span className="text-zinc-500">Top Issue</span>
                  <span className="text-blue-400 font-medium">{p.top_issue}</span>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Geopolitical Events — Strategic Marker Icons */}
        {activeLayers.has('events') && Array.isArray(events) && events.map((e: any) => (
          e.lat && e.lng && (
            <CircleMarker
              key={e.id}
              center={[e.lat, e.lng]}
              radius={7}
              pathOptions={{ fillColor: '#a78bfa', color: '#8b5cf6', fillOpacity: 0.8, weight: 2 }}
            >
              <Popup>
                <div className="p-1 space-y-1">
                  <div className="text-[10px] uppercase font-bold text-purple-400 tracking-wider">GEO-EVENT</div>
                  <div className="text-xs font-bold text-white">{e.title}</div>
                  <div className="text-[10px] text-zinc-400">{e.source} · {e.date}</div>
                </div>
              </Popup>
            </CircleMarker>
          )
        ))}

        {/* Fires — Heat markers */}
        {activeLayers.has('fires') && Array.isArray(fires) && fires.map((f: any, i: number) => (
          f.lat && f.lng && (
            <CircleMarker
              key={i}
              center={[f.lat, f.lng]}
              radius={4}
              pathOptions={{ fillColor: '#fb7185', color: '#f43f5e', fillOpacity: 0.9, weight: 1 }}
            />
          )
        ))}

        {/* Earthquakes — Seismic Rings */}
        {activeLayers.has('earthquakes') && Array.isArray(quakes) && quakes.map((q: any) => (
          q.lat && q.lng && (
            <CircleMarker
              key={q.id}
              center={[q.lat, q.lng]}
              radius={(q.magnitude ?? 3) * 4}
              pathOptions={{ fillColor: '#fcd34d', color: '#fbbf24', fillOpacity: 0.2, weight: 1.5, dashArray: '4, 4' }}
            >
              <Popup>
                <div className="text-xs">
                  <div className="font-bold text-yellow-400">M{q.magnitude} SEISMIC EVENT</div>
                  <div className="text-zinc-300">{q.location}</div>
                  <div className="text-[10px] text-zinc-500 mt-1 italic">Depth: {q.depth}km</div>
                </div>
              </Popup>
            </CircleMarker>
          )
        ))}
      </MapContainer>

      {/* Decorative corners for gov look */}
      <div className="absolute top-0 left-0 w-16 h-16 border-t border-l border-zinc-700/20 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-16 h-16 border-b border-r border-zinc-700/20 pointer-events-none" />
      
      {/* Updated badge */}
      <div className="absolute bottom-3 left-3 z-[400] text-[10px] font-mono text-zinc-500 bg-black/60 border border-zinc-800 px-2 py-1 rounded-md backdrop-blur-sm">
        Updated {lastUpdated}
      </div>
    </div>
  );
};
