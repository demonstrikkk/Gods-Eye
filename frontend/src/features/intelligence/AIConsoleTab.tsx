// ─────────────────────────────────────────────────────────────────────────────
// JanGraph OS — Unified Intelligence Agent Console
// Supports: Standard Query, Strategic Analysis (Multi-tool), News Intelligence
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { postQuery, postStrategicAnalysis, postNewsInsight } from '@/services/api';
import { useAppStore } from '@/store';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, Loader2, Sparkles, AlertTriangle, Bot, User, 
  Search, Shield, Newspaper, Zap, Code, ChevronRight, ChevronDown, Target
} from 'lucide-react';
import clsx from 'clsx';

type AgentMode = 'standard' | 'strategic' | 'news';

interface Message {
  role: 'user' | 'assistant' | 'error';
  mode?: AgentMode;
  content: string;
  data?: any;
  timestamp: string;
}

const MODE_META: Record<AgentMode, { label: string; icon: any; color: string; desc: string }> = {
  standard: { 
    label: 'Ontology QA', 
    icon: Search, 
    color: 'text-blue-400', 
    desc: 'Query countries, booths, workers, schemes, and ontology nodes.' 
  },
  strategic: { 
    label: 'Strategic', 
    icon: Shield, 
    color: 'text-purple-400', 
    desc: 'Multi-tool agent for deep geopolitics.' 
  },
  news: { 
    label: 'News AI', 
    icon: Newspaper, 
    color: 'text-amber-400', 
    desc: 'Extract gists & reasoning from feeds.' 
  },
};

export const AIConsoleTab: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<AgentMode>('standard');
  const bottomRef = useRef<HTMLDivElement>(null);
  const { pendingAgentQuery, pendingAgentMode, clearPendingAgentQuery } = useAppStore();

  const scrollToBottom = () => bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [messages, loading]);

  // Handoff logic: Execute queries dispatched from other panels automatically
  useEffect(() => {
    if (pendingAgentQuery && !loading) {
      setMode(pendingAgentMode);
      // Wait a tick for mode to set, then send
      setTimeout(() => {
        sendQuery(pendingAgentQuery, pendingAgentMode);
        clearPendingAgentQuery();
      }, 50);
    }
  }, [pendingAgentQuery]);

  const sendQuery = async (q: string, overrideMode?: AgentMode) => {
    const text = q.trim();
    if (!text || loading) return;
    const activeMode = overrideMode || mode;

    const userMsg: Message = {
      role: 'user',
      mode: activeMode,
      content: text,
      timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      let response: any;
      if (activeMode === 'strategic') {
        const res = await postStrategicAnalysis(text);
        response = {
          role: 'assistant',
          content: res.data?.executive_summary || "Strategic analysis complete.",
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
      setMessages(prev => [...prev, response]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: `Intelligence failure: ${err.message}`,
        timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d0d12]/40 rounded-xl overflow-hidden">
      {/* Mode Selector */}
      <div className="flex p-1.5 bg-zinc-900/60 border-b border-zinc-800/80 gap-1 shrink-0">
        {(Object.entries(MODE_META) as [AgentMode, any][]).map(([m, meta]) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={clsx(
              "flex-1 flex items-center justify-center space-x-1.5 py-1.5 rounded-lg text-[9px] font-bold uppercase tracking-wider transition-all border",
              mode === m 
                ? "bg-zinc-800 border-zinc-700 text-zinc-100 shadow-sm" 
                : "bg-transparent border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/40"
            )}
          >
            <meta.icon size={11} className={mode === m ? meta.color : ''} />
            <span>{meta.label}</span>
          </button>
        ))}
      </div>

      {/* Mode Description */}
      <div className="px-3 py-1.5 bg-zinc-900/20 border-b border-zinc-800/40 shrink-0">
        <p className="text-[9px] text-zinc-500 italic">{MODE_META[mode].desc}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 p-3 custom-scrollbar">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3 opacity-60">
            <Zap className="text-zinc-700" size={32} />
            <p className="text-[10px] text-zinc-500 max-w-[180px]">
              Ready for mission-critical queries in <span className="text-blue-400 font-bold">{mode.toUpperCase()}</span> mode.
            </p>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={clsx("flex items-start gap-2.5", msg.role === 'user' ? 'flex-row-reverse' : 'flex-row')}
            >
              <div className={clsx(
                "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border mt-0.5",
                msg.role === 'user' ? "bg-zinc-800 border-zinc-700" : "bg-blue-950/40 border-blue-900/50"
              )}>
                {msg.role === 'user' ? <User size={14} className="text-zinc-400" /> : <Bot size={14} className="text-blue-400" />}
              </div>
              
              <div className={clsx(
                "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[11px] leading-relaxed shadow-sm",
                msg.role === 'user' 
                  ? "bg-blue-600 text-white rounded-tr-none" 
                  : "bg-zinc-900/80 border border-zinc-800 text-zinc-200 rounded-tl-none"
              )}>
                <div className="prose prose-invert prose-xs max-w-none prose-p:leading-relaxed prose-pre:bg-zinc-950 prose-pre:border prose-pre:border-zinc-800 font-sans">
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  )}
                </div>
                
                {/* Strategic Data Visualization if present */}
                {msg.data && (
                  <StrategicInsightView data={msg.data} />
                )}

                <div className={clsx("text-[8px] mt-1.5 opacity-40", msg.role === 'user' ? 'text-right' : 'text-left')}>
                  {msg.timestamp}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-950/40 border border-blue-900/50 flex items-center justify-center shrink-0 animate-pulse">
              <Bot size={14} className="text-blue-400" />
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl px-4 py-2 text-[10px] text-zinc-400 flex items-center space-x-2">
              <Loader2 size={12} className="animate-spin text-blue-500" />
              <span>Synthesis in progress...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} className="h-1" />
      </div>

      {/* Input */}
      <div className="p-3 bg-[#0d0d12] border-t border-zinc-800 shrink-0">
        <div className="relative group">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(input); } }}
            placeholder={`Instruct ${mode} agent...`}
            rows={1}
            className="w-full bg-zinc-900/80 border border-zinc-800/80 text-zinc-200 text-xs rounded-xl pl-3 pr-10 py-3 resize-none focus:outline-none focus:border-blue-600/50 transition-all placeholder-zinc-600"
            style={{ maxHeight: '120px' }}
          />
          <button
            onClick={() => sendQuery(input)}
            disabled={loading || !input.trim()}
            className="absolute right-2 bottom-2 w-7 h-7 flex items-center justify-center rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white transition-all shadow-lg"
          >
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};

// Sub-component for deep strategic data mapping
const StrategicInsightView: React.FC<{ data: any }> = ({ data }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-3 pt-3 border-t border-zinc-800 space-y-3">
      {data.key_risk_factors?.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[9px] font-bold text-zinc-500 uppercase flex items-center tracking-widest">
            <Target size={10} className="mr-1 text-red-400" /> Risk Factors
          </span>
          <div className="grid grid-cols-1 gap-1.5">
            {data.key_risk_factors.map((rf: any, idx: number) => (
              <div key={idx} className="bg-[#0b0b0e] p-2 rounded-lg border border-zinc-800 flex flex-col hover:border-zinc-700 transition-colors">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-bold text-zinc-200">{rf.factor}</span>
                  <span className={clsx("text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded", 
                    rf.severity === 'Critical' ? 'bg-red-950/80 text-red-400 border border-red-900/50' : 
                    rf.severity === 'High' ? 'bg-orange-950/80 text-orange-400 border border-orange-900/50' : 
                    'bg-amber-950/80 text-amber-400 border border-amber-900/50'
                  )}>{rf.severity}</span>
                </div>
                <p className="text-[9.5px] text-zinc-400 leading-snug">{rf.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full py-1.5 rounded-lg bg-blue-900/10 border border-blue-900/30 text-[9px] font-bold text-blue-400 hover:bg-blue-900/20 hover:border-blue-800/50 transition-all flex items-center justify-center space-x-1.5 uppercase tracking-widest"
      >
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <span>{expanded ? 'Hide Raw Intelligence Data' : 'View Raw Intelligence Data'}</span>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-[#08080a] border border-zinc-800 rounded-lg p-3 overflow-x-auto relative group">
              <Code size={12} className="absolute top-2 right-2 text-zinc-600" />
              <pre className="text-[8.5px] font-mono leading-relaxed text-blue-300">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
