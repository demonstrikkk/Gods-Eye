import React from 'react';
import ReactCompareImage from 'react-compare-image';
import { Megaphone, MapPin, Camera } from 'lucide-react';

interface ProjectData {
    id: string;
    name: string;
    street: string;
    status: string;
    affected_residents: number;
    sentiment_before: number;
    sentiment_after: number;
}

interface BeforeAfterSliderProps {
    project: ProjectData;
    beforeImage: string;
    afterImage: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({ project, beforeImage, afterImage }) => {
    return (
        <div className="bg-panel border border-border/50 rounded-xl overflow-hidden shadow-lg mt-4 group">
            {/* Image Comparison Container */}
            <div className="relative h-[250px] w-full border-b border-border/50 cursor-ew-resize">
                <ReactCompareImage 
                    leftImage={beforeImage} 
                    rightImage={afterImage} 
                    leftImageLabel="BEFORE"
                    rightImageLabel="AFTER"
                    sliderLineColor="#3b82f6"
                    sliderLineWidth={3}
                />
                
                {/* Micro-Accountability Overlays */}
                <div className="absolute top-3 left-3 bg-danger/90 text-white text-[10px] font-black px-2 py-1 rounded shadow-lg backdrop-blur flex items-center z-10">
                    <span className="mr-1">Sentiment:</span> {project.sentiment_before}%
                </div>
                <div className="absolute top-3 right-3 bg-success/90 text-white text-[10px] font-black px-2 py-1 rounded shadow-lg backdrop-blur flex items-center z-10">
                    <span className="mr-1">Sentiment:</span> {project.sentiment_after}%
                </div>
            </div>

            {/* Outreach Trigger Footer */}
            <div className="p-4 flex items-center justify-between bg-background/50">
                <div className="flex flex-col">
                    <span className="text-[10px] text-text-muted font-bold tracking-widest uppercase mb-1 flex items-center">
                        <Camera size={12} className="mr-1" /> Verified Resolution
                    </span>
                    <span className="text-sm font-black text-text-main flex items-center">
                        <MapPin size={14} className="text-primary-light mr-1" /> {project.street}
                    </span>
                </div>
                
                <button 
                    className="flex items-center space-x-2 bg-primary/20 hover:bg-primary border border-primary/50 text-white text-xs font-bold px-4 py-2 rounded-lg transition-all shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                    onClick={() => alert(`Micro-targeted broadcast sent to ${project.affected_residents} residents on ${project.street}.`)}
                >
                    <Megaphone size={14} className="animate-pulse" />
                    <span>Notify {project.affected_residents} Residents</span>
                </button>
            </div>
        </div>
    );
};
