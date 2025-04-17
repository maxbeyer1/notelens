import { createFileRoute, redirect } from "@tanstack/react-router";

import { store } from "@/lib/store";
import { SearchPage } from "@/components/search/SearchPage";

export const Route = createFileRoute("/search/")({
  beforeLoad: async () => {
    const isOnboardingComplete = await store.get<boolean>(
      "onboarding_complete"
    );

    // Prevent non-completed users from accessing search
    if (!isOnboardingComplete) {
      throw redirect({ to: "/onboarding" });
    }
  },
  component: SearchPage,
});
