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

// Backend message types
export type SetupStage = "initializing" | "parsing" | "processing";

export type SetupStatusType = 
  // Initializing stage
  | "starting"
  | "checking_services"
  | "services_ready"
  // Parsing stage
  | "reading_database"
  | "database_read"
  // Processing stage
  | "preparing_notes"
  | "processing_notes"
  | "cleaning_up"
  // General statuses
  | "completed"
  | "failed";

export type SetupStats = {
  total?: number;
  new: number;
  modified: number;
  unchanged: number;
  deleted: number;
  in_trash: number;
  errors: number;
};

export type ProcessingData = {
  total_notes?: number;
  processed_notes?: number;
  current_note?: string;
};

export type SetupProgressPayload = {
  stage: SetupStage;
  status_type: SetupStatusType;
  processing?: ProcessingData;
  stats?: SetupStats;
};

export type SetupCompletePayload = {
  success: boolean;
  stats?: SetupStats;
  error?: string;
};
