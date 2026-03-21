import React, { useEffect, useRef, useState, useMemo } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';

interface Point {
    lat: number;
    lng: number;
    population: number;
    sentiment: number;
    name: string;
    constituency: string;
}

interface Globe3DProps {
    data: Point[];
}

export const Globe3D: React.FC<Globe3DProps> = ({ data = [] }) => {
    const globeRef = useRef<any>();
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        };

        window.addEventListener('resize', updateDimensions);
        updateDimensions();

        // Focus on India (Lat: 20.5937, Lng: 78.9629) on load
        if (globeRef.current) {
            globeRef.current.pointOfView({ lat: 22, lng: 80, altitude: 0.8 }, 2000);
            
            // Auto-rotate setup
            const controls = globeRef.current.controls();
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.5;
            controls.enableZoom = false; // Disable zoom so it stays framed
        }

        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    // Format data for Globe
    const globeData = useMemo(() => {
        return data.map(d => ({
            lat: d.lat,
            lng: d.lng,
            size: Math.max(d.population / 10000, 0.5), // Scale dot size
            color: d.sentiment < 40 ? '#ef4444' : d.sentiment < 60 ? '#eab308' : '#10b981', // Red/Yellow/Green
            name: d.name,
            constituency: d.constituency,
            sentiment: d.sentiment
        }));
    }, [data]);

    const [geoEvents, setGeoEvents] = useState<any[]>([]);
    const [fires, setFires] = useState<any[]>([]);
    const [quakes, setQuakes] = useState<any[]>([]);

    useEffect(() => {
        // Fetch OSINT mandated layers for the geopolitical mapping
        const loadLayers = async () => {
            try {
                const [evtRes, fireRes, quakesRes] = await Promise.all([
                    fetch('/api/v1/data/geopolitical/events').then(r => r.json()),
                    fetch('/api/v1/data/fires').then(r => r.json()),
                    fetch('/api/v1/data/earthquakes').then(r => r.json()),
                ]);
                if (evtRes.data) setGeoEvents(evtRes.data);
                if (fireRes.data?.hotspots) setFires(fireRes.data.hotspots);
                if (quakesRes.data) setQuakes(quakesRes.data);
            } catch (e) {
                console.error("Layer load failed", e);
            }
        };
        loadLayers();
    }, []);

    // Rings for Earthquakes
    const ringsData = useMemo(() => quakes.map(q => ({
        lat: q.lat, lng: q.lng, color: '#f59e0b', maxR: q.magnitude * 2, propagationSpeed: 2, repeatPeriod: 1000
    })), [quakes]);

    // Arcs for Events (randomized destination just to look cool)
    const arcsData = useMemo(() => geoEvents.map(e => ({
        startLat: e.lat, startLng: e.lng,
        endLat: e.lat + (Math.random() - 0.5) * 20, endLng: e.lng + (Math.random() - 0.5) * 20,
        color: ['#8b5cf6', '#d946ef'],
    })), [geoEvents]);

    return (
        <div ref={containerRef} className="w-full h-full relative flex items-center justify-center overflow-hidden">
            {dimensions.width > 0 && (
                <Globe
                    ref={globeRef}
                    width={dimensions.width}
                    height={dimensions.height}
                    globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
                    bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
                    backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
                    pointsData={[...globeData, ...(fires?.map(f => ({ lat: f.lat, lng: f.lng, size: 0.8, color: '#ef4444', name: 'FIRE' })) || [])]}
                    pointLat="lat"
                    pointLng="lng"
                    pointColor="color"
                    pointAltitude={0.01}
                    pointRadius="size"
                    pointsMerge={true}
                    ringsData={ringsData}
                    ringColor="color"
                    ringMaxRadius="maxR"
                    ringPropagationSpeed="propagationSpeed"
                    ringRepeatPeriod="repeatPeriod"
                    arcsData={arcsData}
                    arcColor="color"
                    arcDashLength={0.4}
                    arcDashGap={0.2}
                    arcDashAnimateTime={1500}
                    pointResolution={16}
                    labelsData={globeData.filter((d: any) => d.sentiment < 40)} // Only label critical
                    labelLat="lat"
                    labelLng="lng"
                    labelDotRadius={0.5}
                    labelDotOrientation={() => 'right'}
                    labelColor={() => 'rgba(255, 255, 255, 0.75)'}
                    labelText="constituency"
                    labelSize={1.5}
                    labelResolution={2}
                />
            )}
            
            <div className="absolute bottom-4 left-4 bg-background/80 border border-border/40 p-3 rounded-lg backdrop-blur-sm pointer-events-none">
                <div className="text-[10px] font-mono text-text-muted uppercase mb-2">Sentiment Heatmap Legend</div>
                <div className="flex items-center gap-3">
                    <span className="flex items-center text-xs"><span className="w-2 h-2 rounded-full bg-success mr-1"></span> &gt;60</span>
                    <span className="flex items-center text-xs"><span className="w-2 h-2 rounded-full bg-warning mr-1"></span> 40-60</span>
                    <span className="flex items-center text-xs"><span className="w-2 h-2 rounded-full bg-danger mr-1 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span> &lt;40</span>
                </div>
            </div>
        </div>
    );
};
