import { useEffect, useCallback } from "react";
import { useStore } from "zustand";
import { invoke } from "@tauri-apps/api/core";

import { WebSocketClient } from "@/lib/websocket";

interface UseWebSocketOptions {
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Error) => void;
  autoStartBackend?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const wsClient = WebSocketClient.getInstance();
  const { isConnected, isConnecting, lastError } = useStore(wsClient.store);

  // Start the backend if autoStartBackend is true
  useEffect(() => {
    if (options.autoStartBackend) {
      startBackend().catch(console.error);
    }
  }, [options.autoStartBackend]);

  // Setup connection status listeners
  useEffect(() => {
    const unsubscribe = wsClient.subscribeToState((newState) => {
      if (newState.isConnected && !isConnected) {
        options.onConnected?.();
      } else if (!newState.isConnected && isConnected) {
        options.onDisconnected?.();
      }

      if (newState.lastError && newState.lastError !== lastError) {
        options.onError?.(newState.lastError);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [options, wsClient, isConnected, isConnecting, lastError]);

  // Backend management functions
  const startBackend = useCallback(async () => {
    try {
      const result = await invoke<string>("start_backend");
      console.log("Backend started:", result);
      return result;
    } catch (error) {
      console.error("Failed to start backend:", error);
      throw error;
    }
  }, []);

  const stopBackend = useCallback(async () => {
    try {
      const result = await invoke<string>("stop_backend");
      console.log("Backend stopped:", result);
      return result;
    } catch (error) {
      console.error("Failed to stop backend:", error);
      throw error;
    }
  }, []);

  // Wrap methods in useCallback to maintain reference equality
  const connect = useCallback(
    (url?: string) => wsClient.connect(url),
    [wsClient]
  );
  const disconnect = useCallback(() => wsClient.disconnect(), [wsClient]);
  const send = useCallback(
    (type: string, payload?: any) => wsClient.send(type, payload),
    [wsClient]
  );
  const subscribe = useCallback(
    <T = any>(type: string, handler: (payload: T) => void) =>
      wsClient.subscribe(type, handler),
    [wsClient]
  );

  return {
    isConnected,
    isConnecting,
    lastError,
    connect,
    disconnect,
    send,
    subscribe,
    startBackend,
    stopBackend,
  };
}
