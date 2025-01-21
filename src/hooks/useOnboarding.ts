import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { store } from "@/lib/store";

export function useOnboarding() {
  const [isComplete, setIsComplete] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadStatus = async () => {
      const status = await store.get<boolean>("onboarding_complete");
      setIsComplete(status ?? false);
    };

    loadStatus();
  }, []);

  const completeOnboarding = async () => {
    try {
      await store.set("onboarding_complete", true);
      setIsComplete(true);
      await store.save();
      navigate({ to: "/search" });
    } catch (error) {
      console.error("Failed to complete onboarding:", error);
    }
  };

  return {
    isComplete,
    isLoading: isComplete === null,
    completeOnboarding,
  };
}
