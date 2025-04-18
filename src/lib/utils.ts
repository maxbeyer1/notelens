import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format seconds to a friendly time string (e.g., "5 minutes")
 */
export function formatTimeRemaining(seconds: number): string {
  if (seconds < 60) {
    return `${Math.ceil(seconds)} second${seconds !== 1 ? "s" : ""}`;
  }

  const minutes = Math.ceil(seconds / 60);
  return `${minutes} minute${minutes !== 1 ? "s" : ""}`;
}

/**
 * Format a number with commas for thousands
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Extract the payload from a WebSocket message based on its type
 */
export function extractPayload<T>(message: any): T | null {
  if (!message) return null;

  // If the message already has the right structure, just return it
  if (message.payload) {
    return message.payload as T;
  }

  // If the message IS the payload (sometimes happens with WebSocket messages)
  if (
    Object.keys(message).includes("stage") ||
    Object.keys(message).includes("success")
  ) {
    return message as T;
  }

  return null;
}
