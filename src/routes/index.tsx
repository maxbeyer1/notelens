import { createFileRoute, redirect } from "@tanstack/react-router";

import { store } from "@/lib/store";

export const Route = createFileRoute("/")({
  beforeLoad: async () => {
    const isOnboardingComplete = await store.get<boolean>(
      "onboarding_complete"
    );

    if (isOnboardingComplete) {
      throw redirect({ to: "/search" });
    } else {
      throw redirect({ to: "/onboarding" });
    }
  },
});
