// ─────────────────────────────────────────────────────────────────────────────
// JanGraph OS — Zustand Global Store
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand';
import type { MapMode, LayerKey, SidebarTab } from '@/types';

export type ActiveView =
  | 'cockpit'
  | 'executive'
  | 'strategic'
  | 'expert'
  | 'constituency'
  | 'workers'
  | 'schemes'
  | 'comms'
  | 'alerts'
  | 'ontology';

interface AppState {
  // Map
  mapMode: MapMode;
  setMapMode: (mode: MapMode) => void;

  // Layers
  activeLayers: Set<LayerKey>;
  toggleLayer: (key: LayerKey) => void;
  setLayerActive: (key: LayerKey, active: boolean) => void;

  // Selection
  selectedId: string | null;
  selectedType: 'country' | 'signal' | 'asset' | 'booth' | 'event' | 'fire' | 'quake' | 'news' | null;
  setSelected: (id: string | null, type: AppState['selectedType']) => void;

  // Active view (cockpit mode)
  activeView: ActiveView;
  setActiveView: (view: ActiveView) => void;

  // Hover popup
  hoveredItem: any | null;
  setHoveredItem: (item: any | null) => void;

  // Agent Handoff
  pendingAgentQuery: string | null;
  pendingAgentMode: 'standard' | 'strategic' | 'news' | 'expert';
  setPendingAgentQuery: (query: string, mode: 'standard' | 'strategic' | 'news' | 'expert') => void;
  clearPendingAgentQuery: () => void;

  // Sidebar
  sidebarTab: SidebarTab;
  setSidebarTab: (tab: SidebarTab) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  // Expert Analysis Map Visualization
  expertMapLayers: Array<{
    type: string;
    name: string;
    description?: string;
    data: any;
    color?: string;
    color_scale?: string;
    visible?: boolean;
  }>;
  expertAffectedRegions: string[];
  setExpertMapLayers: (layers: AppState['expertMapLayers'], regions?: string[]) => void;
  clearExpertMapLayers: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Map defaults
  mapMode: 'globe',
  setMapMode: (mode) => set({ mapMode: mode }),

  // All layers on by default
  activeLayers: new Set<LayerKey>([
    'countries',
    'corridors',
    'economics',
    'governance',
    'climate',
    'defense',
    'conflict',
    'infrastructure',
    'mobility',
    'cyber',
    'news',
  ]),
  toggleLayer: (key) =>
    set((state) => {
      const next = new Set(state.activeLayers);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return { activeLayers: next };
    }),
  setLayerActive: (key, active) =>
    set((state) => {
      const next = new Set(state.activeLayers);
      if (active) next.add(key);
      else next.delete(key);
      return { activeLayers: next };
    }),

  // Selection
  selectedId: null,
  selectedType: null,
  setSelected: (id, type) => set({ selectedId: id, selectedType: type }),

  // Active view
  activeView: 'cockpit',
  setActiveView: (view) => set({ activeView: view }),

  // Hover popup
  hoveredItem: null,
  setHoveredItem: (item) => set({ hoveredItem: item }),

  // Agent Handoff
  pendingAgentQuery: null,
  pendingAgentMode: 'strategic',
  setPendingAgentQuery: (query, mode) => set({ pendingAgentQuery: query, pendingAgentMode: mode }),
  clearPendingAgentQuery: () => set({ pendingAgentQuery: null }),

  // Sidebar
  sidebarTab: 'global',
  setSidebarTab: (tab) => set({ sidebarTab: tab }),
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Expert Analysis Map Visualization
  expertMapLayers: [],
  expertAffectedRegions: [],
  setExpertMapLayers: (layers, regions = []) => set({ expertMapLayers: layers, expertAffectedRegions: regions }),
  clearExpertMapLayers: () => set({ expertMapLayers: [], expertAffectedRegions: [] }),
}));
