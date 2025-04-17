export interface SearchResult {
  id: number;
  title: string;
  plaintext: string;
  similarity_score: number;
  uuid: string;
  html: string;
  creation_time: string;
  modify_time: string;
  is_pinned: boolean;
}

export interface SearchResultsPayload {
  results: SearchResult[];
}

export interface SearchRequest {
  query: string;
  limit?: number;
}