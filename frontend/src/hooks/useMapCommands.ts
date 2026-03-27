/**
 * Gods-Eye OS — Map Commands Hook
 * Fetches and manages AI-generated map visualization commands
 */

import { useEffect, useRef } from 'react';
import { useAppStore } from '@/store';

const MAP_COMMANDS_POLL_INTERVAL_VISIBLE = 8000;
const MAP_COMMANDS_POLL_INTERVAL_HIDDEN = 30000;

const createCommandsSignature = (commands: Array<Record<string, any>>): string => {
  if (!commands.length) return '0';
  return commands
    .map((command) => `${String(command.id || '')}:${String(command.created_at || '')}:${String(command.command_type || '')}:${String(command.priority || '')}`)
    .join('|');
};

export function useMapCommands() {
  const mapCommands = useAppStore((state) => state.mapCommands);
  const setMapCommands = useAppStore((state) => state.setMapCommands);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const inFlightRef = useRef(false);
  const lastPayloadHashRef = useRef('0');

  const stopPolling = () => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  };

  const getNextInterval = () => {
    if (typeof document !== 'undefined' && document.hidden) {
      return MAP_COMMANDS_POLL_INTERVAL_HIDDEN;
    }
    return MAP_COMMANDS_POLL_INTERVAL_VISIBLE;
  };

  const fetchMapCommands = async () => {
    if (inFlightRef.current) return;

    inFlightRef.current = true;
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const response = await fetch('/api/v1/map/commands', {
        signal: abortRef.current.signal,
      });
      if (!response.ok) {
        console.warn('Failed to fetch map commands:', response.statusText);
        return;
      }

      const result = await response.json();
      if (result.status === 'success' && Array.isArray(result.data)) {
        const payloadHash = createCommandsSignature(result.data as Array<Record<string, any>>);
        if (payloadHash !== lastPayloadHashRef.current) {
          setMapCommands(result.data);
          lastPayloadHashRef.current = payloadHash;
        }
      }
    } catch (err) {
      const maybeError = err as Error;
      if (maybeError.name !== 'AbortError') {
        console.error('Error fetching map commands:', err);
      }
    } finally {
      inFlightRef.current = false;
    }
  };

  const scheduleNextPoll = () => {
    stopPolling();
    pollTimeoutRef.current = setTimeout(async () => {
      await fetchMapCommands();
      scheduleNextPoll();
    }, getNextInterval());
  };

  const clearCommand = async (commandId: string) => {
    try {
      const response = await fetch(`/api/v1/map/commands/${commandId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchMapCommands();
      }
    } catch (err) {
      console.error('Error clearing map command:', err);
    }
  };

  const clearAllCommands = async () => {
    try {
      const response = await fetch('/api/v1/map/commands', {
        method: 'DELETE',
      });

      if (response.ok) {
        setMapCommands([]);
        lastPayloadHashRef.current = '0';
      }
    } catch (err) {
      console.error('Error clearing all map commands:', err);
    }
  };

  useEffect(() => {
    const onVisibilityChange = () => {
      scheduleNextPoll();
    };

    void fetchMapCommands();
    scheduleNextPoll();
    document.addEventListener('visibilitychange', onVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      stopPolling();
      abortRef.current?.abort();
    };
  }, []);

  return {
    mapCommands,
    fetchMapCommands,
    clearCommand,
    clearAllCommands,
  };
}
