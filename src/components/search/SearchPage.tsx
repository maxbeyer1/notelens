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
              strokeWidth={1.5}
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
    // Format the date in a more readable format
    const modifyDate = new Date(selectedNote.modify_time);
    const formattedDate = modifyDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
    const formattedTime = modifyDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });

    return (
      <div className="h-full flex flex-col bg-white dark:bg-black">
        <div className="py-3 px-4 border-b border-gray-100 dark:border-gray-900 flex items-center sticky top-0 bg-white/95 dark:bg-black/95 backdrop-blur-sm z-10 shadow-sm">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackToResults}
            className="mr-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
            <span>Back</span>
          </Button>
          <h2 className="text-base font-medium text-gray-900 dark:text-gray-100 ml-2 truncate">
            {selectedNote.title || "Untitled Note"}
          </h2>
          {selectedNote.is_pinned && (
            <svg
              className="w-3.5 h-3.5 ml-2 text-gray-500 dark:text-gray-400 flex-shrink-0"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2L12 22M18 8.5L6 8.5" strokeLinecap="round" />
            </svg>
          )}
        </div>
        
        <div className="flex-1 overflow-auto">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6">
            {/* Note metadata */}
            <div className="mb-6 text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-4">
              <span>Modified {formattedDate} at {formattedTime}</span>
            </div>
            
            {/* Note content */}
            <div 
              className="prose dark:prose-invert prose-gray max-w-none 
                prose-headings:font-medium prose-headings:text-gray-900 dark:prose-headings:text-gray-100
                prose-p:text-gray-700 dark:prose-p:text-gray-300
                prose-a:text-blue-600 dark:prose-a:text-blue-400
                prose-strong:text-gray-900 dark:prose-strong:text-gray-50
                prose-code:text-gray-900 dark:prose-code:text-gray-100 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:py-0.5 prose-code:rounded
                prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800
                prose-ol:text-gray-700 dark:prose-ol:text-gray-300
                prose-ul:text-gray-700 dark:prose-ul:text-gray-300"
              dangerouslySetInnerHTML={{ __html: selectedNote.html }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-black">
      <div className="py-4 px-6">
        <form onSubmit={handleSearch} className="flex">
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
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
              className="w-full pl-9 pr-3 py-2 rounded-xl border-0 bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-200 dark:ring-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-gray-700"
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
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
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
            variant="ghost"
            type="submit"
            className="ml-1 text-gray-600 dark:text-gray-300"
            disabled={!query.trim() || isSearching}
          >
            {isSearching ? (
              <svg
                className="animate-spin w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
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
            ) : (
              "Search"
            )}
          </Button>
        </form>
      </div>

      <div className="flex-1 overflow-auto px-6 pb-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900 rounded-xl text-red-800 dark:text-red-300 text-sm">
            <p>{error.message}</p>
          </div>
        )}

        {isSearching ? (
          <div className="flex flex-col items-center justify-center h-40">
            <svg
              className="w-6 h-6 text-gray-400 dark:text-gray-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
              />
              <path
                className="opacity-75 animate-spin origin-center"
                d="M12 6v0m0 6v0m0 6v0"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              Searching...
            </span>
          </div>
        ) : results.length > 0 ? (
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-500 mb-3 font-medium">
              {results.length} result{results.length !== 1 ? "s" : ""}
            </div>
            <div className="space-y-2">
              {results.map((result) => (
                <SearchResultItem
                  key={result.id}
                  result={result}
                  onClick={handleResultClick}
                />
              ))}
            </div>
          </div>
        ) : query && !isSearching ? (
          <div className="flex flex-col items-center justify-center h-60 text-center">
            <svg
              className="w-14 h-14 text-gray-300 dark:text-gray-700 mb-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-1">
              No results found
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-500 max-w-xs">
              Try a different search term
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-60 text-center">
            <svg
              className="w-14 h-14 text-gray-300 dark:text-gray-700 mb-4"
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
            <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-1">
              Search Your Notes
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-500 max-w-xs">
              Enter keywords to search through your notes
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
