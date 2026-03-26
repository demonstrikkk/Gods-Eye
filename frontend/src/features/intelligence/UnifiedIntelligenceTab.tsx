import { startTransition, useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Database,
  Loader2,
  Map,
  MessageSquare,
  Wand2,
  RefreshCw,
  Send,
  Sparkles,
  Brain,
  ChevronRight
} from 'lucide-react';
import { postUnifiedIntelligence } from '@/services/api';
import { useAppStore } from '@/store';
import type { UnifiedIntelligenceResponse, UnifiedConversationMessageInput } from '@/types';

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

function CapabilityChip({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 px-2 py-1 text-[11px] font-medium text-zinc-300">
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
    <div className="flex flex-wrap items-center gap-y-2 gap-x-4 border-y border-zinc-800/60 py-3">
      {response.capability_statuses.map((status) => (
        <div key={status.capability} className="flex items-center gap-2 text-xs">
          {status.success ? (
            <CheckCircle2 size={14} className="text-emerald-500" />
          ) : (
            <AlertCircle size={14} className="text-amber-500" />
          )}
          <span className="font-medium text-zinc-300 capitalize">
            {status.capability === 'map' ? 'Map' : status.capability}
          </span>
          <span className="text-zinc-500">({Math.round(status.execution_time_ms || 0)}ms)</span>
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
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
        <Wand2 size={14} />
        Artifacts & Visuals
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {charts.map((chart) => (
          <div key={chart.chart_url} className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-900/30">
            <div className="border-b border-zinc-800/80 px-4 py-2.5 text-xs font-medium text-zinc-200">{chart.title}</div>
            <div className="bg-white/5 p-2">
              <img src={chart.chart_url} alt={chart.title} className="w-full mix-blend-screen" loading="lazy" />
            </div>
            {chart.insight && <div className="p-4 text-[13px] leading-relaxed text-zinc-400">{chart.insight}</div>}
          </div>
        ))}

        {diagrams.map((diagram) => (
          <div key={diagram.image_url} className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-900/30">
            <div className="border-b border-zinc-800/80 px-4 py-2.5 text-xs font-medium text-zinc-200">{diagram.diagram_type}</div>
            <div className="bg-white/5 p-2">
              <img src={diagram.image_url} alt={diagram.description} className="w-full mix-blend-screen" loading="lazy" />
            </div>
            <div className="p-4 text-[13px] leading-relaxed text-zinc-400">{diagram.description}</div>
          </div>
        ))}
      </div>

      {response.map_intelligence && (
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-4">
          <div className="flex items-center gap-2 text-xs font-medium text-blue-400">
            <Map size={14} />
            Spatial Layer Analysis
          </div>
          <div className="mt-3 text-[14px] text-zinc-300">
            <span className="text-zinc-500">Regions: </span>
            {response.map_intelligence.affected_regions.join(', ') || 'No explicit regions'}
          </div>
          <div className="mt-3 flex gap-4 text-xs font-medium text-zinc-400">
            <div className="flex h-7 items-center rounded-md bg-zinc-800/50 px-3">
              {response.map_intelligence.markers.length} markers mapped
            </div>
            <div className="flex h-7 items-center rounded-md bg-zinc-800/50 px-3">
              {response.map_intelligence.routes.length} routes tracked
            </div>
          </div>
        </div>
      )}
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
      <div className="mx-auto flex w-full max-w-3xl gap-4">
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
    <div className="mx-auto flex w-full max-w-3xl gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-800 text-zinc-100">
        <Sparkles size={16} />
      </div>

      <div className="flex-1 space-y-6 pt-1">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <h3 className="text-base font-semibold text-zinc-100">{response.assistant_response.title}</h3>
          <div className="flex flex-wrap gap-1.5">
            {response.capabilities_activated.map((capability) => (
              <CapabilityChip key={capability} label={capability} />
            ))}
          </div>
        </div>

        <div className="prose prose-invert prose-p:my-0 prose-zinc max-w-none text-[15px] leading-relaxed text-zinc-300">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{response.assistant_response.executive_brief}</ReactMarkdown>
        </div>

        <StatusRail response={response} />

        {response.assistant_response.key_takeaways.length > 0 && (
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-5">
            <h4 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500">Key Takeaways</h4>
            <ul className="space-y-3">
              {response.assistant_response.key_takeaways.map((item) => (
                <li key={item} className="flex gap-3 text-[14px] text-zinc-200">
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
              <div key={block.title} className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-5">
                <div className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{block.title}</div>
                <div className="prose prose-invert prose-p:my-3 max-w-none text-[15px] leading-relaxed text-zinc-300">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{block.content}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        )}

        <ArtifactsPanel response={response} />

        {response.assistant_response.next_actions.length > 0 && (
          <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-5">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
              <RefreshCw size={14} />
              Recommended Next Moves
            </div>
            <div className="mt-4 space-y-2">
              {response.assistant_response.next_actions.map((step) => (
                <div key={step} className="flex items-start gap-2.5 text-[14px] text-zinc-300">
                  <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-indigo-500/70" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              <Database size={14} />
              Source Ledger
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {response.data_sources_used.map((source) => (
                <span key={source} className="rounded-md border border-zinc-700 bg-zinc-800 px-2 py-1 text-[11px] font-medium text-zinc-300">
                  {source}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-4">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              <MessageSquare size={14} />
              Memory Context
            </div>
            <div className="mt-3 text-[13px] leading-relaxed text-zinc-400">{response.assistant_response.memory_summary}</div>
          </div>
        </div>

        {response.assistant_response.suggested_follow_ups.length > 0 && (
          <div className="pt-2">
            <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">Suggested Follow-ups</div>
            <div className="flex flex-wrap gap-2">
              {response.assistant_response.suggested_follow_ups.map((followUp) => (
                <button
                  key={followUp}
                  onClick={() => onFollowUp(followUp)}
                  className="rounded-full border border-zinc-700 bg-zinc-800/50 px-3.5 py-1.5 text-[13px] font-medium text-zinc-300 transition-colors hover:bg-zinc-700 hover:text-zinc-100"
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
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    unifiedConversationId,
    unifiedMessages,
    setUnifiedConversationId,
    addUnifiedMessage,
    replaceUnifiedMessage,
    clearUnifiedConversation,
  } = useAppStore();

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

  async function submitQuery(nextQuery?: string) {
    const finalQuery = (nextQuery ?? query).trim();
    if (!finalQuery || loading) return;

    setLoading(true);
    setError(null);

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();
    const now = new Date().toISOString();

    startTransition(() => {
      addUnifiedMessage({ id: userMessageId, role: 'user', content: finalQuery, timestamp: now, status: 'done' });
      addUnifiedMessage({
        id: assistantMessageId,
        role: 'assistant',
        content: "Analyzing request context and orchestrating workflow...",
        timestamp: now,
        status: 'pending',
      });
    });
    setQuery('');

    try {
      const response = await postUnifiedIntelligence(finalQuery, {
        conversation_id: unifiedConversationId ?? undefined,
        conversation_history: [...history, { role: 'user', content: finalQuery, timestamp: now }],
        context: { interface: 'unified_assistant', mode: 'chat' },
      });

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
    <div className="flex h-full min-h-0 flex-col bg-[#09090b] text-zinc-100 selection:bg-indigo-500/30">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800/80 bg-[#09090b]/80 px-6 backdrop-blur-md">
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
      </header>

      <main ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 custom-scrollbar">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-8 pb-4">
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
                <div className="mx-auto flex w-full max-w-3xl justify-end">
                  <div className="max-w-[75%] rounded-2xl bg-zinc-800 px-5 py-3.5 text-[15px] leading-relaxed text-zinc-100 shadow-sm">
                    {message.content}
                  </div>
                </div>
              ) : message.status === 'pending' ? (
                <div className="mx-auto flex w-full max-w-3xl gap-4">
                  <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-zinc-800 bg-zinc-900 text-zinc-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                  <div className="flex flex-1 items-center pt-2">
                    <span className="text-[15px] text-zinc-400">{message.content}</span>
                  </div>
                </div>
              ) : (
                <AssistantMessage message={message} onFollowUp={(followUp) => submitQuery(followUp)} />
              )}
            </div>
          ))}

          {error && (
            <div className="mx-auto flex w-full max-w-3xl items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-5 py-4 text-[14px] text-red-200">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}
        </div>
      </main>

      <footer className="shrink-0 border-t border-zinc-800/80 bg-[#09090b]/80 p-4 backdrop-blur-md">
        <div className="mx-auto w-full max-w-3xl">
          <div className="relative flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/50 p-2 shadow-sm transition-all focus-within:border-zinc-600 focus-within:bg-zinc-900 focus-within:ring-1 focus-within:ring-zinc-600">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  submitQuery();
                }
              }}
              rows={Math.max(1, Math.min(5, query.split('\n').length))}
              placeholder="Ask any analytical question..."
              className="max-h-40 w-full resize-none bg-transparent px-3 py-2.5 text-[15px] leading-relaxed text-zinc-100 outline-none placeholder:text-zinc-500"
            />

            <div className="mt-2 flex items-center justify-between px-2 pb-1">
              <div className="flex gap-3 text-xs font-medium text-zinc-500">
                <div className="flex items-center gap-1.5"><kbd className="font-sans text-[10px] uppercase rounded border border-zinc-700 bg-zinc-800 px-1 py-0.5">Mem</kbd> Configured</div>
              </div>

              <button
                onClick={() => submitQuery()}
                disabled={!query.trim() || loading}
                className="inline-flex h-9 items-center gap-2 rounded-xl bg-zinc-100 px-4 text-[13px] font-semibold text-zinc-950 transition-colors hover:bg-white disabled:pointer-events-none disabled:opacity-50"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                Submit
              </button>
            </div>
          </div>
          <div className="mt-3 text-center text-[11px] text-zinc-500">
            Generated insights may require verification. Refer to source ledgers.
          </div>
        </div>
      </footer>
    </div>
  );
}
