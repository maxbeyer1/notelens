import React from "react";
import { Button } from "@/components/ui/button";

const Welcome = () => {
  const handleGetStarted = () => {
    // To be implemented: Navigate to first setup step
    console.log("Starting setup process...");
  };

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center bg-white">
      {/* Main Content */}
      <div className="flex flex-col items-center space-y-16">
        {/* App Name */}
        <h1 className="text-5xl font-medium text-gray-900">NoteLens</h1>

        {/* Single, Impactful Message */}
        <p className="text-2xl text-gray-500">
          Your notes. Brilliantly searchable.
        </p>

        {/* Action Button */}
        <Button
          onClick={handleGetStarted}
          className="px-8 py-6 text-lg bg-[#0066cc] hover:bg-[#0055aa] text-white rounded-lg 
                     transition-colors duration-200 mt-8"
        >
          Continue
        </Button>
      </div>

      {/* Footer */}
      <p className="absolute bottom-4 text-sm text-gray-400">
        {/* Securely enhances your Apple Notes */}
        v0.1.0
      </p>
    </div>
  );
};

export default Welcome;
