// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — Zustand Global Store
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand';
import type {
  MapMode,
  LayerKey,
  SidebarTab,
  UnifiedIntelligenceResponse,
} from '@/types';

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
    line_width?: number;
    visible?: boolean;
  }>;
  expertAffectedRegions: string[];
  setExpertMapLayers: (layers: AppState['expertMapLayers'], regions?: string[]) => void;
  setAffectedRegions: (regions: string[]) => void;
  clearExpertMapLayers: () => void;

  // Map Commands (from backend)
  mapCommands: Array<{
    id: string;
    command_type: string;
    priority: string;
    data: any;
    description: string;
    source: string;
    created_at: string;
  }>;
  setMapCommands: (commands: AppState['mapCommands']) => void;
  addMapCommand: (command: AppState['mapCommands'][0]) => void;
  removeMapCommand: (commandId: string) => void;
  clearMapCommands: () => void;

  // Unified assistant conversation
  unifiedConversationId: string | null;
  unifiedMessages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    response?: UnifiedIntelligenceResponse;
    status?: 'pending' | 'done' | 'error';
  }>;
  setUnifiedConversationId: (conversationId: string | null) => void;
  addUnifiedMessage: (message: AppState['unifiedMessages'][0]) => void;
  replaceUnifiedMessage: (messageId: string, message: Partial<AppState['unifiedMessages'][0]>) => void;
  clearUnifiedConversation: () => void;
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
  setAffectedRegions: (regions) => set({ expertAffectedRegions: regions }),
  clearExpertMapLayers: () => set({ expertMapLayers: [], expertAffectedRegions: [] }),

  // Map Commands
  mapCommands: [],
  setMapCommands: (commands) => set({ mapCommands: commands }),
  addMapCommand: (command) => set((state) => ({ mapCommands: [...state.mapCommands, command] })),
  removeMapCommand: (commandId) => set((state) => ({
    mapCommands: state.mapCommands.filter((cmd) => cmd.id !== commandId),
  })),
  clearMapCommands: () => set({ mapCommands: [] }),

  // Unified assistant conversation
  unifiedConversationId: null,
  unifiedMessages: [],
  setUnifiedConversationId: (conversationId) => set({ unifiedConversationId: conversationId }),
  addUnifiedMessage: (message) => set((state) => ({ unifiedMessages: [...state.unifiedMessages, message] })),
  replaceUnifiedMessage: (messageId, message) => set((state) => ({
    unifiedMessages: state.unifiedMessages.map((item) => (
      item.id === messageId ? { ...item, ...message } : item
    )),
  })),
  clearUnifiedConversation: () => set({ unifiedConversationId: null, unifiedMessages: [] }),
}));
