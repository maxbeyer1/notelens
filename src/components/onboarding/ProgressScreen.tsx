import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

import type { Stage } from "@/types/onboarding";
import StageItem from "@/components/onboarding/StageItem";

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

  // Simulate progress for demo
  useEffect(() => {
    const timer = setTimeout(() => {
      setStages((prev) => {
        const inProgressIndex = prev.findIndex(
          (stage) => stage.status === "in-progress"
        );
        if (inProgressIndex === -1) return prev;

        const newStages = [...prev];
        newStages[inProgressIndex].status = "completed";
        if (inProgressIndex < newStages.length - 1) {
          newStages[inProgressIndex + 1].status = "in-progress";
        }
        return newStages;
      });
    }, 2000);

    return () => clearTimeout(timer);
  }, [stages]);

  // Calculate overall progress
  const progress =
    (stages.filter((stage) => stage.status === "completed").length /
      stages.length) *
    100;

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
        <div className="relative h-1 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className="absolute left-0 top-0 h-full bg-gray-900"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeInOut" }}
          />
        </div>

        {/* Stages */}
        <div className="space-y-8">
          {stages.map((stage, index) => (
            <StageItem
              key={stage.id}
              stage={stage}
              isLast={index === stages.length - 1}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default ProgressScreen;
