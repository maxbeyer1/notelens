import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

import type { Stage, EmbeddingProgress } from "@/types/onboarding";
import StageItem from "@/components/onboarding/StageItem";
import ProgressBar from "@/components/ui/ProgressBar";

const ProgressScreen = () => {
  // In production, this would come from WebSocket
  const [stages, setStages] = useState<Stage[]>([
    {
      id: 1,
      title: "Initializing Services",
      description: "Setting up secure connections",
      status: "in-progress",
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
      totalNotes: 150, // Simulated total
      estimatedTimeRemaining: 300, // 5 minutes in seconds
    }
  );

  // Simulate progress for demo
  useEffect(() => {
    const inProgressIndex = stages.findIndex(
      (stage) => stage.status === "in-progress"
    );
    if (inProgressIndex === -1) return;

    // Only auto-complete for first two stages
    if (inProgressIndex < 2) {
      const timer = setTimeout(
        () => {
          setStages((prev) => {
            const newStages = [...prev];
            newStages[inProgressIndex].status = "completed";
            if (inProgressIndex < newStages.length - 1) {
              newStages[inProgressIndex + 1].status = "in-progress";
            }
            return newStages;
          });
        },
        inProgressIndex === 0 ? 1000 : 3000
      );

      return () => clearTimeout(timer);
    }
  }, [stages]);

  // Simulate embedding progress updates
  useEffect(() => {
    if (stages[2].status === "in-progress") {
      const interval = setInterval(() => {
        setEmbeddingProgress((prev) => {
          const newCompleted = prev.completedNotes + 1;

          // Only complete the stage when we've processed all notes
          if (newCompleted === prev.totalNotes) {
            setStages((prevStages) => {
              const newStages = [...prevStages];
              newStages[2].status = "completed";
              return newStages;
            });
          }

          return {
            currentNote: `Meeting notes from ${new Date().toLocaleDateString()}`,
            completedNotes: newCompleted,
            totalNotes: prev.totalNotes,
            estimatedTimeRemaining: Math.max(
              0,
              prev.estimatedTimeRemaining - 2
            ),
          };
        });
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [stages]);

  // Calculate overall progress
  const calculateProgress = () => {
    const completedStages = stages.filter(
      (stage) => stage.status === "completed"
    ).length;
    const progressPerStage = 100 / stages.length;

    // Add progress for completed stages
    let totalProgress = completedStages * progressPerStage;

    // Add partial progress for embedding stage if it's in progress
    if (stages[2].status === "in-progress") {
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
