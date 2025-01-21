// components/WebSocketTest.tsx
import React, { useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

const WebSocketTest = () => {
  const [lastPong, setLastPong] = useState<string>("No pong received yet");
  const { isConnected, connect, send, subscribe } = useWebSocket({
    onConnected: () => {
      console.log("Connected to WebSocket server");
    },
    onDisconnected: () => {
      console.log("Disconnected from WebSocket server");
    },
    onError: (error) => {
      console.error("WebSocket error:", error);
    },
  });

  // Set up subscription to pong messages
  useEffect(() => {
    // Subscribe to 'pong' messages
    const unsubscribe = subscribe("pong", (payload) => {
      setLastPong(`Received pong at: ${new Date().toISOString()}`);
      console.log("Received pong payload:", payload);
    });

    // Cleanup subscription when component unmounts
    return () => unsubscribe();
  }, [subscribe]);

  // Connect when component mounts
  useEffect(() => {
    connect();
  }, [connect]);

  const handlePing = async () => {
    try {
      // send() automatically adds requestId and timestamp
      const requestId = await send("ping");
      console.log("Sent ping with requestId:", requestId);
    } catch (error) {
      console.error("Failed to send ping:", error);
    }
  };

  return (
    <div className="p-4">
      <div className="mb-4">
        Connection Status: {isConnected ? "Connected" : "Disconnected"}
      </div>
      <button
        onClick={handlePing}
        disabled={!isConnected}
        className="px-4 py-2 bg-gray-900 text-white rounded disabled:opacity-50"
      >
        Send Ping
      </button>
      <div className="mt-4">Last Pong: {lastPong}</div>
    </div>
  );
};

export default WebSocketTest;
