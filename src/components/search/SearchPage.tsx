import React, { useState, useEffect, useRef } from "react";
import { useSearch } from "@/hooks/useSearch";
import { Button } from "@/components/ui/Button";
import { useWebSocket } from "@/hooks/useWebSocket";
import { type SearchResult } from "@/types/search";

import { SearchResultItem } from "./SearchResult";

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState("");
  const [selectedNote, setSelectedNote] = useState<SearchResult | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { connect, isConnected } = useWebSocket();
  const { search, results, isSearching, error, clearResults } = useSearch();

  // Connect to WebSocket when component mounts
  useEffect(() => {
    connect();
  }, [connect]);

  // Focus search input on component mount
  useEffect(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    search({ query: query.trim(), limit: 20 });
  };

  const handleResultClick = (result: SearchResult) => {
    setSelectedNote(result);
  };

  const handleBackToResults = () => {
    setSelectedNote(null);
  };

  if (!isConnected) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-4">
          <svg
            className="w-10 h-10 mx-auto mb-4 text-gray-500 animate-pulse"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Connecting to Server
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Please wait while we establish a connection...
          </p>
        </div>
      </div>
    );
  }

  if (selectedNote) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackToResults}
            className="mr-2"
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back
          </Button>
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100 ml-2 truncate">
            {selectedNote.title || "Untitled Note"}
          </h2>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <div
            className="prose dark:prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: selectedNote.html }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        <form onSubmit={handleSearch} className="flex">
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              ref={searchInputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search your notes..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
            />
            {query && (
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                  clearResults();
                  if (searchInputRef.current) {
                    searchInputRef.current.focus();
                  }
                }}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-500"
              >
                <svg
                  className="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    d="M18 6L6 18M6 6l12 12"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            )}
          </div>
          <Button
            type="submit"
            className="ml-2"
            disabled={!query.trim() || isSearching}
          >
            {isSearching ? (
              <svg
                className="animate-spin w-4 h-4 mr-2"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                />
                <path
                  className="opacity-75"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : null}
            Search
          </Button>
        </form>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {error && (
          <div className="p-4 mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200">
            <p>{error.message}</p>
          </div>
        )}

        {isSearching ? (
          <div className="flex items-center justify-center h-32">
            <svg
              className="animate-spin w-8 h-8 text-gray-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
              />
              <path
                className="opacity-75"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="ml-2 text-gray-500 dark:text-gray-400">
              Searching...
            </span>
          </div>
        ) : results.length > 0 ? (
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Found {results.length} result{results.length !== 1 ? "s" : ""}
            </div>
            {results.map((result) => (
              <SearchResultItem
                key={result.id}
                result={result}
                onClick={handleResultClick}
              />
            ))}
          </div>
        ) : query && !isSearching ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <svg
              className="w-16 h-16 text-gray-300 dark:text-gray-700 mb-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
              No results found
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Try a different search term or check your spelling
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <svg
              className="w-16 h-16 text-gray-300 dark:text-gray-700 mb-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
            >
              <path
                d="M9 7H5a2 2 0 00-2 2v8a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-4m-5-4h5a2 2 0 012 2v4M9 3h-5a2 2 0 00-2 2v4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">
              Search Your Notes
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
              Enter keywords to search through your notes. The search uses AI to
              find semantically relevant results.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
