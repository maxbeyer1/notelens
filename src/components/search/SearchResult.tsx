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
  // Create a brief preview of the plaintext (first 100 characters)
  const textPreview =
    result.plaintext.slice(0, 100) +
    (result.plaintext.length > 100 ? "..." : "");

  // Format the date
  const formattedDate = formatDistanceToNow(new Date(result.modify_time), {
    addSuffix: true,
  });

  const handleClick = () => {
    // Open in Apple Notes app using the URI scheme
    // const appleNotesURL = `notes://showNote?identifier=${result.uuid}`;

    // Attempt to open the URL
    // window.open(appleNotesURL, "_blank");

    // Also call the original onClick handler to maintain the component
    onClick(result);
  };

  return (
    <div
      className="p-3 mb-2 bg-white dark:bg-black rounded-xl cursor-pointer shadow-sm hover:shadow-md transition-shadow border border-gray-100 dark:border-gray-900"
      onClick={handleClick}
    >
      <div className="flex justify-between items-start">
        <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-1 flex items-center truncate max-w-[80%]">
          {result.is_pinned && (
            <svg
              className="w-3 h-3 mr-1 text-gray-500 dark:text-gray-400 flex-shrink-0"
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
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-1.5">
        {textPreview}
      </p>

      <div className="text-xs text-gray-500 dark:text-gray-500">
        {formattedDate}
      </div>
    </div>
  );
};
