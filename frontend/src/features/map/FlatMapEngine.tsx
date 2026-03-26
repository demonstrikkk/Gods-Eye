import React, { useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer, ZoomControl, useMap, Circle, CircleMarker } from 'react-leaflet';
import { useQuery } from '@tanstack/react-query';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  fetchGlobalAssets,
  fetchGlobalCorridors,
  fetchGlobalCountries,
  fetchGlobalOverview,
  fetchGlobalSignals,
} from '@/services/api';
import { useAppStore } from '@/store';
import { useLastUpdated } from '@/hooks/useLastUpdated';
import { useMapCommands } from '@/hooks/useMapCommands';
import { createLeafletMarkerIcon, createHighlightMarkerIcon } from './markerGlyphs';
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

/**
 * AIRegionFocus: Auto-focuses the map on regions identified by AI analysis.
 * Calculates the bounding box of all mentioned countries and fits the view.
 */
function AIRegionFocus({
  regions,
  countries,
}: {
  regions: string[];
  countries: GlobalCountry[];
}) {
  const map = useMap();

  useEffect(() => {
    if (!regions?.length || !countries?.length) return;

    // Find countries that match the regions
    const matchedCountries = countries.filter((c) => {
      const nameLower = c.name.toLowerCase();
      return regions.some((r) => nameLower.includes(r.toLowerCase()) || r.toLowerCase().includes(nameLower));
    });

    if (matchedCountries?.length === 0) return;

    // Create bounds
    const bounds = L.latLngBounds(
      matchedCountries.filter(hasCoords)?.map((c) => [c.lat, c.lng] as [number, number])
    );

    if (bounds.isValid()) {
      // Add padding and fit bounds
      map.flyToBounds(bounds.pad(0.3), {
        animate: true,
        duration: 1.5,
        maxZoom: 5,
      });
    }
  }, [regions, countries, map]);

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

type PinnedScenarioSnapshot = {
  id: string;
  title: string;
  outcome: string;
  source: string;
  priority: string;
  pinnedAt: string;
  scenarios: Array<{ name: string; probability: string; impactSeverity: number }>;
};

type ScenarioOverlaySummary = {
  id: string;
  title: string;
  outcome: string;
  source: string;
  priority: string;
  createdAt: string;
  scenarios: Array<{ name: string; probability: string; impactSeverity: number }>;
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

function MapCommandFocus({
  commands,
  countriesById,
}: {
  commands: MapCommandRecord[];
  countriesById: Map<string, GlobalCountry>;
}) {
  const map = useMap();
  const executedFocusIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const activeFocusIds = new Set(commands.filter((cmd) => cmd.command_type === 'focus')?.map((cmd) => cmd.id));
    for (const executedId of Array.from(executedFocusIdsRef.current)) {
      if (!activeFocusIds.has(executedId)) {
        executedFocusIdsRef.current.delete(executedId);
      }
    }

    const nextFocus = commands.find((cmd) => cmd.command_type === 'focus' && !executedFocusIdsRef.current.has(cmd.id));
    if (!nextFocus) return;

    const focusCountry = countriesById.get(String(nextFocus.data?.country_id || ''));
    if (!focusCountry || !hasCoords(focusCountry)) return;

    const zoomLevel = Number(nextFocus.data?.zoom_level);
    const durationSeconds = Number(nextFocus.data?.duration_ms) / 1000;

    map.flyTo([focusCountry.lat, focusCountry.lng], Number.isFinite(zoomLevel) ? zoomLevel : 5, {
      animate: true,
      duration: Number.isFinite(durationSeconds) && durationSeconds > 0 ? durationSeconds : 1,
    });

    executedFocusIdsRef.current.add(nextFocus.id);
  }, [commands, countriesById, map]);

  return null;
}

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
    expertMapLayers,
    expertAffectedRegions,
  } = useAppStore();

  // Fetch and manage map commands from backend
  const { mapCommands } = useMapCommands();
  const [showBaselineData, setShowBaselineData] = useState(true);
  const [showCommandOverlays, setShowCommandOverlays] = useState(true);
  const [showExpertOverlays, setShowExpertOverlays] = useState(true);
  const [showScenarioOverlays, setShowScenarioOverlays] = useState(true);
  const [pinnedScenarioSnapshots, setPinnedScenarioSnapshots] = useState<PinnedScenarioSnapshot[]>([]);

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

  const sortedMapCommands = useMemo(() => {
    return [...mapCommands]
      .sort((a, b) => {
        const byPriority = (COMMAND_PRIORITY_SCORE[b.priority] || 0) - (COMMAND_PRIORITY_SCORE[a.priority] || 0);
        if (byPriority !== 0) return byPriority;
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      }) as MapCommandRecord[];
  }, [mapCommands]);

  const countriesById = useMemo(() => {
    const map = new Map<string, GlobalCountry>();
    countries.filter(hasCoords).forEach((country) => map.set(country.id, country));
    return map;
  }, [countries]);

  const commandHighlightCircles = useMemo(() => {
    return sortedMapCommands
      .filter((cmd) => cmd.command_type === 'highlight')
      .flatMap((cmd) => {
        const countryIds = Array.isArray(cmd.data?.country_ids) ? cmd.data.country_ids : [];
        return countryIds?.map((countryId: string) => {
          const country = countriesById.get(countryId);
          if (!country || !hasCoords(country)) return null;
          const priorityBoost = COMMAND_PRIORITY_SCORE[cmd.priority] || 1;
          const radius = Number(cmd.data?.radius) || 280000 + priorityBoost * 50000;
          return {
            id: `${cmd.id}-${countryId}`,
            country,
            color: String(cmd.data?.color || '#3b82f6'),
            radius,
            pulse: cmd.data?.pulse !== false,
            description: cmd.description,
            source: cmd.source,
            priority: cmd.priority,
          };
        });
      })
      .filter(Boolean);
  }, [sortedMapCommands, countriesById]);

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
          weight: Number(cmd.data?.weight) || 3,
          animated: cmd.data?.animated !== false,
          routeType: String(cmd.data?.route_type || 'route'),
          description: cmd.description,
          priority: cmd.priority,
          source: cmd.source,
        };
      })
      .filter(Boolean);
  }, [sortedMapCommands, countriesById]);

  const commandHeatmapPoints = useMemo(() => {
    return sortedMapCommands
      .filter((cmd) => cmd.command_type === 'heatmap')
      .flatMap((cmd) => {
        const points = Array.isArray(cmd.data?.data_points) ? cmd.data.data_points : [];
        const scale = String(cmd.data?.color_scale || 'red').toLowerCase();
        return points?.map((point: Record<string, any>, index: number) => {
          const countryId = String(point.country_id || '');
          const country = countryId ? countriesById.get(countryId) : undefined;
          const lat = country?.lat ?? point.lat;
          const lng = country?.lng ?? point.lng;
          if (typeof lat !== 'number' || typeof lng !== 'number' || !Number.isFinite(lat) || !Number.isFinite(lng)) return null;

          const intensity = normalizeIntensity(
            point.value ?? point.risk ?? point.intensity ?? point.score ?? 0,
          );
          const color = colorForHeat(intensity, scale);
          return {
            id: `${cmd.id}-heat-${index}`,
            lat,
            lng,
            intensity,
            color,
            radius: 8 + intensity * 14,
            valueLabel: Math.round(intensity * 100),
            metric: String(cmd.data?.metric || 'intensity'),
            commandDescription: cmd.description,
            source: cmd.source,
            priority: cmd.priority,
            label: String(point.label || country?.name || 'Point'),
          };
        });
      })
      .filter(Boolean);
  }, [sortedMapCommands, countriesById]);

  const commandMarkers = useMemo(() => {
    return sortedMapCommands
      .filter((cmd) => cmd.command_type === 'marker')
      ?.map((cmd) => {
        const lat = Number(cmd.data?.lat);
        const lng = Number(cmd.data?.lng);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
        return {
          id: cmd.id,
          lat,
          lng,
          label: String(cmd.data?.label || 'Marker'),
          markerType: String(cmd.data?.marker_type || 'custom'),
          color: String(cmd.data?.color || '#f59e0b'),
          description: cmd.description,
          source: cmd.source,
          priority: cmd.priority,
        };
      })
      .filter(Boolean);
  }, [sortedMapCommands]);

  const commandOverlayPoints = useMemo(() => {
    return sortedMapCommands
      .filter((cmd) => cmd.command_type === 'overlay')
      .flatMap((cmd) => {
        const overlayType = String(cmd.data?.overlay_type || '').toLowerCase();
        const overlayData = cmd.data?.overlay_data;
        if (!overlayData || (overlayType !== 'scenario_summary' && overlayType !== 'scenario_impact_zones')) {
          return [];
        }

        const points = Array.isArray(overlayData.points) ? overlayData.points : [];
        return points
          ?.map((point: Record<string, any>, index: number) => {
            const country = point.country_id ? countriesById.get(String(point.country_id)) : undefined;
            const lat = country?.lat ?? Number(point.lat);
            const lng = country?.lng ?? Number(point.lng);
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

            const intensity = normalizeIntensity(point.value ?? point.impact ?? 0.45);
            return {
              id: `${cmd.id}-overlay-${index}`,
              lat,
              lng,
              label: String(point.label || country?.name || 'Scenario zone'),
              intensity,
              source: cmd.source,
              priority: cmd.priority,
              description: cmd.description,
            };
          })
          .filter(Boolean);
      });
  }, [sortedMapCommands, countriesById]);

  const scenarioOverlaySummary = useMemo<ScenarioOverlaySummary | null>(() => {
    const overlay = sortedMapCommands.find(
      (cmd) => cmd.command_type === 'overlay' && String(cmd.data?.overlay_type || '').toLowerCase() === 'scenario_summary',
    );
    if (!overlay) return null;

    const overlayData = overlay.data?.overlay_data || {};
    const scenarios = Array.isArray(overlayData.scenarios) ? overlayData.scenarios : [];
    return {
      id: overlay.id,
      title: String(overlayData.title || 'Scenario Simulation'),
      outcome: String(overlayData.outcome || ''),
      scenarios: scenarios
        ?.map((item: Record<string, any>) => ({
          name: String(item.name || 'Scenario'),
          probability: String(item.probability || 'Unknown'),
          impactSeverity: Number(item.impact_severity) || 0,
        }))
        .slice(0, 3),
      source: overlay.source,
      priority: overlay.priority,
      createdAt: overlay.created_at,
    };
  }, [sortedMapCommands]);

  const pinScenarioSnapshot = () => {
    if (!scenarioOverlaySummary) return;

    setPinnedScenarioSnapshots((existing) => {
      if (existing.some((snapshot) => snapshot.id === scenarioOverlaySummary.id)) {
        return existing;
      }
      const nextSnapshot: PinnedScenarioSnapshot = {
        id: scenarioOverlaySummary.id,
        title: scenarioOverlaySummary.title,
        outcome: scenarioOverlaySummary.outcome,
        source: scenarioOverlaySummary.source,
        priority: scenarioOverlaySummary.priority,
        pinnedAt: scenarioOverlaySummary.createdAt,
        scenarios: scenarioOverlaySummary.scenarios,
      };
      return [nextSnapshot, ...existing].slice(0, 5);
    });
  };

  const unpinScenarioSnapshot = (snapshotId: string) => {
    setPinnedScenarioSnapshots((existing) => existing.filter((snapshot) => snapshot.id !== snapshotId));
  };

  const hasCommandVisuals = commandHighlightCircles?.length > 0 || commandHeatmapPoints?.length > 0 || commandRoutes?.length > 0 || commandMarkers?.length > 0 || commandOverlayPoints?.length > 0;
  const hasScenarioOverlay = commandOverlayPoints?.length > 0 || Boolean(scenarioOverlaySummary);

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
        <MapCommandFocus commands={sortedMapCommands} countriesById={countriesById} />
        <TileLayer
          attribution="CARTO | OpenStreetMap"
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        <ZoomControl position="bottomright" />

        {showBaselineData && activeLayers.has('corridors') && corridors.filter(hasCorridorCoords)?.map((corridor) => (
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

        {showBaselineData && activeLayers.has('countries') && countries.filter(hasCoords)?.map((country) => (
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

        {showBaselineData && filteredSignals?.map((signal) => (
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

        {showBaselineData && filteredAssets?.map((asset) => (
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

        {/* Backend map command highlights (priority-ordered) */}
        {showCommandOverlays && commandHighlightCircles?.map((highlight: any) => (
          <Circle
            key={`cmd-highlight-${highlight.id}`}
            center={[highlight.country.lat, highlight.country.lng]}
            radius={highlight.radius}
            pathOptions={{
              color: highlight.color,
              fillColor: highlight.color,
              fillOpacity: 0.13,
              weight: 3,
              className: highlight.pulse ? 'ai-highlight-pulse' : undefined,
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold" style={{ color: highlight.color }}>{highlight.country.name}</div>
                <div className="text-zinc-400">{highlight.description}</div>
                <div className="text-zinc-500">{highlight.source} · {highlight.priority}</div>
              </div>
            </Popup>
          </Circle>
        ))}

        {/* Backend map command heatmap */}
        {showCommandOverlays && commandHeatmapPoints?.map((point: any) => (
          <CircleMarker
            key={`cmd-heat-${point.id}`}
            center={[point.lat, point.lng]}
            radius={point.radius}
            pathOptions={{
              color: point.color,
              fillColor: point.color,
              fillOpacity: 0.32,
              weight: 2,
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold" style={{ color: point.color }}>{point.label}</div>
                <div className="text-zinc-400">{point.metric}: {point.valueLabel}%</div>
                <div className="text-zinc-500">{point.commandDescription}</div>
                <div className="text-zinc-500">{point.source} · {point.priority}</div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* Backend map command routes */}
        {showCommandOverlays && commandRoutes?.map((route: any) => (
          <Polyline
            key={`cmd-route-${route.id}`}
            positions={[
              [route.fromCountry.lat, route.fromCountry.lng],
              [route.toCountry.lat, route.toCountry.lng],
            ]}
            pathOptions={{
              color: route.color,
              weight: route.weight,
              opacity: 0.88,
              className: route.animated ? 'ai-route-animated' : undefined,
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold" style={{ color: route.color }}>
                  {route.fromCountry.name} -&gt; {route.toCountry.name}
                </div>
                <div className="text-zinc-400">{route.routeType}</div>
                <div className="text-zinc-500">{route.description}</div>
                <div className="text-zinc-500">{route.source} · {route.priority}</div>
              </div>
            </Popup>
          </Polyline>
        ))}

        {/* Backend map command markers */}
        {showCommandOverlays && commandMarkers?.map((marker: any) => (
          <Marker
            key={`cmd-marker-${marker.id}`}
            position={[marker.lat, marker.lng]}
            icon={createHighlightMarkerIcon({ type: marker.markerType }, marker.color, true)}
            riseOnHover
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold" style={{ color: marker.color }}>{marker.label}</div>
                <div className="text-zinc-400">{marker.description}</div>
                <div className="text-zinc-500">{marker.source} · {marker.priority}</div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Backend overlay impact points */}
        {showCommandOverlays && showScenarioOverlays && commandOverlayPoints?.map((point: any) => (
          <Circle
            key={`cmd-overlay-${point.id}`}
            center={[point.lat, point.lng]}
            radius={120000 + point.intensity * 260000}
            pathOptions={{
              color: '#f97316',
              fillColor: '#fb923c',
              fillOpacity: 0.12 + point.intensity * 0.18,
              weight: 2,
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold text-orange-300">{point.label}</div>
                <div className="text-zinc-400">Scenario impact: {Math.round(point.intensity * 100)}%</div>
                <div className="text-zinc-500">{point.description}</div>
                <div className="text-zinc-500">{point.source} · {point.priority}</div>
              </div>
            </Popup>
          </Circle>
        ))}

        {/* ═══════════════════════════════════════════════════════════════════════
            AI-DRIVEN MAP LAYERS (Expert Analysis Visualization)
            These layers are populated when expert analysis identifies countries,
            regions, or risks that should be visually highlighted on the map.
        ═══════════════════════════════════════════════════════════════════════ */}

        {/* Highlight Layer: Pulsing rings around countries mentioned in analysis */}
        {showExpertOverlays && expertMapLayers
          .filter((layer) => layer.type === 'highlight' && layer.visible !== false)
          .flatMap((layer) => {
            const countryIds = Array.isArray(layer.data) ? layer.data : [];
            return countryIds?.map((countryId: string) => {
              const country = countries.find((c) => c.id === countryId);
              if (!country || !hasCoords(country)) return null;
              return (
                <Circle
                  key={`ai-highlight-${countryId}`}
                  center={[country.lat, country.lng]}
                  radius={400000}
                  pathOptions={{
                    color: layer.color || '#3b82f6',
                    fillColor: layer.color || '#3b82f6',
                    fillOpacity: 0.15,
                    weight: 3,
                    dashArray: '8 4',
                    className: 'ai-highlight-pulse',
                  }}
                >
                  <Popup>
                    <div className="text-xs">
                      <div className="font-bold text-blue-400">{country.name}</div>
                      <div className="text-zinc-400">AI Focus: {layer.description || 'Mentioned in analysis'}</div>
                    </div>
                  </Popup>
                </Circle>
              );
            });
          })
          .filter(Boolean)}

        {/* Risk Heatmap Layer: Graduated circles based on risk scores */}
        {showExpertOverlays && expertMapLayers
          .filter((layer) => layer.type === 'risk_heatmap' && layer.visible !== false)
          .flatMap((layer) => {
            const riskData = layer.data as Record<string, { name: string; risk: number; relevant?: boolean }>;
            return Object.entries(riskData)?.map(([countryId, data]) => {
              const country = countries.find((c) => c.id === countryId);
              if (!country || !hasCoords(country)) return null;

              const riskScore = data.risk;
              const isRelevant = data.relevant;
              const color = riskScore >= 0.7 ? '#ef4444' : riskScore >= 0.4 ? '#f59e0b' : '#10b981';
              const radius = isRelevant ? 350000 : 200000 + riskScore * 150000;

              return (
                <CircleMarker
                  key={`ai-risk-${countryId}`}
                  center={[country.lat, country.lng]}
                  radius={isRelevant ? 18 : 10 + riskScore * 8}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: isRelevant ? 0.5 : 0.3,
                    weight: isRelevant ? 3 : 2,
                  }}
                >
                  <Popup>
                    <div className="text-xs">
                      <div className="font-bold" style={{ color }}>{data.name}</div>
                      <div className="text-zinc-400">Risk Score: {Math.round(riskScore * 100)}%</div>
                      {isRelevant && <div className="text-blue-400 mt-1">Mentioned in analysis</div>}
                    </div>
                  </Popup>
                </CircleMarker>
              );
            });
          })
          .filter(Boolean)}

        {/* Signal Density Layer: Concentric rings showing intelligence activity */}
        {showExpertOverlays && expertMapLayers
          .filter((layer) => layer.type === 'signal_density' && layer.visible !== false)
          .flatMap((layer) => {
            const densityData = layer.data as Record<string, { count: number; categories: Record<string, number> }>;
            return Object.entries(densityData)?.map(([countryId, data]) => {
              const country = countries.find((c) => c.id === countryId);
              if (!country || !hasCoords(country)) return null;

              const intensity = Math.min(data.count / 10, 1);
              return (
                <Circle
                  key={`ai-density-${countryId}`}
                  center={[country.lat, country.lng]}
                  radius={200000 + data.count * 30000}
                  pathOptions={{
                    color: '#60a5fa',
                    fillColor: '#3b82f6',
                    fillOpacity: 0.1 + intensity * 0.2,
                    weight: 1,
                  }}
                >
                  <Popup>
                    <div className="text-xs">
                      <div className="font-bold text-blue-400">{country.name}</div>
                      <div className="text-zinc-400">{data.count} active signals</div>
                      <div className="text-zinc-500 mt-1">
                        {Object.entries(data.categories)
                          .slice(0, 3)
                          ?.map(([cat, count]) => `${cat}: ${count}`)
                          .join(', ')}
                      </div>
                    </div>
                  </Popup>
                </Circle>
              );
            });
          })
          .filter(Boolean)}

        {/* Trade Route Layer: Highlighted corridors for trade analysis */}
        {showExpertOverlays && expertMapLayers
          .filter((layer) => layer.type === 'route' && layer.visible !== false)
          .flatMap((layer) => {
            const routeData = layer.data as Array<{
              id: string;
              start_lat: number;
              start_lng: number;
              end_lat: number;
              end_lng: number;
              label: string;
              status?: string;
            }>;
            if (!Array.isArray(routeData)) return [];
            return routeData.filter(hasCorridorCoords)?.map((route) => (
              <Polyline
                key={`ai-route-${route.id}`}
                positions={[
                  [route.start_lat, route.start_lng],
                  [route.end_lat, route.end_lng],
                ]}
                pathOptions={{
                  color: layer.color || '#10b981',
                  weight: layer.line_width || 4,
                  opacity: 0.85,
                  dashArray: route.status === 'disrupted' ? '10 5' : undefined,
                }}
              >
                <Popup>
                  <div className="text-xs">
                    <div className="font-bold text-emerald-400">{route.label}</div>
                    <div className="text-zinc-400">Trade Route Analysis</div>
                  </div>
                </Popup>
              </Polyline>
            ));
          })}

        {/* Auto-Focus on AI Regions */}
        <AIRegionFocus
          regions={expertAffectedRegions}
          countries={countries}
        />
      </MapContainer>

      {/* Expert Analysis Overlay Indicator */}
      {showExpertOverlays && expertMapLayers?.length > 0 && (
        <div className="pointer-events-none absolute top-3 left-3 z-[400] rounded-xl border border-purple-500/50 bg-purple-950/80 p-3 backdrop-blur-md">
          <div className="mb-2 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-purple-500 animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest text-purple-300">Expert Analysis Active</span>
          </div>
          <div className="space-y-1 text-[11px] text-purple-200">
            <div>{expertMapLayers?.length} visualization layer{expertMapLayers?.length > 1 ? 's' : ''}</div>
            {expertAffectedRegions?.length > 0 && (
              <div className="text-purple-400">
                Focus: {expertAffectedRegions.slice(0, 3).join(', ')}
                {expertAffectedRegions?.length > 3 && ` +${expertAffectedRegions?.length - 3} more`}
              </div>
            )}
          </div>
          <div className="mt-2 space-y-1">
            {expertMapLayers.slice(0, 4)?.map((layer, i) => (
              <div key={i} className="flex items-center gap-2 text-[10px]">
                <div
                  className="h-2 w-2 rounded-sm"
                  style={{ backgroundColor: layer.color || (layer.color_scale === 'red_gradient' ? '#ef4444' : '#3b82f6') }}
                />
                <span className="text-purple-300">{layer.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {showScenarioOverlays && scenarioOverlaySummary && (
        <div className="absolute top-3 left-1/2 z-[400] -translate-x-1/2 rounded-xl border border-orange-500/60 bg-orange-950/85 px-4 py-3 backdrop-blur-md">
          <div className="mb-2 flex items-center justify-between gap-4 text-[10px] uppercase tracking-widest text-orange-300">
            <span>Scenario Overlay</span>
            <button
              type="button"
              onClick={pinScenarioSnapshot}
              className="pointer-events-auto rounded border border-orange-400/60 bg-orange-900/70 px-2 py-0.5 text-[10px] tracking-normal text-orange-200 hover:bg-orange-800/80"
            >
              Pin Snapshot
            </button>
          </div>
          <div className="max-w-[460px] space-y-1 text-[11px]">
            <div className="font-semibold text-orange-200">{scenarioOverlaySummary.title}</div>
            {scenarioOverlaySummary.outcome && (
              <div className="text-orange-100/85">{scenarioOverlaySummary.outcome}</div>
            )}
            {scenarioOverlaySummary.scenarios?.length > 0 && (
              <div className="pt-1 text-orange-200/90">
                {scenarioOverlaySummary.scenarios?.map((scenario: ScenarioOverlaySummary['scenarios'][number], idx: number) => (
                  <div key={`${scenario.name}-${idx}`}>
                    {scenario.name}: {scenario.probability} · Severity {scenario.impactSeverity}/10
                  </div>
                ))}
              </div>
            )}
            <div className="pt-1 text-[10px] text-orange-300/80">
              {scenarioOverlaySummary.source} · {scenarioOverlaySummary.priority}
            </div>
          </div>
        </div>
      )}

      {pinnedScenarioSnapshots?.length > 0 && (
        <div className="absolute left-3 bottom-12 z-[410] w-[320px] rounded-xl border border-orange-700/70 bg-black/80 p-3 backdrop-blur-md">
          <div className="mb-2 text-[10px] uppercase tracking-widest text-orange-300">Pinned Scenario Snapshots</div>
          <div className="space-y-2 max-h-[180px] overflow-auto pr-1">
            {pinnedScenarioSnapshots?.map((snapshot) => (
              <div key={snapshot.id} className="rounded border border-orange-900/70 bg-orange-950/30 p-2 text-[11px]">
                <div className="mb-1 flex items-start justify-between gap-2">
                  <div className="font-semibold text-orange-200 leading-snug">{snapshot.title}</div>
                  <button
                    type="button"
                    onClick={() => unpinScenarioSnapshot(snapshot.id)}
                    className="pointer-events-auto rounded border border-orange-500/60 px-1.5 py-0.5 text-[10px] text-orange-300 hover:bg-orange-900/50"
                  >
                    Unpin
                  </button>
                </div>
                {snapshot.outcome && <div className="text-orange-100/85">{snapshot.outcome}</div>}
                <div className="mt-1 text-[10px] text-orange-300/80">{snapshot.source} · {snapshot.priority}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showBaselineData && (
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
      )}

      <div className="pointer-events-none absolute bottom-3 left-3 z-[400] rounded-md border border-zinc-800 bg-black/60 px-2 py-1 font-mono text-[10px] text-zinc-500 backdrop-blur-sm">
        Updated {lastUpdated}
      </div>
    </div>
  );
};
