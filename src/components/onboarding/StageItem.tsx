import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check } from "lucide-react";

import type { Stage, EmbeddingProgress } from "@/types/onboarding";

interface StageItemProps {
  stage: Stage;
  isLast: boolean;
  embeddingProgress?: EmbeddingProgress;
}

const StageItem = ({ stage, isLast, embeddingProgress }: StageItemProps) => {
  const variants = {
    waiting: { opacity: 0.5 },
    "in-progress": { opacity: 1 },
    completed: { opacity: 1 },
  };

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  };

  return (
    <motion.div
      className="relative flex items-start space-x-4"
      variants={variants}
      animate={stage.status}
      transition={{ duration: 0.4 }}
    >
      <div className="relative">
        <motion.div
          className={`w-6 h-6 rounded-full flex items-center justify-center
            ${stage.status === "completed" ? "bg-gray-900" : "border-2 border-gray-300"}`}
        >
          <AnimatePresence>
            {stage.status === "completed" && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <Check className="w-4 h-4 text-white" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {!isLast && (
          <div className="absolute left-3 top-6 w-px h-16 bg-gray-200 transform -translate-x-1/2" />
        )}
      </div>

      <div className="flex-1 space-y-2">
        <h3 className="text-lg font-medium text-gray-900">{stage.title}</h3>
        <p className="text-gray-500">{stage.description}</p>

        {stage.status === "in-progress" && !embeddingProgress && (
          <motion.div
            className="h-1 w-24 bg-gray-100 rounded-full overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
          >
            <motion.div
              className="h-full bg-gray-900 rounded-full"
              initial={{ x: "-100%" }}
              animate={{ x: "100%" }}
              transition={{
                repeat: Infinity,
                duration: 1,
                ease: "linear",
              }}
            />
          </motion.div>
        )}

        {/* Embedding Progress Details */}
        {stage.status === "in-progress" && embeddingProgress && (
          <motion.div
            className="space-y-4 mt-4"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.4 }}
          >
            {/* Note Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-500">
                <span>
                  {embeddingProgress.completedNotes} of{" "}
                  {embeddingProgress.totalNotes} notes
                </span>
                <span>
                  {formatTime(embeddingProgress.estimatedTimeRemaining)}{" "}
                  remaining
                </span>
              </div>
              <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gray-900"
                  initial={{ width: 0 }}
                  animate={{
                    width: `${(embeddingProgress.completedNotes / embeddingProgress.totalNotes) * 100}%`,
                  }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            </div>

            {/* Currently Processing Note */}
            <motion.div
              className="text-sm text-gray-500"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              key={embeddingProgress.currentNote} // Trigger animation on note change
            >
              Processing: {embeddingProgress.currentNote}
            </motion.div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default StageItem;
