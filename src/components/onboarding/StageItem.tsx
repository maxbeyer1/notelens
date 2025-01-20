import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check } from "lucide-react";

import type { Stage } from "@/types/onboarding";

interface StageItemProps {
  stage: Stage;
  isLast: boolean;
}

const StageItem = ({ stage, isLast }: StageItemProps) => {
  const variants = {
    waiting: { opacity: 0.5 },
    "in-progress": { opacity: 1 },
    completed: { opacity: 1 },
  };

  return (
    <motion.div
      className="relative flex items-start space-x-4"
      variants={variants}
      animate={stage.status}
      transition={{ duration: 0.4 }}
    >
      {/* Status indicator */}
      <div className="relative">
        <motion.div
          className={`w-6 h-6 rounded-full flex items-center justify-center
            ${
              stage.status === "completed"
                ? "bg-gray-900"
                : "border-2 border-gray-300"
            }`}
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

        {/* Connector line */}
        {!isLast && (
          <div className="absolute left-3 top-6 w-px h-16 bg-gray-200 transform -translate-x-1/2" />
        )}
      </div>

      {/* Stage content */}
      <div className="flex-1 space-y-2">
        <h3 className="text-lg font-medium text-gray-900">{stage.title}</h3>
        <p className="text-gray-500">{stage.description}</p>

        {/* Loading indicator for in-progress stage */}
        {stage.status === "in-progress" && (
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
      </div>
    </motion.div>
  );
};

export default StageItem;
