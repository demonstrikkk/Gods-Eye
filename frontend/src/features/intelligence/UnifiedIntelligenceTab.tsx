import { startTransition, useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Database,
  Download,
  FileUp,
  Lock,
  Loader2,
  Map as MapIcon,
  MessageSquare,
  Wand2,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
  Brain,
  ChevronRight,
  X,
} from 'lucide-react';
import { postUnifiedIntelligence, streamUnifiedIntelligence } from '@/services/api';
import { GeneratedChartArtifact } from '@/components/intelligence/GeneratedChartArtifact';
import { useAppStore } from '@/store';
import type {
  UnifiedIntelligenceResponse,
  UnifiedConversationMessageInput,
  UnifiedCapabilityType,
  UnifiedExecutionMode,
} from '@/types';

type ThreadMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  response?: UnifiedIntelligenceResponse;
  status?: 'pending' | 'done' | 'error';
};

const EXAMPLE_PROMPTS = [
  'Build a full strategic brief on India-China competition with charts and map context',
  'What changed in global AI regulation trends and what matters next?',
  'Compare energy, trade, and geopolitical risk exposure across India, China, and Europe',
];

type StoreMapCommand = {
  id: string;
  command_type: string;
  priority: string;
  data: Record<string, unknown>;
  description: string;
  source: string;
  created_at: string;
};

type CommandPayload = Record<string, unknown>;

type UploadedLocalFile = {
  id: string;
  name: string;
  mimeType: string;
  size: number;
  uploadedAt: string;
  summary: string;
  excerpt: string;
};

type ModularSegment =
  | { type: 'markdown'; content: string }
  | { type: 'box'; title: string; content: string }
  | { type: 'card'; cardType: string; title: string; content: string }
  | { type: 'chart'; chartType: 'line' | 'bar' | 'pie'; title: string; data: Array<Record<string, unknown>> };

type ModePreset = {
  id: UnifiedExecutionMode;
  label: string;
  summary: string;
  manualDefault?: UnifiedCapabilityType[];
};

const MODE_PRESETS: ModePreset[] = [
  { id: 'auto', label: 'Auto', summary: 'Use smart capability selection.' },
  { id: 'fast', label: 'Fast', summary: 'Low-latency source fetch + 1-2 agent brief.' },
  { id: 'visual_only', label: 'Graph', summary: 'Generate charts/graph output only.' },
  { id: 'reasoning_only', label: 'Reasoning', summary: 'Reasoning-only analysis mode.' },
  { id: 'tools_only', label: 'Data', summary: 'Fetch and return source-grounded data only.' },
  { id: 'map_only', label: 'Map', summary: 'Geospatial/map capability only.' },
  { id: 'manual', label: 'Manual', summary: 'Pick capabilities manually.', manualDefault: ['visuals'] },
];

const CAPABILITY_OPTIONS: Array<{ id: UnifiedCapabilityType; label: string }> = [
  { id: 'reasoning', label: 'Reasoning' },
  { id: 'tools', label: 'Tools' },
  { id: 'visuals', label: 'Visuals' },
  { id: 'map', label: 'Map' },
];

const MAX_LOCAL_EXCERPT_CHARS = 4500;
const CHART_SWATCH = ['#06b6d4', '#22c55e', '#6366f1', '#f59e0b', '#ef4444', '#a855f7'];

const parseTagAttributes = (raw: string): Record<string, string> => {
  const attrs: Record<string, string> = {};
  const attrRegex = /([a-zA-Z_][\w-]*)=("([^"]*)"|\{([\s\S]*?)\})/g;
  let match: RegExpExecArray | null;
  while ((match = attrRegex.exec(raw)) !== null) {
    attrs[match[1]] = (match[3] ?? match[4] ?? '').trim();
  }
  return attrs;
};

const parseChartData = (value: string | undefined, fallbackBody: string): Array<Record<string, unknown>> => {
  const candidate = (value && value.trim()) || fallbackBody.trim();
  if (!candidate) return [];
  try {
    const parsed = JSON.parse(candidate);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const normalizeTextInput = (input: unknown): string => {
  if (typeof input === 'string') return input;
  if (input == null) return '';
  if (typeof input === 'number' || typeof input === 'boolean') return String(input);
  try {
    return JSON.stringify(input, null, 2);
  } catch {
    return String(input);
  }
};

const parseModularSegments = (input: unknown): ModularSegment[] => {
  const normalizedInput = normalizeTextInput(input);
  if (!normalizedInput.trim()) return [];
  const tagRegex = /<(Box|Card|Chart)([^>]*)>([\s\S]*?)<\/\1>/gi;
  const segments: ModularSegment[] = [];
  let cursor = 0;
  let match: RegExpExecArray | null;

  while ((match = tagRegex.exec(normalizedInput)) !== null) {
    const start = match.index;
    const end = tagRegex.lastIndex;
    if (start > cursor) {
      const markdown = normalizedInput.slice(cursor, start).trim();
      if (markdown) segments.push({ type: 'markdown', content: markdown });
    }

    const tag = match[1].toLowerCase();
    const attrs = parseTagAttributes(match[2] || '');
    const body = (match[3] || '').trim();

    if (tag === 'box') {
      segments.push({
        type: 'box',
        title: attrs.title || 'Box',
        content: body,
      });
    } else if (tag === 'card') {
      segments.push({
        type: 'card',
        cardType: attrs.type || 'analysis',
        title: attrs.title || 'Card',
        content: body,
      });
    } else if (tag === 'chart') {
      const chartType = (attrs.type || 'line').toLowerCase();
      const normalized = chartType === 'bar' || chartType === 'pie' ? chartType : 'line';
      segments.push({
        type: 'chart',
        chartType: normalized,
        title: attrs.title || 'Chart',
        data: parseChartData(attrs.data, body),
      });
    }

    cursor = end;
  }

  if (cursor < normalizedInput.length) {
    const markdown = normalizedInput.slice(cursor).trim();
    if (markdown) segments.push({ type: 'markdown', content: markdown });
  }

  return segments.length > 0 ? segments : [{ type: 'markdown', content: normalizedInput }];
};

function ChartBox({ chartType, data, title }: { chartType: 'line' | 'bar' | 'pie'; data: Array<Record<string, unknown>>; title: string }) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
        Chart payload unavailable.
      </div>
    );
  }

  const firstDatum = data[0] || {};
  const keys = Object.keys(firstDatum);
  const categoryKey = keys.find((key) => typeof firstDatum[key] === 'string') || keys[0] || 'name';
  const valueKey = keys.find((key) => typeof firstDatum[key] === 'number') || keys[1] || keys[0] || 'value';

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
      <div className="mb-3 text-[12px] font-semibold uppercase tracking-[0.12em] text-slate-500">{title}</div>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 12 }}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis dataKey={categoryKey} tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip />
              <Bar dataKey={valueKey} fill="#06b6d4" radius={[6, 6, 0, 0]} />
            </BarChart>
          ) : chartType === 'pie' ? (
            <PieChart>
              <Tooltip />
              <Pie data={data} dataKey={valueKey} nameKey={categoryKey} outerRadius={90} label>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_SWATCH[index % CHART_SWATCH.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 12 }}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis dataKey={categoryKey} tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip />
              <Line type="monotone" dataKey={valueKey} stroke="#0ea5e9" strokeWidth={3} dot={{ r: 3 }} />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ModularContentRenderer({ content }: { content: unknown }) {
  const segments = useMemo(() => parseModularSegments(content), [content]);

  return (
    <div className="space-y-4">
      {segments.map((segment, index) => {
        if (segment.type === 'markdown') {
          return (
            <div key={`md-${index}`} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
              <div className="prose max-w-none prose-slate prose-p:my-0 text-[15px] leading-[1.6] text-slate-700">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{segment.content}</ReactMarkdown>
              </div>
            </div>
          );
        }
        if (segment.type === 'box') {
          return (
            <div key={`box-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
              <div className="mb-2 text-[12px] font-semibold uppercase tracking-[0.12em] text-slate-500">{segment.title}</div>
              <div className="prose max-w-none prose-slate text-[15px] leading-[1.6] text-slate-700">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{segment.content}</ReactMarkdown>
              </div>
            </div>
          );
        }
        if (segment.type === 'card') {
          return (
            <div key={`card-${index}`} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_10px_28px_rgba(15,23,42,0.06)]">
              <div className="mb-2 text-[12px] font-semibold uppercase tracking-[0.12em] text-cyan-700">{segment.title} · {segment.cardType}</div>
              <div className="prose max-w-none prose-slate text-[15px] leading-[1.6] text-slate-700">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{segment.content}</ReactMarkdown>
              </div>
            </div>
          );
        }
        return <ChartBox key={`chart-${index}`} chartType={segment.chartType} data={segment.data} title={segment.title} />;
      })}
    </div>
  );
}

const formatBytes = (bytes: number): string => {
  if (bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, index);
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
};

const summarizeLocalFile = async (file: File): Promise<UploadedLocalFile> => {
  const raw = await file.text();
  const content = raw.trim();
  const mime = file.type || 'text/plain';
  let summary = 'Text intelligence context uploaded.';
  let excerpt = content.slice(0, MAX_LOCAL_EXCERPT_CHARS);

  if (mime.includes('json') || file.name.toLowerCase().endsWith('.json')) {
    try {
      const parsed = JSON.parse(content);
      if (Array.isArray(parsed)) {
        summary = `JSON array with ${parsed.length} records. Local summary extracted for unified reasoning.`;
      } else if (parsed && typeof parsed === 'object') {
        summary = `JSON object with ${Object.keys(parsed).length} top-level keys. Local summary extracted for unified reasoning.`;
      } else {
        summary = 'JSON scalar value uploaded. Local summary extracted for unified reasoning.';
      }
      excerpt = JSON.stringify(parsed, null, 2).slice(0, MAX_LOCAL_EXCERPT_CHARS);
    } catch {
      summary = 'JSON-like file uploaded; parser fallback used with text summary.';
    }
  } else if (mime.includes('csv') || file.name.toLowerCase().endsWith('.csv')) {
    const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0);
    const header = lines[0] ? lines[0].split(',').map((item) => item.trim()).filter(Boolean) : [];
    const rowCount = Math.max(lines.length - 1, 0);
    summary = `CSV dataset with ${rowCount} rows and ${header.length || 'unknown'} columns. Local summary extracted for unified reasoning.`;
    excerpt = lines.slice(0, 20).join('\n').slice(0, MAX_LOCAL_EXCERPT_CHARS);
  } else {
    const words = content ? content.split(/\s+/).length : 0;
    const lines = content ? content.split(/\r?\n/).length : 0;
    summary = `Text file with ${lines} lines and ${words} words. Local summary extracted for unified reasoning.`;
  }

  return {
    id: crypto.randomUUID(),
    name: file.name,
    mimeType: mime,
    size: file.size,
    uploadedAt: new Date().toISOString(),
    summary,
    excerpt,
  };
};

const normalizeUnifiedCommand = (command: CommandPayload): StoreMapCommand | null => {
  const commandType = String(command.command_type || command.type || '').trim().toLowerCase();
  if (!commandType) return null;

  const payload = typeof command.data === 'object' && command.data !== null
    ? { ...command.data }
    : Object.fromEntries(
        Object.entries(command).filter(([key]) => !['id', 'command_type', 'type', 'priority', 'description', 'source', 'created_at', 'timestamp', 'metadata', 'data'].includes(key))
      );

  return {
    id: String(command.id || `cmd-${crypto.randomUUID().slice(0, 8)}`),
    command_type: commandType,
    priority: String(command.priority || 'medium'),
    data: payload,
    description: String(command.description || `${commandType} command`),
    source: String(command.source || 'unified_response'),
    created_at: String(command.created_at || command.timestamp || new Date().toISOString()),
  };
};

const mergeMapCommands = (existing: StoreMapCommand[], incoming: StoreMapCommand[]): StoreMapCommand[] => {
  if (!incoming.length) return existing;
  const byId = new Map<string, StoreMapCommand>();
  [...existing, ...incoming].forEach((command) => byId.set(command.id, command));
  return Array.from(byId.values());
};

const extractUnifiedCommands = (response: UnifiedIntelligenceResponse): StoreMapCommand[] => {
  const rawCommands: CommandPayload[] = [];
  if (Array.isArray(response.map_commands)) rawCommands.push(...response.map_commands as CommandPayload[]);
  if (Array.isArray(response.map_intelligence?.map_commands)) rawCommands.push(...response.map_intelligence.map_commands as CommandPayload[]);
  if (!rawCommands.length && Array.isArray(response.map_intelligence?.commands)) {
    rawCommands.push(...response.map_intelligence.commands as CommandPayload[]);
  }

  return rawCommands
    .map(normalizeUnifiedCommand)
    .filter((item): item is StoreMapCommand => item !== null);
};

function CapabilityChip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-600 shadow-[0_2px_8px_rgba(15,23,42,0.05)]">
      <span className={`h-1.5 w-1.5 rounded-full ${
        label === 'reasoning' ? 'bg-indigo-400' :
        label === 'tools' ? 'bg-amber-400' :
        label === 'visuals' ? 'bg-emerald-400' : 'bg-blue-400'
      }`}></span>
      {label === 'map' ? 'Map Intelligence' : label.charAt(0).toUpperCase() + label.slice(1)}
    </span>
  );
}

function StatusRail({ response }: { response: UnifiedIntelligenceResponse }) {
  return (
    <div className="flex flex-wrap items-center gap-y-2 gap-x-4 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-[0_6px_18px_rgba(15,23,42,0.04)]">
      {response.capability_statuses.map((status) => (
        <div key={status.capability} className="flex items-center gap-2 text-xs">
          {status.success ? (
            <CheckCircle2 size={14} className="text-emerald-500" />
          ) : (
            <AlertCircle size={14} className="text-amber-500" />
          )}
          <span className="font-medium text-slate-700 capitalize">
            {status.capability === 'map' ? 'Map' : status.capability}
          </span>
          <span className="text-slate-500">({Math.round(status.execution_time_ms || 0)}ms)</span>
        </div>
      ))}
    </div>
  );
}

function ArtifactsPanel({ response }: { response: UnifiedIntelligenceResponse }) {
  const charts = response.visuals?.charts || [];
  const diagrams = response.visuals?.diagrams || [];

  if (!charts.length && !diagrams.length && !response.map_intelligence) {
    return null;
  }

  return (
    <div className="space-y-4 pt-2">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
        <Wand2 size={14} />
        Artifacts & Visuals
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {charts.map((chart) => (
          <GeneratedChartArtifact key={`${chart.title}-${chart.chart_url}`} chart={chart} theme="light" />
        ))}

        {diagrams.map((diagram) => (
          <div key={diagram.image_url} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
            <div className="border-b border-slate-200 px-4 py-2.5 text-xs font-medium text-slate-700">{diagram.diagram_type}</div>
            <div className="bg-slate-50 p-2">
              <img src={diagram.image_url} alt={diagram.description} className="w-full mix-blend-screen" loading="lazy" />
            </div>
            <div className="p-4 text-[13px] leading-relaxed text-slate-600">{diagram.description}</div>
          </div>
        ))}
      </div>

      {response.map_intelligence && (
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
          <div className="flex items-center gap-2 text-xs font-medium text-blue-400">
            <MapIcon size={14} />
            Spatial Layer Analysis
          </div>
          <div className="mt-3 text-[14px] text-slate-700">
            <span className="text-slate-500">Regions: </span>
            {response.map_intelligence.affected_regions.join(', ') || 'No explicit regions'}
          </div>
          <div className="mt-3 flex gap-4 text-xs font-medium text-slate-600">
            <div className="flex h-7 items-center rounded-md bg-slate-100 px-3">
              {response.map_intelligence.markers.length} markers mapped
            </div>
            <div className="flex h-7 items-center rounded-md bg-slate-100 px-3">
              {response.map_intelligence.routes.length} routes tracked
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TypewriterBrief({ content, messageId }: { content: string; messageId: string }) {
  const [visibleChars, setVisibleChars] = useState(() => {
    if (!content) return 0;
    return Math.min(120, content.length);
  });

  useEffect(() => {
    const initial = Math.min(120, content.length);
    if (initial >= content.length) return;

    const interval = window.setInterval(() => {
      setVisibleChars((current) => {
        const next = current + 18;
        if (next >= content.length) {
          window.clearInterval(interval);
          return content.length;
        }
        return next;
      });
    }, 22);

    return () => window.clearInterval(interval);
  }, [content, messageId]);

  const rendered = content.slice(0, visibleChars);
  const complete = visibleChars >= content.length;

  return (
    <div>
      {complete ? (
        <ModularContentRenderer content={content || ' '} />
      ) : (
        <p className="whitespace-pre-wrap text-[15px] leading-[1.6] text-slate-700">{rendered || ' '}</p>
      )}
      {!complete && <span className="inline-block h-4 w-2 animate-pulse rounded-sm bg-cyan-400/80 align-middle" />}
    </div>
  );
}

function AssistantMessage({
  message,
  onFollowUp,
}: {
  message: ThreadMessage;
  onFollowUp: (query: string) => void;
}) {
  const response = message.response;

  if (!response) {
    return (
      <div className="mx-auto flex w-full max-w-[900px] gap-4">
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10 text-red-400">
          <AlertTriangle size={16} />
        </div>
        <div className="flex-1 rounded-2xl border border-red-500/20 bg-red-500/10 px-5 py-3.5 text-[15px] text-red-200">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-[900px] gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-700">
        <Sparkles size={16} />
      </div>

      <div className="flex-1 space-y-6 pt-1">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <h3 className="text-base font-semibold text-slate-900">{response.assistant_response.title}</h3>
          <div className="flex flex-wrap gap-1.5">
            {response.capabilities_activated.map((capability) => (
              <CapabilityChip key={capability} label={capability} />
            ))}
          </div>
        </div>

        <TypewriterBrief content={response.assistant_response.executive_brief} messageId={message.id} />

        <StatusRail response={response} />

        {response.assistant_response.key_takeaways.length > 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
            <h4 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-500">Key Takeaways</h4>
            <ul className="space-y-3">
              {response.assistant_response.key_takeaways.map((item) => (
                <li key={item} className="flex gap-3 text-[14px] text-slate-700">
                  <CircleDot className="mt-1 h-3.5 w-3.5 shrink-0 text-indigo-400" />
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {response.assistant_response.response_blocks.length > 0 && (
          <div className="space-y-4">
            {response.assistant_response.response_blocks.map((block) => (
              <div key={block.title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">{block.title}</div>
                <div className="mt-3">
                  <ModularContentRenderer content={block.content} />
                </div>
              </div>
            ))}
          </div>
        )}

        <ArtifactsPanel response={response} />

        {response.assistant_response.next_actions.length > 0 && (
          <div className="rounded-2xl border border-indigo-200 bg-indigo-50/60 p-5">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
              <RefreshCw size={14} />
              Recommended Next Moves
            </div>
            <div className="mt-4 space-y-2">
              {response.assistant_response.next_actions.map((step) => (
                <div key={step} className="flex items-start gap-2.5 text-[14px] text-slate-700">
                  <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500/70" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <Database size={14} />
              Source Ledger
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {response.data_sources_used.map((source) => (
                <span key={source} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] font-medium text-slate-600">
                  {source}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.05)]">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <MessageSquare size={14} />
              Memory Context
            </div>
            <div className="mt-3 text-[13px] leading-relaxed text-slate-600">{response.assistant_response.memory_summary}</div>
          </div>
        </div>

        {response.assistant_response.suggested_follow_ups.length > 0 && (
          <div className="pt-2">
            <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Suggested Follow-ups</div>
            <div className="flex flex-wrap gap-2">
              {response.assistant_response.suggested_follow_ups.map((followUp) => (
                <button
                  key={followUp}
                  onClick={() => onFollowUp(followUp)}
                  className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-[13px] font-medium text-slate-600 shadow-[0_4px_12px_rgba(15,23,42,0.04)] transition-colors hover:border-cyan-300 hover:text-slate-900"
                >
                  {followUp}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function UnifiedIntelligenceTab() {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const uploadRef = useRef<HTMLInputElement | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [cloudContextEnabled, setCloudContextEnabled] = useState(false);
  const [executionMode, setExecutionMode] = useState<UnifiedExecutionMode>('auto');
  const [manualCapabilities, setManualCapabilities] = useState<UnifiedCapabilityType[]>(['visuals']);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedLocalFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  const unifiedConversationId = useAppStore((state) => state.unifiedConversationId);
  const unifiedMessages = useAppStore((state) => state.unifiedMessages);
  const setUnifiedConversationId = useAppStore((state) => state.setUnifiedConversationId);
  const addUnifiedMessage = useAppStore((state) => state.addUnifiedMessage);
  const replaceUnifiedMessage = useAppStore((state) => state.replaceUnifiedMessage);
  const setMapCommands = useAppStore((state) => state.setMapCommands);
  const setCockpitState = useAppStore((state) => state.setCockpitState);
  const contentWidthClass = 'mx-auto flex w-full max-w-[600px] flex-col gap-6 pb-4';
  const messageWidthClass = 'mx-auto flex w-full max-w-[600px]';

  const localContext = useMemo(() => {
    if (!uploadedFiles.length) return null;
    return {
      source: 'local_uploads',
      transmission_mode: cloudContextEnabled ? 'cloud_context_enabled' : 'summary_only',
      files: uploadedFiles.map((file) => ({
        name: file.name,
        mime_type: file.mimeType,
        size_bytes: file.size,
        uploaded_at: file.uploadedAt,
        summary: file.summary,
        excerpt: cloudContextEnabled ? file.excerpt : undefined,
      })),
    };
  }, [cloudContextEnabled, uploadedFiles]);

  const latestCompletedResponse = useMemo(() => {
    for (let index = unifiedMessages.length - 1; index >= 0; index -= 1) {
      const message = unifiedMessages[index];
      if (message.role === 'assistant' && message.response) return message.response;
    }
    return null;
  }, [unifiedMessages]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }, [unifiedMessages, loading]);

  const history = useMemo<UnifiedConversationMessageInput[]>(
    () =>
      unifiedMessages.map((message) => ({
        role: message.role,
        content: message.content,
        timestamp: message.timestamp,
      })),
    [unifiedMessages]
  );

  const onFilesSelected: React.ChangeEventHandler<HTMLInputElement> = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);
    try {
      const selected = Array.from(files).slice(0, 4);
      const parsedFiles = await Promise.all(selected.map((file) => summarizeLocalFile(file)));
      setUploadedFiles((current) => {
        const merged = [...current];
        for (const next of parsedFiles) {
          const duplicate = merged.find((item) => item.name === next.name && item.size === next.size);
          if (!duplicate) merged.push(next);
        }
        return merged;
      });
    } catch (uploadError) {
      const message = uploadError instanceof Error ? uploadError.message : 'Failed to parse local file.';
      setError(message);
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const removeUploadedFile = (id: string) => {
    setUploadedFiles((files) => files.filter((file) => file.id !== id));
  };

  const exportLatestBrief = async () => {
    if (!latestCompletedResponse || exporting) return;
    setExporting(true);
    setError(null);

    try {
      const [{ jsPDF }, html2canvasModule] = await Promise.all([
        import('jspdf'),
        import('html2canvas'),
      ]);
      const html2canvas = html2canvasModule.default;

      const documentPdf = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });
      const pageWidth = documentPdf.internal.pageSize.getWidth();
      const pageHeight = documentPdf.internal.pageSize.getHeight();
      const margin = 36;
      const bodyWidth = pageWidth - margin * 2;
      let cursorY = margin;

      const ensureSpace = (heightNeeded: number) => {
        if (cursorY + heightNeeded <= pageHeight - margin) return;
        documentPdf.addPage();
        cursorY = margin;
      };

      const addHeading = (text: string) => {
        ensureSpace(28);
        documentPdf.setFont('helvetica', 'bold');
        documentPdf.setFontSize(12);
        documentPdf.text(text, margin, cursorY);
        cursorY += 18;
      };

      const addParagraph = (text: string, fontSize = 10) => {
        const lines = documentPdf.splitTextToSize(text || '-', bodyWidth);
        const height = Math.max(14, lines.length * (fontSize + 3));
        ensureSpace(height + 4);
        documentPdf.setFont('helvetica', 'normal');
        documentPdf.setFontSize(fontSize);
        documentPdf.text(lines, margin, cursorY);
        cursorY += height + 4;
      };

      documentPdf.setFont('helvetica', 'bold');
      documentPdf.setFontSize(16);
      documentPdf.text('GOD\'S EYE OS - Intelligence Brief', margin, cursorY);
      cursorY += 20;

      documentPdf.setFont('helvetica', 'normal');
      documentPdf.setFontSize(9);
      documentPdf.text(`Generated at ${new Date().toISOString()}`, margin, cursorY);
      cursorY += 18;

      addHeading('Executive Brief');
      addParagraph(latestCompletedResponse.assistant_response.executive_brief, 11);

      addHeading('Key Takeaways');
      if (latestCompletedResponse.assistant_response.key_takeaways.length === 0) {
        addParagraph('No key takeaways were returned by the latest response.');
      } else {
        latestCompletedResponse.assistant_response.key_takeaways.slice(0, 8).forEach((item) => addParagraph(`• ${item}`));
      }

      addHeading('Visual Assets');
      const charts = latestCompletedResponse.visuals?.charts || [];
      const diagrams = latestCompletedResponse.visuals?.diagrams || [];
      if (!charts.length && !diagrams.length) {
        addParagraph('No chart or diagram assets were generated.');
      } else {
        charts.slice(0, 6).forEach((chart) => addParagraph(`Chart: ${chart.title}\nURL: ${chart.chart_url}`));
        diagrams.slice(0, 6).forEach((diagram) => addParagraph(`Diagram: ${diagram.diagram_type}\nURL: ${diagram.image_url}`));
      }

      addHeading('Map Intelligence');
      addParagraph(`Affected regions: ${(latestCompletedResponse.map_intelligence?.affected_regions || []).join(', ') || 'None'}`);
      addParagraph(`Markers: ${latestCompletedResponse.map_intelligence?.markers.length || 0} | Routes: ${latestCompletedResponse.map_intelligence?.routes.length || 0}`);

      try {
        const mapElement = document.getElementById('map-canvas-root');
        if (mapElement) {
          const mapCanvas = await html2canvas(mapElement, {
            backgroundColor: '#050505',
            useCORS: true,
            allowTaint: true,
            scale: 1,
            logging: false,
          });
          const snapshotWidth = bodyWidth;
          const snapshotHeight = Math.min(260, (mapCanvas.height * snapshotWidth) / Math.max(mapCanvas.width, 1));
          ensureSpace(snapshotHeight + 26);
          addHeading('Map Snapshot');
          documentPdf.addImage(mapCanvas.toDataURL('image/png'), 'PNG', margin, cursorY, snapshotWidth, snapshotHeight);
          cursorY += snapshotHeight + 8;
        }
      } catch {
        addParagraph('Map snapshot capture failed in this environment; map metrics are included above.');
      }

      addHeading('Source Ledger');
      addParagraph(latestCompletedResponse.data_sources_used.join(', ') || 'No explicit sources listed.');

      const filenameTimestamp = new Date().toISOString().replace(/[:.]/g, '-');
      documentPdf.save(`gods-eye-intelligence-${filenameTimestamp}.pdf`);
    } catch (exportError) {
      const message = exportError instanceof Error ? exportError.message : 'Export failed.';
      setError(message);
    } finally {
      setExporting(false);
    }
  };

  async function submitQuery(nextQuery?: string) {
    const finalQuery = (nextQuery ?? query).trim();
    if (!finalQuery || loading) return;

    setLoading(true);
    setError(null);

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();
    const now = new Date().toISOString();
    const selectedManualCapabilities = executionMode === 'manual' ? manualCapabilities : undefined;
    const maxProcessingTime = executionMode === 'fast' ? 8 : 30;

    startTransition(() => {
      addUnifiedMessage({ id: userMessageId, role: 'user', content: finalQuery, timestamp: now, status: 'done' });
      addUnifiedMessage({
        id: assistantMessageId,
        role: 'assistant',
        content: `Analyzing in ${executionMode.replace('_', ' ')} mode...`,
        timestamp: now,
        status: 'pending',
      });
    });
    setQuery('');

    try {
      let response: UnifiedIntelligenceResponse;

      try {
        response = await new Promise<UnifiedIntelligenceResponse>((resolve, reject) => {
          let settled = false;
          let latestStreamMessage = '';
          let flushTimer: number | null = null;
          let mapFlushTimer: number | null = null;
          let pendingMapCommands: StoreMapCommand[] = [];

          const flushMessage = () => {
            flushTimer = null;
            if (!latestStreamMessage) return;
            startTransition(() => {
              replaceUnifiedMessage(assistantMessageId, { content: latestStreamMessage });
            });
          };

          const flushMapCommands = () => {
            mapFlushTimer = null;
            if (!pendingMapCommands.length) return;
            const state = useAppStore.getState();
            state.setMapCommands(mergeMapCommands(state.mapCommands as StoreMapCommand[], pendingMapCommands));
            pendingMapCommands = [];
          };

          const socket = streamUnifiedIntelligence(
            {
              query: finalQuery,
              conversation_id: unifiedConversationId ?? undefined,
              conversation_history: [...history, { role: 'user', content: finalQuery, timestamp: now }],
              execution_mode: executionMode,
              manual_capabilities: selectedManualCapabilities,
              max_processing_time: maxProcessingTime,
              context: {
                interface: 'unified_assistant',
                mode: 'chat',
                execution_mode: executionMode,
                local_data: localContext,
              },
            },
            {
              onEvent: (event) => {
                const messageText = event.message || (
                  event.type === 'capability' && event.capability
                    ? `${String(event.capability)} ${event.success ? 'completed' : 'failed'}...`
                    : event.phase
                      ? `${String(event.phase).replace(/_/g, ' ')}...`
                      : undefined
                );

                if (messageText && messageText !== latestStreamMessage) {
                  latestStreamMessage = messageText;
                  if (flushTimer === null) {
                    flushTimer = window.setTimeout(flushMessage, 90);
                  }
                }

                if (event.type === 'map_update' && Array.isArray(event.map_commands)) {
                  const incoming = (event.map_commands as CommandPayload[])
                    .map(normalizeUnifiedCommand)
                    .filter((item): item is StoreMapCommand => item !== null);
                  if (incoming.length) {
                    pendingMapCommands = [...pendingMapCommands, ...incoming];
                    if (mapFlushTimer === null) {
                      mapFlushTimer = window.setTimeout(flushMapCommands, 120);
                    }
                  }
                }

                if (event.type === 'cockpit_state' && event.cockpit_state) {
                  setCockpitState(event.cockpit_state);
                }
              },
              onResult: (streamResponse) => {
                if (settled) return;
                settled = true;
                if (flushTimer !== null) {
                  window.clearTimeout(flushTimer);
                  flushTimer = null;
                }
                if (mapFlushTimer !== null) {
                  window.clearTimeout(mapFlushTimer);
                }
                flushMapCommands();
                socket.close(1000, 'complete');
                resolve(streamResponse);
              },
              onError: (streamError) => {
                if (settled) return;
                settled = true;
                if (flushTimer !== null) {
                  window.clearTimeout(flushTimer);
                  flushTimer = null;
                }
                if (mapFlushTimer !== null) {
                  window.clearTimeout(mapFlushTimer);
                }
                flushMapCommands();
                try {
                  socket.close(1011, 'stream-error');
                } catch {
                  // no-op
                }
                reject(new Error(streamError));
              },
              onClose: (closeEvent) => {
                if (settled) return;
                if (closeEvent.code !== 1000) {
                  settled = true;
                  if (flushTimer !== null) {
                    window.clearTimeout(flushTimer);
                  }
                  if (mapFlushTimer !== null) {
                    window.clearTimeout(mapFlushTimer);
                  }
                  reject(new Error(`Unified stream closed (${closeEvent.code}) before completion`));
                }
              },
            },
          );
        });
      } catch {
        response = await postUnifiedIntelligence(finalQuery, {
          conversation_id: unifiedConversationId ?? undefined,
          conversation_history: [...history, { role: 'user', content: finalQuery, timestamp: now }],
          execution_mode: executionMode,
          manual_capabilities: selectedManualCapabilities,
          max_processing_time: maxProcessingTime,
          context: {
            interface: 'unified_assistant',
            mode: 'chat',
            execution_mode: executionMode,
            local_data: localContext,
          },
        });
      }

      const unifiedCommands = extractUnifiedCommands(response);
      if (unifiedCommands.length) {
        const state = useAppStore.getState();
        setMapCommands(mergeMapCommands(state.mapCommands as StoreMapCommand[], unifiedCommands));
      }
      if (response.cockpit_state) {
        setCockpitState(response.cockpit_state);
      }

      startTransition(() => {
        setUnifiedConversationId(response.conversation_id);
        replaceUnifiedMessage(assistantMessageId, {
          content: response.assistant_response.executive_brief,
          response,
          timestamp: response.timestamp,
          status: 'done',
        });
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unified intelligence failed';
      setError(message);
      startTransition(() => {
        replaceUnifiedMessage(assistantMessageId, {
          content: message,
          status: 'error',
        });
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col bg-[#090d10] text-slate-900 selection:bg-cyan-200/70">
      {/* <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800/80 bg-[#09090b]/80 px-6 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-zinc-950 shadow-sm">
            <Sparkles size={16} className="fill-zinc-950" />
          </div>
          <div className="flex flex-col">
            <h2 className="text-[15px] font-semibold text-zinc-100">Unified Intelligence</h2>
            <span className="text-[11px] uppercase tracking-wider text-zinc-500">Autonomous Analyst</span>
          </div>
        </div>

        {unifiedMessages.length > 0 && (
          <button
            onClick={clearUnifiedConversation}
            className="rounded-md px-3 py-1.5 text-[13px] font-medium text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-zinc-100"
          >
            Clear Context
          </button>
        )}
      </header> */}

      <main ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 custom-scrollbar">
        <div className={contentWidthClass}>
          {unifiedMessages.length === 0 && (
            <div className="mt-8 space-y-6">
              <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/30 p-6 sm:p-8">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                  <Brain className="h-4 w-4" />
                  Workspace Ready
                </div>
                <h1 className="mt-4 text-2xl font-semibold tracking-tight text-zinc-100">
                  How can I assist your analysis today?
                </h1>
                <p className="mt-2 text-[15px] leading-relaxed text-zinc-400">
                  I can generate strategic briefs, build comparative tables, execute reasoning workflows, and incorporate maps or visual intelligence into my responses.
                </p>
              </div>

              <div className="grid gap-3">
                {EXAMPLE_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setQuery(prompt)}
                    className="flex w-full items-center justify-between rounded-xl border border-zinc-800 bg-zinc-900/30 px-5 py-4 text-left transition-all hover:border-zinc-700 hover:bg-zinc-800/50 group"
                  >
                    <span className="text-[14px] text-zinc-300 group-hover:text-zinc-100">{prompt}</span>
                    <ChevronRight className="h-4 w-4 text-zinc-600 transition-colors group-hover:text-zinc-400" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {unifiedMessages.map((message) => (
            <div key={message.id} className="w-full">
              {message.role === 'user' ? (
                <div className={`${messageWidthClass} justify-end`}>
                  <div className="max-w-[100%] rounded-2xl bg-zinc-800 px-5 py-3.5 text-[15px] leading-relaxed text-zinc-100 shadow-sm">
                    {message.content}
                  </div>
                </div>
              ) : message.status === 'pending' ? (
                <div className={`${messageWidthClass} gap-4`}>
                  <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-800 bg-zinc-900 text-zinc-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                  <div className="flex flex-1 flex-col gap-2 pt-1">
                    <span className="text-[15px] text-zinc-400">{message.content}</span>
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div className="h-20 animate-pulse rounded-xl border border-zinc-800/80 bg-zinc-900/40" />
                      <div className="h-20 animate-pulse rounded-xl border border-zinc-800/80 bg-zinc-900/40" />
                    </div>
                  </div>
                </div>
              ) : (
                <AssistantMessage message={message} onFollowUp={(followUp) => submitQuery(followUp)} />
              )}
            </div>
          ))}

          {error && (
            <div className={`${messageWidthClass} items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-5 py-4 text-[14px] text-red-200`}>
              <AlertTriangle size={18} />
              {error}
            </div>
          )}
        </div>
      </main>

      <footer className="shrink-0 border-t border-slate-200 bg-teal/50 p-2 backdrop-blur-md">
        <div className="mx-auto w-full max-w-[800px]">
          <div className="mb-2 rounded-xl border border-slate-200 bg-white/80 p-2 shadow-[0_6px_18px_rgba(15,23,42,0.05)]">
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-500">Execution Mode</div>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {MODE_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => {
                    setExecutionMode(preset.id);
                    if (preset.id === 'manual' && preset.manualDefault && manualCapabilities.length === 0) {
                      setManualCapabilities(preset.manualDefault);
                    }
                  }}
                  className={`whitespace-nowrap rounded-full border px-2.5 py-1 text-[10px] font-semibold transition-colors ${
                    executionMode === preset.id
                      ? 'border-cyan-500 bg-cyan-50 text-cyan-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-cyan-300 hover:text-slate-900'
                  }`}
                  title={preset.summary}
                >
                  {preset.label}
                </button>
              ))}
            </div>
            {executionMode === 'manual' && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {CAPABILITY_OPTIONS.map((option) => {
                  const active = manualCapabilities.includes(option.id);
                  return (
                    <button
                      key={option.id}
                      onClick={() => {
                        setManualCapabilities((current) => {
                          if (active) {
                            const next = current.filter((item) => item !== option.id);
                            return next.length > 0 ? next : current;
                          }
                          return [...current, option.id];
                        });
                      }}
                      className={`rounded-md border px-2 py-1 text-[10px] font-medium transition-colors ${
                        active
                          ? 'border-indigo-400 bg-indigo-50 text-indigo-700'
                          : 'border-slate-200 bg-white/80 text-slate-600 hover:border-indigo-300'
                      }`}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mb-2 flex flex-wrap items-center gap-1.5 rounded-xl border border-slate-200 bg-white/80 px-2.5 py-1.5 text-[10px] text-slate-500 shadow-[0_6px_18px_rgba(15,23,42,0.04)]">
            <input
              ref={uploadRef}
              type="file"
              multiple
              accept=".csv,.json,.txt,text/plain,text/csv,application/json"
              className="hidden"
              onChange={onFilesSelected}
            />
            <button
              onClick={() => uploadRef.current?.click()}
              className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-medium text-slate-700 transition-colors hover:border-slate-300"
              disabled={uploading}
            >
              {uploading ? <Loader2 size={12} className="animate-spin" /> : <FileUp size={12} />}
              {uploading ? 'Processing...' : 'Upload local file'}
            </button>

            <button
              onClick={exportLatestBrief}
              disabled={!latestCompletedResponse || exporting}
              className="inline-flex items-center gap-1 rounded-md border border-cyan-400/60 bg-cyan-50 px-2 py-1 text-[10px] font-medium text-cyan-700 transition-colors hover:border-cyan-500 disabled:opacity-50"
            >
              {exporting ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
              {exporting ? 'Exporting...' : 'Export PDF'}
            </button>

            <button
              onClick={() => setCloudContextEnabled((value) => !value)}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[10px] font-medium transition-colors ${
                cloudContextEnabled
                  ? 'border-amber-500/60 bg-amber-50 text-amber-700'
                  : 'border-emerald-500/60 bg-emerald-50 text-emerald-700'
              }`}
            >
              {cloudContextEnabled ? <ShieldAlert size={12} /> : <Lock size={12} />}
              {cloudContextEnabled ? 'Cloud context ON' : 'Sensitive local mode ON'}
            </button>

            <span className="hidden sm:inline text-slate-500">Enter to send • Shift+Enter for new line</span>
          </div>

          {uploadedFiles.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1.5 rounded-xl border border-slate-200 bg-white p-1.5 shadow-[0_6px_18px_rgba(15,23,42,0.04)]">
              {uploadedFiles.map((file) => (
                <div key={file.id} className="inline-flex items-start gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
                  <div className="max-w-[220px]">
                    <div className="truncate font-medium text-slate-800">{file.name}</div>
                    <div className="text-slate-500">{formatBytes(file.size)} • {file.summary}</div>
                  </div>
                  <button
                    onClick={() => removeUploadedFile(file.id)}
                    className="rounded p-0.5 text-slate-500 transition-colors hover:text-slate-700"
                    title="Remove local file context"
                  >
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="relative flex flex-col rounded-xl border border-slate-200 bg-white/80 p-1.5 shadow-[0_8px_24px_rgba(15,23,42,0.06)] transition-all focus-within:border-cyan-300 focus-within:ring-1 focus-within:ring-cyan-200">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  submitQuery();
                }
              }}
              rows={Math.max(1, Math.min(3, query.split('\n').length))}
              placeholder="Ask any analytical question..."
              className="max-h-28 w-full resize-none bg-transparent px-2.5 py-2 text-[14px] leading-[1.5] text-slate-800 outline-none placeholder:text-slate-400"
            />

            <div className="mt-1.5 flex items-center justify-between px-2 pb-0.5">
              <div className="flex gap-3 text-xs font-medium text-slate-500">
                <div className="flex items-center gap-1.5"><kbd className="font-sans text-[10px] uppercase rounded border border-slate-300 bg-slate-100 px-1 py-0.5">Mode</kbd> {executionMode.replace('_', ' ')}</div>
                {uploadedFiles.length > 0 && (
                  <div className="flex items-center gap-1.5 text-cyan-700">
                    <FileUp size={12} />
                    {uploadedFiles.length} local file(s)
                  </div>
                )}
              </div>

              <button
                onClick={() => submitQuery()}
                disabled={!query.trim() || loading}
                className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-cyan-600 px-3 text-[12px] font-semibold text-white transition-colors hover:bg-cyan-500 disabled:pointer-events-none disabled:opacity-50"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                Submit
              </button>
            </div>
          </div>
          <div className="mt-2 text-center text-[10px] text-slate-500">
            Generated insights may require verification. Refer to source ledgers.
          </div>
        </div>
      </footer>
    </div>
  );
}
