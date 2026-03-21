import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, ZoomControl, useMap } from 'react-leaflet';
import { useQuery } from '@tanstack/react-query';
import 'leaflet/dist/leaflet.css';
import {
  fetchGlobalCorridors,
  fetchGlobalCountries,
  fetchGlobalOverview,
  fetchGlobalSignals,
} from '@/services/api';
import { useAppStore } from '@/store';
import { useLastUpdated } from '@/hooks/useLastUpdated';

const countryColor = (risk: number) => (risk >= 70 ? '#ef4444' : risk >= 50 ? '#f59e0b' : '#10b981');
const signalColor = (severity: string) => (severity === 'High' ? '#ef4444' : severity === 'Medium' ? '#38bdf8' : '#c084fc');
const economicCategories = new Set(['Economics', 'Trade', 'Industry', 'Finance']);
const climateCategories = new Set(['Climate']);
const defenseCategories = new Set(['Defense', 'Geopolitics']);

function MapResizer() {
  const map = useMap();
  useEffect(() => {
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

  const { data: countries = [], dataUpdatedAt } = useQuery({
    queryKey: ['global-countries'],
    queryFn: fetchGlobalCountries,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: overview } = useQuery({
    queryKey: ['global-overview'],
    queryFn: fetchGlobalOverview,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: signals = [] } = useQuery({
    queryKey: ['global-signals'],
    queryFn: fetchGlobalSignals,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: corridors = [] } = useQuery({
    queryKey: ['global-corridors'],
    queryFn: fetchGlobalCorridors,
    refetchInterval: 90_000,
    staleTime: 60_000,
  });

  const filteredSignals = useMemo(() => {
    const rows = [];
    if (activeLayers.has('economics')) {
      rows.push(...signals.filter((signal: any) => economicCategories.has(signal.category)));
    }
    if (activeLayers.has('climate')) {
      rows.push(...signals.filter((signal: any) => climateCategories.has(signal.category)));
    }
    if (activeLayers.has('defense')) {
      rows.push(...signals.filter((signal: any) => defenseCategories.has(signal.category)));
    }
    if (activeLayers.has('news')) {
      rows.push(...signals);
    }
    return rows.filter((signal: any, index: number, array: any[]) => array.findIndex((item) => item.id === signal.id) === index);
  }, [signals, activeLayers]);

  const lastUpdated = useLastUpdated(dataUpdatedAt);

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#050505', overflow: 'hidden' }}>
      <MapContainer center={[20, 15]} zoom={2} style={{ width: '100%', height: '100%', background: '#050505' }} zoomControl={false}>
        <MapResizer />
        <TileLayer
          attribution='© CARTO © OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <ZoomControl position="bottomright" />

        {activeLayers.has('corridors') && corridors.map((corridor: any) => (
          <Polyline
            key={corridor.id}
            positions={[
              [corridor.start_lat, corridor.start_lng],
              [corridor.end_lat, corridor.end_lng],
            ]}
            pathOptions={{
              color: corridor.status === 'Critical' ? '#ef4444' : corridor.status === 'Elevated' || corridor.status === 'Stressed' ? '#f59e0b' : '#38bdf8',
              weight: Math.max(1.5, corridor.weight / 35),
              opacity: 0.65,
              dashArray: corridor.status === 'Critical' ? '6, 6' : undefined,
            }}
          >
            <Popup>
              <div className="space-y-1 text-xs">
                <div className="font-bold text-zinc-100">{corridor.label}</div>
                <div className="text-zinc-400">{corridor.from_name} → {corridor.to_name}</div>
                <div className="text-zinc-500 uppercase tracking-widest text-[10px]">
                  {corridor.category} | {corridor.status}
                </div>
              </div>
            </Popup>
          </Polyline>
        ))}

        {activeLayers.has('countries') && countries.map((country: any) => (
          <CircleMarker
            key={country.id}
            center={[country.lat, country.lng]}
            radius={6 + country.influence_index / 20}
            pathOptions={{
              fillColor: countryColor(country.risk_index),
              color: '#ffffff',
              fillOpacity: 0.45,
              weight: 0.8,
            }}
            eventHandlers={{
              click: () => {
                setSelected(country.id, 'country');
                setSidebarTab('global');
              },
            }}
          >
            <Popup>
              <div className="p-1 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-zinc-100">{country.name}</span>
                  <span className="text-[10px] uppercase tracking-widest text-zinc-500">{country.region}</span>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
                  <span className="text-zinc-500">Risk</span>
                  <span className="font-bold" style={{ color: countryColor(country.risk_index) }}>{country.risk_index}</span>
                  <span className="text-zinc-500">Influence</span>
                  <span className="text-zinc-300">{country.influence_index}</span>
                  <span className="text-zinc-500">Signals</span>
                  <span className="text-cyan-300">{country.active_signals}</span>
                  <span className="text-zinc-500">Pressure</span>
                  <span className="text-zinc-300">{country.pressure}</span>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {filteredSignals.map((signal: any) => (
          <CircleMarker
            key={signal.id}
            center={[signal.lat, signal.lng]}
            radius={signal.severity === 'High' ? 6 : 4}
            pathOptions={{
              fillColor: signalColor(signal.severity),
              color: signalColor(signal.severity),
              fillOpacity: 0.8,
              weight: 1,
            }}
            eventHandlers={{
              click: () => {
                setSelected(signal.id, 'signal');
                setSidebarTab('alerts');
              },
            }}
          >
            <Popup>
              <div className="space-y-1 text-xs">
                <div className="font-bold text-zinc-100">{signal.title}</div>
                <div className="text-zinc-400">{signal.category} | {signal.severity}</div>
                <div className="text-zinc-300">{signal.summary}</div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="absolute top-3 right-3 z-[400] rounded-xl border border-zinc-800 bg-black/65 p-3 backdrop-blur-md">
        <div className="text-[10px] uppercase tracking-widest text-zinc-500 mb-2">Global Brief</div>
        <div className="space-y-1 text-[11px]">
          <div className="flex items-center justify-between gap-4">
            <span className="text-zinc-500">Systemic Stress</span>
            <span className="font-black text-amber-400">{overview?.systemic_stress ?? '--'}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-zinc-500">Critical Zones</span>
            <span className="font-black text-red-400">{overview?.critical_zones ?? '--'}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-zinc-500">Corridors</span>
            <span className="font-black text-cyan-400">{overview?.active_corridors ?? '--'}</span>
          </div>
        </div>
      </div>

      <div className="absolute bottom-3 left-3 z-[400] text-[10px] font-mono text-zinc-500 bg-black/60 border border-zinc-800 px-2 py-1 rounded-md backdrop-blur-sm">
        Updated {lastUpdated}
      </div>
    </div>
  );
};
