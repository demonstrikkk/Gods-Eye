// ─────────────────────────────────────────────────────────────────────────────
// App root — unified cockpit at '/', all views live inside it
// DashboardLayout routes maintained as fallback URLs
// ─────────────────────────────────────────────────────────────────────────────

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CommandCenter } from '@/pages/CommandCenter';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 8000),
      staleTime: 15_000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Single cockpit — all views are mode-switched inside CommandCenter */}
          <Route path="/*" element={<CommandCenter />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
