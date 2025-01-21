export type Stage = {
  id: number;
  title: string;
  description: string;
  status: "waiting" | "in-progress" | "completed";
};

export type EmbeddingProgress = {
  currentNote: string;
  completedNotes: number;
  totalNotes: number;
  estimatedTimeRemaining: number;
};
