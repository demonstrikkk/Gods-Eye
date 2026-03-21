// ─────────────────────────────────────────────────────────────────────────────
// JanGraph OS — Zustand Global Store
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand';
import type { MapMode, LayerKey, SidebarTab } from '@/types';

export type ActiveView =
  | 'cockpit'
  | 'executive'
  | 'strategic'
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
  selectedType: 'booth' | 'event' | 'fire' | 'quake' | 'news' | null;
  setSelected: (id: string | null, type: AppState['selectedType']) => void;

  // Active view (cockpit mode)
  activeView: ActiveView;
  setActiveView: (view: ActiveView) => void;

  // Hover popup
  hoveredItem: any | null;
  setHoveredItem: (item: any | null) => void;

  // Agent Handoff
  pendingAgentQuery: string | null;
  pendingAgentMode: 'standard' | 'strategic' | 'news';
  setPendingAgentQuery: (query: string, mode: 'standard' | 'strategic' | 'news') => void;
  clearPendingAgentQuery: () => void;

  // Sidebar
  sidebarTab: SidebarTab;
  setSidebarTab: (tab: SidebarTab) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Map defaults
  mapMode: 'globe',
  setMapMode: (mode) => set({ mapMode: mode }),

  // All layers on by default
  activeLayers: new Set<LayerKey>(['sentiment', 'events', 'fires', 'earthquakes', 'news']),
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
  sidebarTab: 'booths',
  setSidebarTab: (tab) => set({ sidebarTab: tab }),
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
