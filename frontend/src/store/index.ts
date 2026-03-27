// ─────────────────────────────────────────────────────────────────────────────
// Gods-Eye OS — Zustand Global Store
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand';
import type {
  MapMode,
  LayerKey,
  SidebarTab,
  UnifiedIntelligenceResponse,
  CockpitState,
} from '@/types';

const MAX_MAP_COMMANDS = 450;

const createdAtMs = (value?: string): number => {
  const parsed = Date.parse(value || '');
  return Number.isNaN(parsed) ? 0 : parsed;
};

function normalizeMapCommands<T extends { id: string; created_at?: string }>(commands: T[]): T[] {
  if (!commands.length) return [];
  const byId = new Map<string, T>();
  for (const command of commands) {
    byId.set(command.id, command);
  }
  const deduped = Array.from(byId.values()).sort((left, right) => {
    return createdAtMs(left.created_at) - createdAtMs(right.created_at);
  });
  return deduped.slice(-MAX_MAP_COMMANDS);
}

function appendMapCommand<T extends { id: string; created_at?: string }>(commands: T[], command: T): T[] {
  if (!commands.length) return [command];

  const next = [...commands];
  const existingIndex = next.findIndex((item) => item.id === command.id);

  if (existingIndex >= 0) {
    next[existingIndex] = command;
    next.sort((left, right) => createdAtMs(left.created_at) - createdAtMs(right.created_at));
    return next.slice(-MAX_MAP_COMMANDS);
  }

  const lastTimestamp = createdAtMs(next[next.length - 1]?.created_at);
  const incomingTimestamp = createdAtMs(command.created_at);
  next.push(command);
  if (incomingTimestamp < lastTimestamp) {
    next.sort((left, right) => createdAtMs(left.created_at) - createdAtMs(right.created_at));
  }

  return next.slice(-MAX_MAP_COMMANDS);
}

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
  liteMode: boolean;
  setLiteMode: (value: boolean) => void;

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

  cockpitState: CockpitState | null;
  setCockpitState: (value: CockpitState | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Map defaults
  mapMode: 'globe',
  setMapMode: (mode) => set({ mapMode: mode }),
  liteMode: false,
  setLiteMode: (value) => set({ liteMode: value, mapMode: value ? 'flat' : 'globe' }),

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
  sidebarTab: 'unified',
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
  setMapCommands: (commands) => set({ mapCommands: normalizeMapCommands(commands) }),
  addMapCommand: (command) => set((state) => ({ mapCommands: appendMapCommand(state.mapCommands, command) })),
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
  cockpitState: null,
  setCockpitState: (value) => set({ cockpitState: value }),
}));
