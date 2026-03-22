import React, { useEffect, useMemo, useRef } from 'react';
import Globe, { type GlobeMethods } from 'react-globe.gl';
import { useQuery } from '@tanstack/react-query';
import {
  fetchGlobalAssets,
  fetchGlobalCorridors,
  fetchGlobalCountries,
  fetchGlobalSignals,
  fetchNews,
} from '@/services/api';
import { useAppStore } from '@/store';
import { getMarkerHtml } from './markerGlyphs';
import type { GlobalAsset, GlobalCountry, GlobalSignal, LayerKey } from '@/types';

interface GlobeEngineProps {
  width: number;
  height: number;
}

type CountryMarker = GlobalCountry & { type: 'country'; altitude: number };
type SignalMarker = GlobalSignal & { type: 'signal'; altitude: number };
type AssetMarker = GlobalAsset & { type: 'asset'; altitude: number };
type GlobeMarker = CountryMarker | SignalMarker | AssetMarker;

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

export const GlobeEngine: React.FC<GlobeEngineProps> = ({ width, height }) => {
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const {
    activeLayers,
    selectedId,
    selectedType,
    setHoveredItem,
    setSelected,
    setSidebarTab,
    setSidebarOpen,
  } = useAppStore();

  const { data: countries = [] } = useQuery({
    queryKey: ['global-countries'],
    queryFn: fetchGlobalCountries,
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

  const { data: feeds = [] } = useQuery({
    queryKey: ['news'],
    queryFn: fetchNews,
    refetchInterval: 60_000,
    staleTime: 30_000,
    enabled: activeLayers.has('news'),
  });

  const getGlobe = () => globeRef.current;

  useEffect(() => {
    const globe = getGlobe();
    if (!globe) return;
    globe.pointOfView({ lat: 20, lng: 30, altitude: 1.65 }, 1800);
    const controls = globe.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.28;
    controls.enableZoom = true;
    controls.enablePan = true;

    const stopRotate = () => {
      controls.autoRotate = false;
    };

    const canvas = globe.renderer().domElement;
    canvas.style.pointerEvents = 'auto';
    canvas.style.cursor = 'grab';
    canvas.addEventListener('mousedown', stopRotate);
    canvas.addEventListener('touchstart', stopRotate);
    return () => {
      canvas.removeEventListener('mousedown', stopRotate);
      canvas.removeEventListener('touchstart', stopRotate);
    };
  }, []);

  useEffect(() => {
    const globe = getGlobe();
    if (!globe || selectedType !== 'country' || !selectedId) return;
    const selectedCountry = countries.filter(hasCoords).find((country) => country.id === selectedId);
    if (!selectedCountry) return;
    globe.pointOfView(
      { lat: selectedCountry.lat, lng: selectedCountry.lng, altitude: 1.02 },
      1400,
    );
    globe.controls().autoRotate = false;
  }, [countries, selectedId, selectedType]);

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

  const markers = useMemo<GlobeMarker[]>(() => {
    const countryMarkers: CountryMarker[] = activeLayers.has('countries')
      ? countries
          .filter(hasCoords)
          .map((country) => ({ ...country, type: 'country' as const, altitude: 0.025 }))
      : [];

    const signalMarkers: SignalMarker[] = filteredSignals.map((signal) => ({
      ...signal,
      type: 'signal' as const,
      altitude: signal.severity === 'High' ? 0.05 : 0.04,
    }));

    const assetMarkers: AssetMarker[] = filteredAssets.map((asset) => ({
      ...asset,
      type: 'asset' as const,
      altitude: 0.032,
    }));

    return [...countryMarkers, ...signalMarkers, ...assetMarkers];
  }, [activeLayers, countries, filteredAssets, filteredSignals]);

  const arcsData = useMemo(
    () =>
      activeLayers.has('corridors')
        ? corridors.filter(hasCorridorCoords).map((corridor) => ({
            ...corridor,
            startLat: corridor.start_lat,
            startLng: corridor.start_lng,
            endLat: corridor.end_lat,
            endLng: corridor.end_lng,
            color:
              corridor.status === 'Critical'
                ? ['#ef4444', '#fb7185']
                : corridor.status === 'Elevated' || corridor.status === 'Stressed'
                  ? ['#f59e0b', '#fbbf24']
                  : ['#38bdf8', '#818cf8'],
          }))
        : [],
    [corridors, activeLayers],
  );

  const newsLabels = useMemo(
    () =>
      activeLayers.has('news')
        ? countries
            .filter(hasCoords)
            .slice()
            .sort((left, right) => right.active_signals - left.active_signals)
            .slice(0, 8)
            .map((country, index) => ({
              lat: country.lat,
              lng: country.lng,
              text: feeds[index]?.text?.slice(0, 48) || `${country.name}: signal density rising`,
              size: 1.0,
              color: '#67e8f9',
            }))
        : [],
    [activeLayers, countries, feeds],
  );

  const handleMarkerSelection = (marker: GlobeMarker) => {
    if (marker.type === 'country') {
      setSelected(marker.id, 'country');
      setSidebarTab('global');
      setSidebarOpen(true);
      return;
    }

    if (marker.type === 'signal') {
      setSelected(marker.id, 'signal');
      setSidebarTab('alerts');
      setSidebarOpen(true);
      return;
    }

    if (marker.type === 'asset') {
      setSelected(marker.country_id, 'country');
    }
    setSidebarTab('global');
    setSidebarOpen(true);
  };

  return (
    <Globe
      ref={globeRef}
      width={width}
      height={height}
      globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
      bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
      backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
      showAtmosphere
      showPointerCursor
      enablePointerInteraction
      atmosphereColor="#38bdf8"
      atmosphereAltitude={0.16}
      htmlElementsData={markers}
      htmlLat="lat"
      htmlLng="lng"
      htmlAltitude="altitude"
      htmlTransitionDuration={0}
      htmlElement={(datum: object) => {
        const marker = datum as GlobeMarker;
        const element = document.createElement('button');
        element.type = 'button';
        element.style.background = 'transparent';
        element.style.border = '0';
        element.style.padding = '0';
        element.style.cursor = 'pointer';
        element.style.pointerEvents = 'auto';
        element.innerHTML = getMarkerHtml(
          {
            ...marker,
            sourceMode: marker.type === 'country' ? marker.country_catalog_mode : marker.source_mode,
          },
          marker.id === selectedId || (marker.type === 'asset' && marker.country_id === selectedId),
        );
        element.onmouseenter = () => setHoveredItem(marker);
        element.onmouseleave = () => setHoveredItem(null);
        element.onclick = (event) => {
          event.stopPropagation();
          handleMarkerSelection(marker);
        };
        return element;
      }}
      arcsData={arcsData}
      arcColor="color"
      arcDashLength={0.35}
      arcDashGap={0.18}
      arcDashAnimateTime={1600}
      arcStroke={0.62}
      arcAltitudeAutoScale={0.45}
      arcLabel={(arc: object) => {
        const item = arc as { label: string; from_name: string; to_name: string };
        return `${item.label} | ${item.from_name} -> ${item.to_name}`;
      }}
      labelsData={newsLabels}
      labelLat="lat"
      labelLng="lng"
      labelText="text"
      labelSize="size"
      labelColor="color"
      labelDotRadius={0.35}
      labelAltitude={0.01}
    />
  );
};
