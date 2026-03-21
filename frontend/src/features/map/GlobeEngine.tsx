// ─────────────────────────────────────────────────────────────────────────────
// GlobeEngine — 3D Globe with multi-layer support
// Layers: sentiment dots, geo events (arcs), fires (red), earthquake rings
// ─────────────────────────────────────────────────────────────────────────────

import React, { useEffect, useRef, useMemo } from 'react';
import Globe from 'react-globe.gl';
import { useQuery } from '@tanstack/react-query';
import {
  fetchSentimentHeatmap, fetchEvents, fetchFires, fetchEarthquakes, fetchNews
} from '@/services/api';
import { useAppStore } from '@/store';

interface GlobeEngineProps {
  width: number;
  height: number;
}

const sentimentColor = (s: number) =>
  s < 35 ? '#ef4444' : s < 55 ? '#f59e0b' : '#10b981';

export const GlobeEngine: React.FC<GlobeEngineProps> = ({ width, height }) => {
  const globeRef = useRef<any>(null);
  const { activeLayers, setSelected, setSidebarTab } = useAppStore();

  // ── Data Queries ──────────────────────────────────────────────────────────
  const { data: heatmap = [] } = useQuery({
    queryKey: ['heatmap'],
    queryFn: fetchSentimentHeatmap,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: events = [] } = useQuery({
    queryKey: ['events'],
    queryFn: fetchEvents,
    refetchInterval: 120_000,
    staleTime: 90_000,
    enabled: activeLayers.has('events'),
  });

  const { data: firesRaw } = useQuery({
    queryKey: ['fires'],
    queryFn: fetchFires,
    refetchInterval: 120_000,
    enabled: activeLayers.has('fires'),
  });

  const { data: quakes = [] } = useQuery({
    queryKey: ['earthquakes'],
    queryFn: fetchEarthquakes,
    refetchInterval: 120_000,
    enabled: activeLayers.has('earthquakes'),
  });

  const { data: newsItems = [] } = useQuery({
    queryKey: ['news'],
    queryFn: fetchNews,
    refetchInterval: 60_000,
    enabled: activeLayers.has('news'),
  });

  // ── Camera setup ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!globeRef.current) return;
    globeRef.current.pointOfView({ lat: 22, lng: 80, altitude: 1.2 }, 1800);
    const ctrl = globeRef.current.controls();
    ctrl.autoRotate = true;
    ctrl.autoRotateSpeed = 0.4;

    // Stop rotation on interaction
    const stopRotate = () => {
      if (ctrl.autoRotate) {
        ctrl.autoRotate = false;
      }
    };
    
    // The renderer's domElement is the canvas where events happen
    const canvas = globeRef.current.renderer().domElement;
    canvas.addEventListener('mousedown', stopRotate);
    canvas.addEventListener('touchstart', stopRotate);

    return () => {
      canvas.removeEventListener('mousedown', stopRotate);
      canvas.removeEventListener('touchstart', stopRotate);
    };
  }, []);

  // ── Layer data (memoised) ─────────────────────────────────────────────────
  const sentimentPoints = useMemo(() =>
    activeLayers.has('sentiment') && Array.isArray(heatmap)
      ? heatmap.map((d: any) => ({
          lat: d.lat, lng: d.lng,
          size: Math.max((d.population || 5000) / 12000, 0.3),
          color: sentimentColor(d.sentiment),
          label: `${d.name} · ${d.sentiment}%`,
          id: d.id, type: 'booth',
        }))
      : [],
    [heatmap, activeLayers]
  );

  const firePoints = useMemo(() => {
    if (!activeLayers.has('fires')) return [];
    const hotspots = firesRaw?.hotspots ?? (Array.isArray(firesRaw) ? firesRaw : []);
    return hotspots.map((f: any, i: number) => ({
      lat: f.lat, lng: f.lng, size: 0.5, color: '#f97316',
      label: `Fire · ${f.confidence ?? 'detected'}`, id: `fire-${i}`, type: 'fire',
    }));
  }, [firesRaw, activeLayers]);

  const allPoints = useMemo(() => [...sentimentPoints, ...firePoints], [sentimentPoints, firePoints]);

  const arcsData = useMemo(() =>
    activeLayers.has('events') && Array.isArray(events)
      ? events.slice(0, 30).map((e: any) => ({
          startLat: e.lat, startLng: e.lng,
          endLat: e.lat + (Math.random() - 0.5) * 12,
          endLng: e.lng + (Math.random() - 0.5) * 12,
          color: ['#8b5cf6', '#a78bfa'],
          label: e.title,
          id: e.id,
        }))
      : [],
    [events, activeLayers]
  );

  const ringsData = useMemo(() =>
    activeLayers.has('earthquakes') && Array.isArray(quakes)
      ? quakes.map((q: any) => ({
          lat: q.lat, lng: q.lng,
          maxR: (q.magnitude ?? 4) * 2.5,
          color: '#fbbf24',
          propagationSpeed: 2.5,
          repeatPeriod: 1200,
          label: `M${q.magnitude} · ${q.location}`,
        }))
      : [],
    [quakes, activeLayers]
  );

  const newsPoints = useMemo(() =>
    activeLayers.has('news') && Array.isArray(newsItems)
      ? newsItems.filter((n: any) => n.lat && n.lng).map((n: any) => ({
          lat: n.lat, lng: n.lng,
          text: n.text?.slice(0, 40) ?? '',
          size: 1.2, color: '#22d3ee',
        }))
      : [],
    [newsItems, activeLayers]
  );

  const handlePointClick = (point: any) => {
    if (point?.type === 'booth') {
      setSelected(point.id, 'booth');
      setSidebarTab('booths');
    }
  };

  return (
    <Globe
      ref={globeRef}
      width={width}
      height={height}
      globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
      bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
      backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
      
      // Atmosphere
      showAtmosphere={true}
      atmosphereColor="#3b82f6"
      atmosphereAltitude={0.15}

      // Sentiment + fire points
      pointsData={allPoints}
      pointLat="lat"
      pointLng="lng"
      pointColor="color"
      pointRadius="size"
      pointAltitude={0.015}
      pointsMerge={false}
      pointLabel="label"
      onPointClick={handlePointClick}
      
      // Event arcs
      arcsData={arcsData}
      arcColor="color"
      arcDashLength={0.4}
      arcDashGap={0.2}
      arcDashAnimateTime={1500}
      arcStroke={0.5}
      arcAltitudeAutoScale={0.5}
      arcLabel="label"

      // Earthquake rings
      ringsData={ringsData}
      ringColor="color"
      ringMaxRadius="maxR"
      ringPropagationSpeed="propagationSpeed"
      ringRepeatPeriod="repeatPeriod"

      // News labels
      labelsData={newsPoints}
      labelLat="lat"
      labelLng="lng"
      labelText="text"
      labelSize="size"
      labelColor="color"
      labelDotRadius={0.4}
      labelAltitude={0.01}
    />
  );
};
