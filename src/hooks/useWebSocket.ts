import { useEffect, useCallback } from "react";
import { useStore } from "zustand";

import { WebSocketClient } from "@/lib/websocket";

interface UseWebSocketOptions {
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Error) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const wsClient = WebSocketClient.getInstance();

  const { isConnected, isConnecting, lastError } = useStore(wsClient.store);

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
  }, [
    // options.onConnected,
    // options.onDisconnected,
    // options.onError,
    options,
    wsClient,
    isConnected,
    isConnecting,
    lastError,
  ]);

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
    isConnected: isConnected,
    isConnecting: isConnecting,
    lastError: lastError,
    connect,
    disconnect,
    send,
    subscribe,
  };
}
