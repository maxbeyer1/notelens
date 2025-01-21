import WebSocket from "@tauri-apps/plugin-websocket";
import { nanoid } from "nanoid";
import { create } from "zustand";

// Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  requestId: string;
  timestamp: number;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  messageQueue: WebSocketMessage[];
  lastError: Error | null;
}

export class WebSocketClient {
  private static instance: WebSocketClient;
  private ws: Awaited<ReturnType<typeof WebSocket.connect>> | null = null;
  private reconnectTimeout: number = 1000; // Start with 1s timeout
  private maxReconnectTimeout: number = 30000; // Max 30s timeout
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, Set<(payload: any) => void>> = new Map();

  // Zustand store for managing WebSocket state
  public store = create<WebSocketState>()((set) => ({
    isConnected: false,
    isConnecting: false,
    messageQueue: [],
    lastError: null,
  }));

  private constructor() {}

  public static getInstance(): WebSocketClient {
    if (!WebSocketClient.instance) {
      WebSocketClient.instance = new WebSocketClient();
    }
    return WebSocketClient.instance;
  }

  public async connect(url: string = "ws://localhost:8000"): Promise<void> {
    if (this.ws || this.store.getState().isConnecting) return;

    this.store.setState({ isConnecting: true });

    try {
      this.ws = await WebSocket.connect(url);

      // Set up message handler
      this.ws.addListener((msg) => {
        if (msg.type === "Text") {
          const parsedMsg = JSON.parse(msg.data) as WebSocketMessage;
          this.handleMessage(parsedMsg);
        }
      });

      this.store.setState({
        isConnected: true,
        isConnecting: false,
        lastError: null,
      });

      // Reset reconnect timeout on successful connection
      this.reconnectTimeout = 1000;

      // Process any queued messages
      this.processMessageQueue();
    } catch (error) {
      this.store.setState({
        isConnecting: false,
        lastError: error as Error,
      });
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
      // Exponential backoff with max timeout
      this.reconnectTimeout = Math.min(
        this.reconnectTimeout * 2,
        this.maxReconnectTimeout
      );
    }, this.reconnectTimeout);
  }

  public async disconnect(): Promise<void> {
    if (!this.ws) return;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    try {
      await this.ws.disconnect();
    } finally {
      this.ws = null;
      this.store.setState({
        isConnected: false,
        messageQueue: [],
      });
    }
  }

  public async send(type: string, payload: any = {}): Promise<string> {
    const message: WebSocketMessage = {
      type,
      payload,
      requestId: nanoid(),
      timestamp: Date.now(),
    };

    if (!this.ws || !this.store.getState().isConnected) {
      // Queue message if not connected
      this.store.setState((state) => ({
        messageQueue: [...state.messageQueue, message],
      }));
      return message.requestId;
    }

    try {
      await this.ws.send(JSON.stringify(message));
      return message.requestId;
    } catch (error) {
      this.store.setState({ lastError: error as Error });
      throw error;
    }
  }

  private async processMessageQueue(): Promise<void> {
    const { messageQueue } = this.store.getState();
    if (!messageQueue.length) return;

    const messages = [...messageQueue];
    this.store.setState({ messageQueue: [] });

    for (const message of messages) {
      try {
        await this.send(message.type, message.payload);
      } catch (error) {
        console.error("Failed to process queued message:", error);
      }
    }
  }

  public subscribe<T = any>(
    type: string,
    handler: (payload: T) => void
  ): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }

    const handlers = this.messageHandlers.get(type)!;
    handlers.add(handler);

    // Return unsubscribe function
    return () => {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.messageHandlers.delete(type);
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message.payload);
        } catch (error) {
          console.error("Error in message handler:", error);
        }
      });
    }
  }

  public getState() {
    return this.store.getState();
  }

  public subscribeToState(listener: (state: WebSocketState) => void) {
    return this.store.subscribe(listener);
  }
}

// Export types that might be needed by consumers
export type { WebSocketState };
