import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

import type {
  Stage,
  EmbeddingProgress,
  SetupProgressPayload,
  SetupCompletePayload,
} from "@/types/onboarding";
import StageItem from "@/components/onboarding/StageItem";
import ProgressBar from "@/components/ui/ProgressBar";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useOnboarding } from "@/hooks/useOnboarding";

const ProgressScreen = () => {
  const { isConnected, connect, send, subscribe } = useWebSocket();
  const { completeOnboarding } = useOnboarding();

  const [stages, setStages] = useState<Stage[]>([
    {
      id: 1,
      title: "Initializing Services",
      description: "Setting up secure connections",
      status: "waiting",
    },
    {
      id: 2,
      title: "Reading Your Notes",
      description: "Safely accessing your Apple Notes library",
      status: "waiting",
    },
    {
      id: 3,
      title: "Enhancing Search",
      description: "Making your notes brilliantly searchable",
      status: "waiting",
    },
  ]);

  const [embeddingProgress, setEmbeddingProgress] = useState<EmbeddingProgress>(
    {
      currentNote: "",
      completedNotes: 0,
      totalNotes: 0,
      estimatedTimeRemaining: 0,
    }
  );

  // Connect to WebSocket when component mounts
  useEffect(() => {
    connect();
  }, [connect]);

  // Start setup process when connected
  useEffect(() => {
    if (isConnected) {
      // Set first stage to in-progress
      setStages((prev) => {
        const newStages = [...prev];
        newStages[0].status = "in-progress";
        return newStages;
      });

      // Send setup_start message to backend
      send("setup_start");
    }
  }, [isConnected, send]);

  // Listen for setup progress messages
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = subscribe("setup_progress", (message: any) => {
      console.log("Received setup progress:", message);

      // Use our utility function to extract the payload
      let payload: SetupProgressPayload | null = null;

      // Check if message directly contains 'payload' property
      if (message.payload) {
        payload = message.payload;
      }
      // Check if message is structured differently (direct fields)
      else if (message.stage) {
        payload = message;
      }

      // Validate payload
      if (!payload || !payload.stage) {
        console.error("Invalid setup_progress message format:", message);
        return;
      }

      const { stage, status_type, processing, stats } = payload;

      // Map backend stage to frontend stage index
      let stageIndex = 0;
      if (stage === "initializing") stageIndex = 0;
      else if (stage === "parsing") stageIndex = 1;
      else if (stage === "processing") stageIndex = 2;

      // Check if this is the final processing update (all notes processed)
      const isComplete =
        stage === "processing" &&
        processing?.processed_notes === processing?.total_notes &&
        processing?.total_notes > 0;

      // Update stages
      setStages((prev) => {
        const newStages = [...prev];

        // Mark previous stages as completed
        for (let i = 0; i < stageIndex; i++) {
          newStages[i].status = "completed";
        }

        // Mark current stage as in-progress or completed
        if (status_type === "completed" || isComplete) {
          newStages[stageIndex].status = "completed";

          // If there's a next stage, make it in-progress
          if (stageIndex < newStages.length - 1) {
            newStages[stageIndex + 1].status = "in-progress";
          }
        } else {
          newStages[stageIndex].status = "in-progress";
        }

        return newStages;
      });

      // Update embedding progress for processing stage
      if (stage === "processing" && processing && processing.total_notes) {
        console.log("Updating embedding progress with:", processing);

        // Make sure we don't show more completed notes than total notes
        const completedNotes = Math.min(
          processing.processed_notes || 0,
          processing.total_notes
        );

        setEmbeddingProgress({
          currentNote: processing.current_note || "",
          completedNotes,
          totalNotes: processing.total_notes,
          estimatedTimeRemaining: Math.max(
            0,
            (processing.total_notes - completedNotes) * 2 // Rough estimate: 2 seconds per note
          ),
        });

        // If we've processed all notes, this is effectively complete
        if (completedNotes === processing.total_notes) {
          console.log("All notes processed, treating as setup completion");

          // Mark all stages as completed
          setStages((prev) =>
            prev.map((stage) => ({ ...stage, status: "completed" }))
          );

          // Complete onboarding after a short delay to show completion
          setTimeout(async () => {
            await completeOnboarding();
            // Force navigation to ensure redirect happens
            window.location.href = "/search";
          }, 1500);
        }
      }
    });

    return () => unsubscribe();
  }, [isConnected, subscribe]);

  // Listen for setup complete message and results
  useEffect(() => {
    if (!isConnected) return;

    // Set up subscriptions for both message types that could indicate setup completion
    const completeUnsubscribe = subscribe("setup_complete", (message: any) => {
      console.log("Received setup_complete:", message);
      handleSetupComplete(message);
    });

    const resultsUnsubscribe = subscribe("setup_results", (message: any) => {
      console.log("Received setup_results:", message);
      handleSetupComplete(message);
    });

    function handleSetupComplete(message: any) {
      // Try to extract success status using various possible message formats
      let success = false;

      // Case 1: message.payload.success exists
      if (message?.payload?.success === true) {
        success = true;
      }
      // Case 2: message.success exists directly
      else if (message?.success === true) {
        success = true;
      }
      // Case 3: message.payload.results.status exists (from setup.py handler)
      else if (message?.payload?.results?.status === "success") {
        success = true;
      }
      // Case 4: message.status exists directly
      else if (message?.status === "success") {
        success = true;
      }

      console.log("Setup completion status:", success);

      if (success) {
        // Mark all stages as completed
        setStages((prev) =>
          prev.map((stage) => ({ ...stage, status: "completed" }))
        );

        // Complete onboarding after a short delay to show completion
        setTimeout(async () => {
          await completeOnboarding();
          // Force navigation to ensure redirect happens
          window.location.href = "/search";
        }, 1500);
      } else {
        const errorMsg =
          message?.payload?.error ||
          message?.error ||
          message?.payload?.results?.error ||
          "Unknown error";

        if (errorMsg !== "Unknown error") {
          console.error("Setup failed:", errorMsg);
        }
      }
    }

    return () => {
      completeUnsubscribe();
      resultsUnsubscribe();
    };
  }, [isConnected, subscribe, completeOnboarding]);

  // Calculate overall progress
  const calculateProgress = () => {
    const completedStages = stages.filter(
      (stage) => stage.status === "completed"
    ).length;
    const progressPerStage = 100 / stages.length;

    // Add progress for completed stages
    let totalProgress = completedStages * progressPerStage;

    // Add partial progress for embedding stage if it's in progress
    if (
      stages[2].status === "in-progress" &&
      embeddingProgress.totalNotes > 0
    ) {
      const embeddingStageProgress =
        (embeddingProgress.completedNotes / embeddingProgress.totalNotes) *
        progressPerStage;
      totalProgress += embeddingStageProgress;
    }

    return totalProgress;
  };

  const progress = calculateProgress();

  return (
    <motion.div
      className="h-screen w-screen flex flex-col items-center justify-center bg-white p-8"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="max-w-xl w-full space-y-12">
        {/* Progress Header */}
        <motion.div
          className="text-center space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-3xl font-medium text-gray-900">
            Setting up NoteLens
          </h2>
          <p className="text-gray-500">This will take just a moment</p>
        </motion.div>

        {/* Progress Bar */}
        <ProgressBar progress={progress} />

        {/* Stages */}
        <div className="space-y-8">
          {stages.map((stage, index) => (
            <StageItem
              key={stage.id}
              stage={stage}
              isLast={index === stages.length - 1}
              embeddingProgress={stage.id === 3 ? embeddingProgress : undefined}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default ProgressScreen;
