// Strategic Panel — shown when activeView === 'strategic'
// Quick-fire analysis launcher; full results go to AI Console
import React, { useState } from 'react';
import { postStrategicAnalysis } from '@/services/api';
import { useAppStore } from '@/store';
import { Brain, Send, Loader2, Target, Zap } from 'lucide-react';

const QUICK_QUERIES = [
  "India's 45-day risk from current conflicts",
  'Impact of oil price surge on rural sentiment',
  'Monsoon failure chain reaction analysis',
];

export const StrategicPanel: React.FC = () => {
  const { setSidebarTab, setPendingAgentQuery } = useAppStore();
  const [query, setQuery] = useState('');

  const run = (q: string) => {
    if (!q.trim()) return;
    setPendingAgentQuery(q, 'strategic');
    setSidebarTab('ai');
  };

  return (
    <div className="p-3 space-y-3">
      <div className="text-[9px] font-bold text-purple-400 uppercase tracking-widest px-1 flex items-center space-x-2">
        <span className="w-1 h-3 rounded-full bg-purple-500 inline-block" />
        <span>Strategic Agent — Quick Launch</span>
      </div>

      {/* Query box */}
      <div className="flex space-x-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && run(query)}
          placeholder="Ask the strategic agent…"
          className="flex-1 bg-zinc-900 border border-zinc-800 text-zinc-200 text-[10px] rounded-lg px-2.5 py-2 focus:outline-none focus:border-purple-600/60 transition-colors placeholder-zinc-600"
        />
        <button
          onClick={() => run(query)}
          disabled={!query.trim()}
          className="w-8 h-8 flex items-center justify-center rounded-lg bg-purple-700 hover:bg-purple-600 disabled:bg-zinc-800 text-white transition-all shrink-0"
        >
          <Send size={13} />
        </button>
      </div>

      {/* Quick queries */}
      <div className="flex flex-col space-y-1">
        {QUICK_QUERIES?.map(q => (
          <button
            key={q}
            onClick={() => { setQuery(q); run(q); }}
            className="text-left text-[9px] text-zinc-500 hover:text-purple-300 px-2 py-1.5 rounded-lg bg-zinc-900/40 border border-zinc-800/30 hover:border-purple-900/50 transition-all"
          >
            <Zap size={8} className="inline mr-1.5 text-purple-600" />{q}
          </button>
        ))}
      </div>

    </div>
  );
};
