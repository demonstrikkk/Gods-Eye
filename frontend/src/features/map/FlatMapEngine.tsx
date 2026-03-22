import React, { useEffect, useMemo } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import { useQuery } from '@tanstack/react-query';
import 'leaflet/dist/leaflet.css';
import {
  fetchGlobalAssets,
  fetchGlobalCorridors,
  fetchGlobalCountries,
  fetchGlobalOverview,
  fetchGlobalSignals,
} from '@/services/api';
import { useAppStore } from '@/store';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { createLeafletMarkerIcon } from './markerGlyphs';
import type { GlobalAsset, GlobalCountry, GlobalSignal, LayerKey } from '@/types';

const hasCoords = (value: { lat?: number | null; lng?: number | null }) =>
  typeof value.lat === 'number' && Number.isFinite(value.lat) &&
  typeof value.lng === 'number' && Number.isFinite(value.lng);

const hasCorridorCoords = (value: {
  start_lat?: number | null;
  start_lng?: number | null;
  end_lat?: number | null;
  end_lng?: number | null;
}) =>
  typeof value.start_lat === 'number' && Number.isFinite(value.start_lat) &&
  typeof value.start_lng === 'number' && Number.isFinite(value.start_lng) &&
  typeof value.end_lat === 'number' && Number.isFinite(value.end_lat) &&
  typeof value.end_lng === 'number' && Number.isFinite(value.end_lng);

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

function SelectedCountryFocus({ country }: { country: GlobalCountry | null }) {
  const map = useMap();

  useEffect(() => {
    if (!country) return;
    map.flyTo([country.lat, country.lng], Math.max(map.getZoom(), 4), {
      animate: true,
      duration: 1.2,
    });
  }, [country, map]);

  return null;
}

const DATA_LAYERS: LayerKey[] = [
  'economics',
  'governance',
  'climate',
  'defense',
  'conflict',
  'infrastructure',
  'mobility',
  'cyber',
];

const popupForCountry = (country: GlobalCountry) => (
  <div className="space-y-1 text-xs">
    <div className="font-bold text-zinc-100">{country.name}</div>
    <div className="text-zinc-400">{country.region} · Risk {country.risk_index}</div>
    <div className="text-zinc-300">
      Influence {country.influence_index} · Signals {country.active_signals} · Assets {country.asset_count ?? 0}
    </div>
  </div>
);

const popupForSignal = (signal: GlobalSignal) => (
  <div className="space-y-1 text-xs">
    <div className="font-bold text-zinc-100">{signal.title}</div>
    <div className="text-zinc-400">{signal.category} · {signal.severity} · {signal.layer}</div>
    <div className="text-zinc-300">{signal.summary}</div>
  </div>
);

const popupForAsset = (asset: GlobalAsset) => (
  <div className="space-y-1 text-xs">
    <div className="font-bold text-zinc-100">{asset.title}</div>
    <div className="text-zinc-400">{asset.kind} · {asset.status}</div>
    <div className="text-zinc-300">{asset.description}</div>
  </div>
);

export const FlatMapEngine: React.FC = () => {
  const {
    activeLayers,
    selectedId,
    selectedType,
    setHoveredItem,
    setSelected,
    setSidebarTab,
    setSidebarOpen,
  } = useAppStore();

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

  const { data: assets = [] } = useQuery({
    queryKey: ['global-assets'],
    queryFn: fetchGlobalAssets,
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const { data: corridors = [] } = useQuery({
    queryKey: ['global-corridors'],
    queryFn: fetchGlobalCorridors,
    refetchInterval: 90_000,
    staleTime: 60_000,
  });

  const filteredSignals = useMemo(() => {
    const selectedSignals = DATA_LAYERS.flatMap((layer) =>
      activeLayers.has(layer) ? signals.filter((signal) => signal.layer === layer) : [],
    );
    const merged = activeLayers.has('news') ? [...selectedSignals, ...signals] : selectedSignals;
    return merged
      .filter(hasCoords)
      .filter((signal, index, array) => array.findIndex((item) => item.id === signal.id) === index);
  }, [activeLayers, signals]);

  const filteredAssets = useMemo(() => {
    const merged = DATA_LAYERS.flatMap((layer) =>
      activeLayers.has(layer) ? assets.filter((asset) => asset.layer === layer) : [],
    );
    return merged
      .filter(hasCoords)
      .filter((asset, index, array) => array.findIndex((item) => item.id === asset.id) === index);
  }, [activeLayers, assets]);

  const selectedCountry = useMemo(
    () => (
      selectedType === 'country'
        ? countries.filter(hasCoords).find((country) => country.id === selectedId) ?? null
        : null
    ),
    [countries, selectedId, selectedType],
  );

  const lastUpdated = useLastUpdated(dataUpdatedAt);

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#050505', overflow: 'hidden' }}>
      <MapContainer
        center={[20, 15]}
        zoom={2}
        zoomControl={false}
        scrollWheelZoom
        doubleClickZoom
        dragging
        touchZoom
        boxZoom
        keyboard
        style={{ width: '100%', height: '100%', background: '#050505', cursor: 'grab' }}
      >
        <MapResizer />
        <SelectedCountryFocus country={selectedCountry} />
        <TileLayer
          attribution="CARTO | OpenStreetMap"
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        <ZoomControl position="bottomright" />

        {activeLayers.has('corridors') && corridors.filter(hasCorridorCoords).map((corridor) => (
          <Polyline
            key={corridor.id}
            positions={[
              [corridor.start_lat, corridor.start_lng],
              [corridor.end_lat, corridor.end_lng],
            ]}
            pathOptions={{
              color: corridor.status === 'Critical' ? '#ef4444' : corridor.status === 'Elevated' || corridor.status === 'Stressed' ? '#f59e0b' : '#38bdf8',
              weight: Math.max(1.8, corridor.weight / 32),
              opacity: 0.7,
              dashArray: corridor.status === 'Critical' ? '7 6' : corridor.status === 'Elevated' ? '5 5' : undefined,
            }}
          >
            <Popup>
              <div className="space-y-1 text-xs">
                <div className="font-bold text-zinc-100">{corridor.label}</div>
                <div className="text-zinc-400">{corridor.from_name} -&gt; {corridor.to_name}</div>
                <div className="text-zinc-300">{corridor.category} · {corridor.status}</div>
              </div>
            </Popup>
          </Polyline>
        ))}

        {activeLayers.has('countries') && countries.filter(hasCoords).map((country) => (
          <Marker
            key={country.id}
            position={[country.lat, country.lng]}
            icon={createLeafletMarkerIcon({ type: 'country', sourceMode: country.country_catalog_mode }, country.id === selectedId)}
            riseOnHover
            eventHandlers={{
              mouseover: () => setHoveredItem(country),
              mouseout: () => setHoveredItem(null),
              click: () => {
                setSelected(country.id, 'country');
                setSidebarTab('global');
                setSidebarOpen(true);
              },
            }}
          >
            <Popup>{popupForCountry(country)}</Popup>
          </Marker>
        ))}

        {filteredSignals.map((signal) => (
          <Marker
            key={signal.id}
            position={[signal.lat, signal.lng]}
            icon={createLeafletMarkerIcon({ type: 'signal', layer: signal.layer, category: signal.category, sourceMode: signal.source_mode })}
            riseOnHover
            eventHandlers={{
              mouseover: () => setHoveredItem(signal),
              mouseout: () => setHoveredItem(null),
              click: () => {
                setSelected(signal.id, 'signal');
                setSidebarTab('alerts');
                setSidebarOpen(true);
              },
            }}
          >
            <Popup>{popupForSignal(signal)}</Popup>
          </Marker>
        ))}

        {filteredAssets.map((asset) => (
          <Marker
            key={asset.id}
            position={[asset.lat, asset.lng]}
            icon={createLeafletMarkerIcon({ type: 'asset', layer: asset.layer, category: asset.category, sourceMode: asset.source_mode }, asset.country_id === selectedId)}
            riseOnHover
            eventHandlers={{
              mouseover: () => setHoveredItem(asset),
              mouseout: () => setHoveredItem(null),
              click: () => {
                setSelected(asset.country_id, 'country');
                setSidebarTab('global');
                setSidebarOpen(true);
              },
            }}
          >
            <Popup>{popupForAsset(asset)}</Popup>
          </Marker>
        ))}
      </MapContainer>

      <div className="pointer-events-none absolute top-3 right-3 z-[400] rounded-xl border border-zinc-800 bg-black/65 p-3 backdrop-blur-md">
        <div className="mb-2 text-[10px] uppercase tracking-widest text-zinc-500">Global Brief</div>
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
            <span className="text-zinc-500">Assets</span>
            <span className="font-black text-emerald-400">{overview?.total_assets ?? '--'}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-zinc-500">Runtime / Seeded</span>
            <span className="font-black text-cyan-300">
              {overview?.runtime_signals ?? 0} / {overview?.seeded_signals ?? 0}
            </span>
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-3 left-3 z-[400] rounded-md border border-zinc-800 bg-black/60 px-2 py-1 font-mono text-[10px] text-zinc-500 backdrop-blur-sm">
        Updated {lastUpdated}
      </div>
    </div>
  );
};
