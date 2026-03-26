import React, { useEffect, useEffectEvent, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import {
  Bot,
  Brain,
  ChevronDown,
  ChevronRight,
  Loader2,
  Newspaper,
  Search,
  Send,
  Shield,
  Target,
  User,
  Zap,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { fetchCountryAnalysis, postNewsInsight, postQuery, postStrategicAnalysis } from '@/services/api';
import { useAppStore } from '@/store';

type AgentMode = 'standard' | 'strategic' | 'news';

interface Message {
  role: 'user' | 'assistant' | 'error';
  mode?: AgentMode;
  content: string;
  data?: StrategicInsightPayload;
  timestamp: string;
}

interface StrategicInsightPayload {
  key_risk_factors?: Array<{ factor: string; severity: string; description: string }>;
  _meta?: {
    grounding_mode?: string;
    tools_used?: string[];
    unavailable_tools?: Record<string, unknown>;
  };
  [key: string]: unknown;
}

const MODE_META: Record<AgentMode, { label: string; icon: LucideIcon; color: string; desc: string }> = {
  standard: {
    label: 'Research',
    icon: Search,
    color: 'text-cyan-300',
    desc: 'Ask for direct country, ontology, and operations answers.',
  },
  strategic: {
    label: 'Analyst',
    icon: Shield,
    color: 'text-amber-300',
    desc: 'Get a grounded strategic assessment using only live/local evidence.',
  },
  news: {
    label: 'News Desk',
    icon: Newspaper,
    color: 'text-emerald-300',
    desc: 'Extract gist and significance from the current feed stack.',
  },
};

export const AIConsoleTab: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<AgentMode>('strategic');
  const bottomRef = useRef<HTMLDivElement>(null);
  const {
    pendingAgentQuery,
    pendingAgentMode,
    clearPendingAgentQuery,
    selectedId,
    selectedType,
  } = useAppStore();

  const { data: selectedCountryAnalysis } = useQuery({
    queryKey: ['country-analysis', selectedId],
    queryFn: () => fetchCountryAnalysis(selectedId as string),
    enabled: selectedType === 'country' && !!selectedId,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const scrollToBottom = () => bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [messages, loading]);

  const sendQuery = async (q: string, overrideMode?: AgentMode) => {
    const text = q.trim();
    if (!text || loading) return;
    const activeMode = overrideMode || mode;

    const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [
      ...prev,
      { role: 'user', mode: activeMode, content: text, timestamp: now },
    ]);
    setInput('');
    setLoading(true);

    try {
      let response: Message;

      if (activeMode === 'strategic') {
        const res = await postStrategicAnalysis(text);
        response = {
          role: 'assistant',
          content: res.data?.executive_summary || 'Strategic analysis complete.',
          data: res.data,
          timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        };
      } else if (activeMode === 'news') {
        const res = await postNewsInsight(text);
        response = {
          role: 'assistant',
          content: res.answer,
          timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        };
      } else {
        const res = await postQuery(text);
        response = {
          role: 'assistant',
          content: res.answer,
          timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        };
      }

      setMessages((prev) => [...prev, response]);
    } catch (err: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          content: `Research request failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
          timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handlePendingQuery = useEffectEvent((query: string, agentMode: typeof pendingAgentMode) => {
    const resolvedMode: AgentMode = agentMode === 'expert' ? 'strategic' : agentMode;
    setMode(resolvedMode);
    setTimeout(() => {
      sendQuery(query, resolvedMode);
      clearPendingAgentQuery();
    }, 50);
  });

  useEffect(() => {
    if (pendingAgentQuery && !loading) {
      handlePendingQuery(pendingAgentQuery, pendingAgentMode);
    }
  }, [loading, pendingAgentMode, pendingAgentQuery]);

  const contextualPrompts = selectedCountryAnalysis
    ? [
      `Give me a grounded brief on ${selectedCountryAnalysis.country.name} for the next 14 days.`,
      `What evidence matters most for ${selectedCountryAnalysis.country.name} right now?`,
      `Turn ${selectedCountryAnalysis.country.name} into an action checklist for me.`,
    ]
    : [];

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl bg-transparent">
      <div className="shrink-0 border-b border-white/5 bg-white/5 p-1.5">
        <div className="flex gap-1">
          {(Object.entries(MODE_META) as [AgentMode, { label: string; icon: LucideIcon; color: string; desc: string }][])
            ?.map(([candidateMode, meta]) => (
              <button
                key={candidateMode}
                onClick={() => setMode(candidateMode)}
                className={clsx(
                  'flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-2 py-1.5 text-[9px] font-bold uppercase tracking-wider transition-all',
                  mode === candidateMode
                    ? 'border-zinc-700 bg-zinc-800 text-zinc-100'
                    : 'border-transparent text-zinc-500 hover:bg-zinc-800/40 hover:text-zinc-300',
                )}
              >
                <meta.icon size={11} className={mode === candidateMode ? meta.color : ''} />
                <span>{meta.label}</span>
              </button>
            ))}
        </div>
        <p className="px-2 pt-2 text-[10px] text-zinc-500">{MODE_META[mode].desc}</p>
      </div>

      {!!selectedCountryAnalysis && (
        <div className="shrink-0 border-b border-zinc-800/70 bg-zinc-950/50 p-3">
          <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-300">
            <Brain size={11} />
            <span>{selectedCountryAnalysis.country.name} Research Context</span>
          </div>
          <div className="grid gap-2">
            {contextualPrompts?.map((prompt) => (
              <button
                key={prompt}
                onClick={() => sendQuery(prompt, 'strategic')}
                className="rounded-xl border border-zinc-800 bg-black/20 px-3 py-2 text-left text-[11px] text-zinc-200 transition-all hover:border-cyan-700/40 hover:bg-cyan-950/10"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="custom-scrollbar flex-1 space-y-4 overflow-y-auto p-3">
        {!messages?.length && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <Zap className="mb-3 text-zinc-700" size={30} />
            <div className="max-w-[240px] text-sm font-semibold text-zinc-200">Research copilot is ready.</div>
            <div className="mt-1 max-w-[260px] text-[11px] leading-relaxed text-zinc-500">
              Ask for a country brief, a strategic assessment, or a direct evidence review. The analyst will stay grounded in available data.
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages?.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={clsx('flex items-start gap-2.5', message.role === 'user' ? 'flex-row-reverse' : 'flex-row')}
            >
              <div
                className={clsx(
                  'mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border',
                  message.role === 'user' ? 'border-zinc-700 bg-zinc-800' : 'border-cyan-900/40 bg-cyan-950/20',
                )}
              >
                {message.role === 'user' ? <User size={14} className="text-zinc-400" /> : <Bot size={14} className="text-cyan-300" />}
              </div>

              <div
                className={clsx(
                  'max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[11px] leading-relaxed shadow-sm',
                  message.role === 'user'
                    ? 'rounded-tr-none bg-cyan-600 text-white'
                    : 'rounded-tl-none border border-zinc-800 bg-zinc-900/80 text-zinc-200',
                )}
              >
                <div className="prose prose-invert prose-xs max-w-none font-sans prose-p:leading-relaxed prose-pre:border prose-pre:border-zinc-800 prose-pre:bg-zinc-950">
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                  )}
                </div>

                {message.data && <StrategicInsightView data={message.data} />}

                <div className={clsx('mt-1.5 text-[8px] opacity-40', message.role === 'user' ? 'text-right' : 'text-left')}>
                  {message.timestamp}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-cyan-900/40 bg-cyan-950/20">
              <Bot size={14} className="text-cyan-300" />
            </div>
            <div className="flex items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/80 px-4 py-2 text-[10px] text-zinc-400">
              <Loader2 size={12} className="animate-spin text-cyan-300" />
              <span>Research synthesis in progress...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} className="h-1" />
      </div>

      <div className="shrink-0 border-t border-zinc-800 bg-[#0d0d12] p-3">
        <div className="relative">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendQuery(input);
              }
            }}
            rows={1}
            placeholder={`Ask the ${MODE_META[mode].label.toLowerCase()}...`}
            className="max-h-[120px] w-full resize-none rounded-xl border border-zinc-800/80 bg-zinc-900/80 py-3 pl-3 pr-10 text-xs text-zinc-100 outline-none transition-all placeholder:text-zinc-600 focus:border-cyan-600/40"
          />
          <button
            onClick={() => sendQuery(input)}
            disabled={loading || !input.trim()}
            className="absolute bottom-2 right-2 flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-600 text-white transition-all hover:bg-cyan-500 disabled:bg-zinc-800 disabled:text-zinc-600"
          >
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};

const StrategicInsightView: React.FC<{ data: StrategicInsightPayload }> = ({ data }) => {
  const [expanded, setExpanded] = useState(false);
  const unavailableTools = data?._meta?.unavailable_tools
    ? Object.keys(data._meta.unavailable_tools)
    : [];

  return (
    <div className="mt-3 space-y-3 border-t border-zinc-800 pt-3">
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl border border-zinc-800 bg-black/20 p-2">
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">Grounding</div>
          <div className="mt-1 text-[10px] font-bold text-cyan-300">
            {data?._meta?.grounding_mode || 'not reported'}
          </div>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-black/20 p-2">
          <div className="text-[9px] uppercase tracking-widest text-zinc-500">Tools Used</div>
          <div className="mt-1 text-[10px] font-bold text-zinc-200">
            {data?._meta?.tools_used?.length ?? 0}
          </div>
        </div>
      </div>

      {!!data.key_risk_factors?.length && (
        <div className="space-y-1.5">
          <span className="flex items-center gap-1.5 text-[9px] font-bold uppercase tracking-widest text-zinc-500">
            <Target size={10} className="text-amber-300" />
            Risk Factors
          </span>
          <div className="space-y-1.5">
            {data.key_risk_factors.slice(0, 3)?.map((factor, index: number) => (
              <div key={`${factor.factor}-${index}`} className="rounded-lg border border-zinc-800 bg-[#0b0b0e] p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-bold text-zinc-200">{factor.factor}</span>
                  <span className="text-[8px] uppercase tracking-widest text-amber-300">{factor.severity}</span>
                </div>
                <p className="mt-1 text-[9.5px] leading-snug text-zinc-400">{factor.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!!unavailableTools?.length && (
        <div className="rounded-xl border border-amber-900/40 bg-amber-950/10 p-2.5">
          <div className="text-[9px] font-bold uppercase tracking-widest text-amber-300">Unavailable Inputs</div>
          <div className="mt-1 text-[10px] leading-relaxed text-zinc-300">
            {unavailableTools.join(', ')}
          </div>
        </div>
      )}

      <button
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-cyan-900/30 bg-cyan-950/10 py-1.5 text-[9px] font-bold uppercase tracking-widest text-cyan-300 transition-all hover:border-cyan-800/50 hover:bg-cyan-950/20"
      >
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span>{expanded ? 'Hide raw data' : 'Show raw data'}</span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-lg border border-zinc-800 bg-[#08080a] p-3">
              <pre className="overflow-x-auto text-[8.5px] leading-relaxed text-cyan-200">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
