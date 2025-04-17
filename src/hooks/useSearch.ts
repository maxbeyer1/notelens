import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import type { SearchResult, SearchResultsPayload, SearchRequest } from '@/types/search';

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const { send, subscribe, isConnected } = useWebSocket();

  // Subscribe to search results
  useEffect(() => {
    if (!isConnected) return;
    
    const unsubscribe = subscribe<SearchResultsPayload>('search_results', (payload) => {
      setResults(payload.results);
      setIsSearching(false);
    });

    return () => {
      unsubscribe();
    };
  }, [subscribe, isConnected]);

  const search = useCallback(async (searchParams: SearchRequest) => {
    if (!isConnected) {
      setError(new Error('Not connected to server'));
      return;
    }

    try {
      setIsSearching(true);
      setError(null);
      
      await send('search_request', searchParams);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to send search request'));
      setIsSearching(false);
    }
  }, [send, isConnected]);

  const clearResults = useCallback(() => {
    setResults([]);
  }, []);

  return {
    search,
    results,
    isSearching,
    error,
    clearResults,
    isConnected
  };
}