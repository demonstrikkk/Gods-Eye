import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

interface Node {
    id: string;
    group: string;
    label: string;
    val: number;
    color?: string;
    segment?: string;
}

interface Link {
    source: string;
    target: string;
    label: string;
}

interface GraphData {
    nodes: Node[];
    links: Link[];
}

interface OntologyGraphProps {
    data: GraphData;
}

export const OntologyGraph: React.FC<OntologyGraphProps> = ({ data }) => {
    const fgRef = useRef<any>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

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
        
        // Initial zoom to fit after short delay
        setTimeout(() => {
            if (fgRef.current) {
                fgRef.current.zoomToFit(400, 50);
            }
        }, 800);

        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    // Custom node styling
    const getNodeColor = (node: Node) => {
        if (node.color) return node.color;
        switch (node.group) {
            case 'Scheme': return '#a855f7'; // Purple
            case 'Issue': return '#eab308'; // Yellow
            case 'Booth': return '#3b82f6'; // Blue
            case 'Citizen': return '#9ca3af'; // Gray
            default: return '#ffffff';
        }
    };

    return (
        <div ref={containerRef} className="w-full h-full relative cursor-crosshair">
            <ForceGraph2D
                ref={fgRef}
                width={dimensions.width}
                height={dimensions.height}
                graphData={data}
                nodeAutoColorBy="group"
                nodeColor={getNodeColor}
                nodeRelSize={4}
                nodeLabel="label"
                linkColor={() => '#3f3f46'} // Zinc 700
                linkWidth={0.5}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalArrowLength={2}
                linkDirectionalArrowRelPos={1}
                onNodeClick={(node) => {
                    if (fgRef.current) {
                        fgRef.current.centerAt(node.x, node.y, 1000);
                        fgRef.current.zoom(4, 2000);
                    }
                }}
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                    const label = node.label;
                    const fontSize = 12 / globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;
                    
                    // Draw node
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, node.val, 0, 2 * Math.PI, false);
                    ctx.fillStyle = getNodeColor(node as Node);
                    ctx.fill();

                    // Draw text label on top
                    if (globalScale > 1.5 || node.group !== 'Citizen') {
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                        ctx.fillText(label, node.x, node.y + node.val + fontSize);
                    }
                }}
            />
            
            {/* Legend Overlay */}
            <div className="absolute top-4 right-4 bg-background/90 p-3 rounded border border-border/50 text-xs shadow-lg backdrop-blur-md">
                <div className="font-bold mb-2 uppercase text-text-muted tracking-widest text-[10px]">Graph Legend</div>
                <div className="flex items-center gap-2 mb-1"><div className="w-3 h-3 rounded-full bg-purple-500"></div> Government Scheme</div>
                <div className="flex items-center gap-2 mb-1"><div className="w-3 h-3 rounded-full bg-yellow-500"></div> Critical Issue</div>
                <div className="flex items-center gap-2 mb-1"><div className="w-3 h-3 rounded-full bg-blue-500"></div> Polling Booth</div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-gray-400"></div> Citizen</div>
            </div>
        </div>
    );
};
