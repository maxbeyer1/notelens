import React from "react";
import { formatDistanceToNow } from "date-fns";

import { type SearchResult } from "@/types/search";

interface SearchResultProps {
  result: SearchResult;
  onClick: (result: SearchResult) => void;
}

export const SearchResultItem: React.FC<SearchResultProps> = ({
  result,
  onClick,
}) => {
  // Create a brief preview of the plaintext (first 160 characters)
  const textPreview =
    result.plaintext.slice(0, 160) +
    (result.plaintext.length > 160 ? "..." : "");

  // Format the date
  const formattedDate = formatDistanceToNow(new Date(result.modify_time), {
    addSuffix: true,
  });

  // Calculate a percentage from similarity score
  const relevancePercent = Math.round(result.similarity_score * 100);

  return (
    <div
      className="p-4 border border-gray-200 dark:border-gray-800 rounded-lg mb-3 bg-white dark:bg-gray-950 hover:bg-gray-50 dark:hover:bg-gray-900 transition cursor-pointer shadow-sm"
      onClick={() => onClick(result)}
    >
      <div className="flex justify-between items-start">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1 flex items-center">
          {result.is_pinned && (
            <svg
              className="w-4 h-4 mr-1 text-gray-500 dark:text-gray-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2L12 22M18 8.5L6 8.5" strokeLinecap="round" />
            </svg>
          )}
          {result.title || "Untitled Note"}
        </h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {relevancePercent}% match
        </span>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-2">
        {textPreview}
      </p>

      <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
        <span>Modified {formattedDate}</span>
      </div>
    </div>
  );
};
