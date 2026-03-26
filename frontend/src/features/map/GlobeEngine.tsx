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
import { useMapCommands } from '@/hooks/useMapCommands';
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

const COMMAND_PRIORITY_SCORE: Record<string, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

type MapCommandRecord = {
  id: string;
  command_type: string;
  priority: string;
  data: Record<string, any>;
  description: string;
  source: string;
  created_at: string;
  metadata?: Record<string, any>;
};

const normalizeIntensity = (value: unknown): number => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  if (numeric > 1) return Math.max(0, Math.min(1, numeric / 100));
  return Math.max(0, Math.min(1, numeric));
};

const colorForHeat = (intensity: number, colorScale: string): string => {
  if (colorScale === 'blue') {
    if (intensity > 0.75) return '#1d4ed8';
    if (intensity > 0.5) return '#2563eb';
    if (intensity > 0.25) return '#3b82f6';
    return '#93c5fd';
  }
  if (colorScale === 'amber') {
    if (intensity > 0.75) return '#b45309';
    if (intensity > 0.5) return '#d97706';
    if (intensity > 0.25) return '#f59e0b';
    return '#fcd34d';
  }
  if (intensity > 0.75) return '#dc2626';
  if (intensity > 0.5) return '#ef4444';
  if (intensity > 0.25) return '#f97316';
  return '#fca5a5';
};

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
    expertMapLayers,
    expertAffectedRegions,
  } = useAppStore();

  const { mapCommands } = useMapCommands();
  const executedFocusIdsRef = useRef<Set<string>>(new Set());

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

  const countriesById = useMemo(() => {
    const map = new Map<string, GlobalCountry>();
    countries.filter(hasCoords).forEach((country) => map.set(country.id, country));
    return map;
  }, [countries]);

  const sortedMapCommands = useMemo(() => {
    return [...mapCommands]
      .sort((a, b) => {
        const byPriority = (COMMAND_PRIORITY_SCORE[b.priority] || 0) - (COMMAND_PRIORITY_SCORE[a.priority] || 0);
        if (byPriority !== 0) return byPriority;
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      }) as MapCommandRecord[];
  }, [mapCommands]);

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

  // Map command Focus Effect
  useEffect(() => {
    const activeFocusIds = new Set(sortedMapCommands.filter((cmd) => cmd.command_type === 'focus')?.map((cmd) => cmd.id));
    for (const executedId of Array.from(executedFocusIdsRef.current)) {
      if (!activeFocusIds.has(executedId)) {
        executedFocusIdsRef.current.delete(executedId);
      }
    }

    const nextFocus = sortedMapCommands.find((cmd) => cmd.command_type === 'focus' && !executedFocusIdsRef.current.has(cmd.id));
    if (!nextFocus) return;

    const focusCountry = countriesById.get(String(nextFocus.data?.country_id || ''));
    if (!focusCountry || !hasCoords(focusCountry)) return;

    const globe = getGlobe();
    if (globe) {
      globe.pointOfView({ lat: focusCountry.lat, lng: focusCountry.lng, altitude: 0.8 }, 1400);
      globe.controls().autoRotate = false;
    }
    executedFocusIdsRef.current.add(nextFocus.id);
  }, [sortedMapCommands, countriesById]);

  // AI Region Focus Effect
  useEffect(() => {
    if (!expertAffectedRegions?.length || !countries?.length) return;

    const matchedCountries = countries.filter((c) => {
      const nameLower = c.name.toLowerCase();
      return expertAffectedRegions.some((r) => nameLower.includes(r.toLowerCase()) || r.toLowerCase().includes(nameLower));
    });

    if (matchedCountries?.length === 0) return;

    const first = matchedCountries.filter(hasCoords)[0];
    if (first) {
      const globe = getGlobe();
      if (globe) {
        globe.pointOfView({ lat: first.lat, lng: first.lng, altitude: 1.2 }, 1500);
        globe.controls().autoRotate = false;
      }
    }
  }, [expertAffectedRegions, countries]);

  // Selected Country Effect
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
        ?.map((country) => ({ ...country, type: 'country' as const, altitude: 0.025 }))
      : [];

    const signalMarkers: SignalMarker[] = filteredSignals?.map((signal) => ({
      ...signal,
      type: 'signal' as const,
      altitude: signal.severity === 'High' ? 0.05 : 0.04,
    }));

    const assetMarkers: AssetMarker[] = filteredAssets?.map((asset) => ({
      ...asset,
      type: 'asset' as const,
      altitude: 0.032,
    }));

    return [...countryMarkers, ...signalMarkers, ...assetMarkers];
  }, [activeLayers, countries, filteredAssets, filteredSignals]);

  // Extract Route Commands
  const commandRoutes = useMemo(() => {
    return sortedMapCommands
      .filter((cmd) => cmd.command_type === 'route')
      ?.map((cmd) => {
        const fromId = String(cmd.data?.from_country || '');
        const toId = String(cmd.data?.to_country || '');
        const fromCountry = countriesById.get(fromId);
        const toCountry = countriesById.get(toId);
        if (!fromCountry || !toCountry || !hasCoords(fromCountry) || !hasCoords(toCountry)) return null;
        return {
          id: cmd.id,
          fromCountry,
          toCountry,
          color: String(cmd.data?.color || '#10b981'),
        };
      })
      .filter(Boolean);
  }, [sortedMapCommands, countriesById]);

  // Unified Arcs Data
  const arcsData = useMemo(() => {
    const baseArcs = activeLayers.has('corridors')
      ? corridors.filter(hasCorridorCoords)?.map((corridor) => ({
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
          label: `${corridor.label} | ${corridor.from_name} -> ${corridor.to_name}`,
        }))
      : [];

    const cmdArcs = commandRoutes?.map((route: any) => ({
      startLat: route.fromCountry.lat,
      startLng: route.fromCountry.lng,
      endLat: route.toCountry.lat,
      endLng: route.toCountry.lng,
      color: [route.color, route.color],
      label: `${route.fromCountry.name} -> ${route.toCountry.name}`,
    })) || [];

    const expertArcs = (expertMapLayers || [])
      .filter((layer) => layer.type === 'route' && layer.visible !== false)
      .flatMap((layer) => {
        const routeData = layer.data as Array<any>;
        if (!Array.isArray(routeData)) return [];
        return routeData.filter(hasCorridorCoords).map((route) => ({
          startLat: route.start_lat,
          startLng: route.start_lng,
          endLat: route.end_lat,
          endLng: route.end_lng,
          color: [layer.color || '#10b981', layer.color || '#10b981'],
          label: route.label || 'Expert Route',
        }));
      });

    return [...baseArcs, ...cmdArcs, ...expertArcs];
  }, [corridors, activeLayers, commandRoutes, expertMapLayers]);

  // Extract Rings Data (Highlights, Heatmaps, Expert Layers)
  const commandRings = useMemo(() => {
    const highlights = sortedMapCommands
      .filter((cmd) => cmd.command_type === 'highlight')
      .flatMap((cmd) => {
        const countryIds = Array.isArray(cmd.data?.country_ids) ? cmd.data.country_ids : [];
        return countryIds?.map((countryId: string) => {
          const country = countriesById.get(countryId);
          if (!country || !hasCoords(country)) return null;
          const priorityBoost = COMMAND_PRIORITY_SCORE[cmd.priority] || 1;
          const radius = Number(cmd.data?.radius) || 280000 + priorityBoost * 50000;
          return {
            lat: country.lat,
            lng: country.lng,
            maxR: radius / 111000,
            propagationSpeed: cmd.data?.pulse !== false ? 2 : 0,
            repeatPeriod: cmd.data?.pulse !== false ? 800 : 0,
            color: String(cmd.data?.color || '#3b82f6'),
          };
        });
      })
      .filter(Boolean);

    const heatmaps = sortedMapCommands
      .filter((cmd) => cmd.command_type === 'heatmap')
      .flatMap((cmd) => {
        const points = Array.isArray(cmd.data?.data_points) ? cmd.data.data_points : [];
        const scale = String(cmd.data?.color_scale || 'red').toLowerCase();
        return points?.map((point: Record<string, any>) => {
          const countryId = String(point.country_id || '');
          const country = countryId ? countriesById.get(countryId) : undefined;
          const lat = country?.lat ?? point.lat;
          const lng = country?.lng ?? point.lng;
          if (typeof lat !== 'number' || typeof lng !== 'number' || !Number.isFinite(lat) || !Number.isFinite(lng)) return null;

          const intensity = normalizeIntensity(
            point.value ?? point.risk ?? point.intensity ?? point.score ?? 0,
          );
          const color = colorForHeat(intensity, scale);
          const radius = 8 + intensity * 14; // roughly matching scale
          return {
            lat,
            lng,
            maxR: radius / 3, // scale leafet radius roughly to degrees
            propagationSpeed: 1.5,
            repeatPeriod: 1200,
            color,
          };
        });
      })
      .filter(Boolean);

    const overlays = sortedMapCommands
      .filter((cmd) => cmd.command_type === 'overlay')
      .flatMap((cmd) => {
        const overlayType = String(cmd.data?.overlay_type || '').toLowerCase();
        const overlayData = cmd.data?.overlay_data;
        if (!overlayData || (overlayType !== 'scenario_summary' && overlayType !== 'scenario_impact_zones')) return [];
        const points = Array.isArray(overlayData.points) ? overlayData.points : [];
        return points?.map((point: Record<string, any>) => {
          const country = point.country_id ? countriesById.get(String(point.country_id)) : undefined;
          const lat = country?.lat ?? Number(point.lat);
          const lng = country?.lng ?? Number(point.lng);
          if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

          const intensity = normalizeIntensity(point.value ?? point.impact ?? 0.45);
          return {
            lat,
            lng,
            maxR: (120000 + intensity * 260000) / 111000,
            propagationSpeed: 1,
            repeatPeriod: 1500,
            color: '#f97316',
          };
        });
      })
      .filter(Boolean);

    // Expert Overlays
    const expertHighlights = (expertMapLayers || [])
      .filter((l) => l.type === 'highlight' && l.visible !== false)
      .flatMap((l) => (Array.isArray(l.data) ? l.data : []).map((cid) => {
        const c = countriesById.get(cid);
        if (!c || !hasCoords(c)) return null;
        return {
          lat: c.lat,
          lng: c.lng,
          maxR: 400000 / 111000,
          propagationSpeed: 2,
          repeatPeriod: 1000,
          color: l.color || '#3b82f6',
        };
      })).filter(Boolean);

    const expertRisk = (expertMapLayers || [])
      .filter((l) => l.type === 'risk_heatmap' && l.visible !== false)
      .flatMap((l) => {
        const riskData = l.data as Record<string, any>;
        return Object.entries(riskData).map(([cid, data]) => {
          const c = countriesById.get(cid);
          if (!c || !hasCoords(c)) return null;
          const isRel = data.relevant;
          const risk = data.risk;
          const color = risk >= 0.7 ? '#ef4444' : risk >= 0.4 ? '#f59e0b' : '#10b981';
          return {
            lat: c.lat,
            lng: c.lng,
            maxR: (isRel ? 350000 : 200000 + risk * 150000) / 111000,
            propagationSpeed: isRel ? 1.5 : 0,
            repeatPeriod: isRel ? 1000 : 0,
            color,
          };
        });
      }).filter(Boolean);

    const expertDensity = (expertMapLayers || [])
      .filter((l) => l.type === 'signal_density' && l.visible !== false)
      .flatMap((l) => {
        const densityData = l.data as Record<string, any>;
        return Object.entries(densityData).map(([cid, data]) => {
          const c = countriesById.get(cid);
          if (!c || !hasCoords(c)) return null;
          return {
            lat: c.lat,
            lng: c.lng,
            maxR: (200000 + data.count * 30000) / 111000,
            propagationSpeed: 1,
            repeatPeriod: 1000,
            color: '#60a5fa',
          };
        });
      }).filter(Boolean);

    return [...highlights, ...heatmaps, ...overlays, ...expertHighlights, ...expertRisk, ...expertDensity];
  }, [sortedMapCommands, countriesById, expertMapLayers]);

  const newsLabels = useMemo(
    () =>
      activeLayers.has('news')
        ? countries
          .filter(hasCoords)
          .slice()
          .sort((left, right) => right.active_signals - left.active_signals)
          .slice(0, 8)
          ?.map((country, index) => ({
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
        const item = arc as { label: string };
        return item.label;
      }}
      ringsData={commandRings}
      ringLat="lat"
      ringLng="lng"
      ringMaxRadius="maxR"
      ringPropagationSpeed="propagationSpeed"
      ringRepeatPeriod="repeatPeriod"
      ringColor="color"
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
