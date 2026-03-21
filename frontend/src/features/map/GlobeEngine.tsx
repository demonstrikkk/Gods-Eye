import React, { useEffect, useMemo, useRef } from 'react';
import Globe from 'react-globe.gl';
import { useQuery } from '@tanstack/react-query';
import {
  fetchGlobalCorridors,
  fetchGlobalCountries,
  fetchGlobalSignals,
  fetchNews,
} from '@/services/api';
import { useAppStore } from '@/store';

interface GlobeEngineProps {
  width: number;
  height: number;
}

const countryColor = (risk: number) =>
  risk >= 70 ? '#ef4444' : risk >= 50 ? '#f59e0b' : '#10b981';

const severityColor = (severity: string) =>
  severity === 'High' ? '#ef4444' : severity === 'Medium' ? '#38bdf8' : '#c084fc';

const economicCategories = new Set(['Economics', 'Trade', 'Industry', 'Finance']);
const climateCategories = new Set(['Climate']);
const defenseCategories = new Set(['Defense', 'Geopolitics']);

export const GlobeEngine: React.FC<GlobeEngineProps> = ({ width, height }) => {
  const globeRef = useRef<any>(null);
  const { activeLayers, setSelected, setSidebarTab } = useAppStore();

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

  useEffect(() => {
    if (!globeRef.current) return;
    globeRef.current.pointOfView({ lat: 20, lng: 30, altitude: 1.65 }, 1800);
    const controls = globeRef.current.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.25;

    const stopRotate = () => {
      controls.autoRotate = false;
    };

    const canvas = globeRef.current.renderer().domElement;
    canvas.addEventListener('mousedown', stopRotate);
    canvas.addEventListener('touchstart', stopRotate);
    return () => {
      canvas.removeEventListener('mousedown', stopRotate);
      canvas.removeEventListener('touchstart', stopRotate);
    };
  }, []);

  const countryPoints = useMemo(
    () =>
      activeLayers.has('countries')
        ? countries.map((country: any) => ({
            ...country,
            color: countryColor(country.risk_index),
            size: Math.max(0.35, country.influence_index / 90),
            label: `${country.name} | Risk ${country.risk_index} | Influence ${country.influence_index}`,
            type: 'country',
          }))
        : [],
    [countries, activeLayers],
  );

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

  const signalPoints = useMemo(
    () =>
      filteredSignals.map((signal: any) => ({
        ...signal,
        color: severityColor(signal.severity),
        size: signal.severity === 'High' ? 0.28 : 0.22,
        label: `${signal.title} | ${signal.category} | ${signal.severity}`,
        type: 'signal',
      })),
    [filteredSignals],
  );

  const arcsData = useMemo(
    () =>
      activeLayers.has('corridors')
        ? corridors.map((corridor: any) => ({
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
            .slice()
            .sort((a: any, b: any) => b.active_signals - a.active_signals)
            .slice(0, 6)
            .map((country: any, index: number) => ({
              lat: country.lat,
              lng: country.lng,
              text: feeds[index]?.text?.slice(0, 42) || `${country.name}: signal density rising`,
              size: 1.2,
              color: '#67e8f9',
            }))
        : [],
    [countries, feeds, activeLayers],
  );

  const handlePointClick = (point: any) => {
    if (point?.type === 'country') {
      setSelected(point.id, 'country');
      setSidebarTab('global');
      return;
    }
    if (point?.type === 'signal') {
      setSelected(point.id, 'signal');
      setSidebarTab('alerts');
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
      showAtmosphere
      atmosphereColor="#38bdf8"
      atmosphereAltitude={0.16}
      pointsData={[...countryPoints, ...signalPoints]}
      pointLat="lat"
      pointLng="lng"
      pointColor="color"
      pointRadius="size"
      pointAltitude={0.015}
      pointLabel="label"
      onPointClick={handlePointClick}
      arcsData={arcsData}
      arcColor="color"
      arcDashLength={0.35}
      arcDashGap={0.18}
      arcDashAnimateTime={1600}
      arcStroke={0.55}
      arcAltitudeAutoScale={0.45}
      arcLabel={(arc: any) => `${arc.label} | ${arc.from_name} -> ${arc.to_name}`}
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
