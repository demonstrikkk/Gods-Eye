// ─────────────────────────────────────────────────────────────────────────────
// Hook: useLastUpdated
// Shows a human-readable "last updated X sec ago" string, updating every second.
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect } from 'react';

export function useLastUpdated(dataUpdatedAt: number | undefined): string {
  const [label, setLabel] = useState<string>('—');

  useEffect(() => {
    if (!dataUpdatedAt) return;

    const update = () => {
      const diff = Math.floor((Date.now() - dataUpdatedAt) / 1000);
      if (diff < 5) setLabel('just now');
      else if (diff < 60) setLabel(`${diff}s ago`);
      else if (diff < 3600) setLabel(`${Math.floor(diff / 60)}m ago`);
      else setLabel(`${Math.floor(diff / 3600)}h ago`);
    };

    update();
    const id = setInterval(update, 5000);
    return () => clearInterval(id);
  }, [dataUpdatedAt]);

  return label;
}
