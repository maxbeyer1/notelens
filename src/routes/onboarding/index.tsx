// routes/onboarding/index.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";

import Welcome from "@/components/onboarding/Welcome";
import { store } from "@/lib/store";

export const Route = createFileRoute("/onboarding/")({
  beforeLoad: async () => {
    const isOnboardingComplete = await store.get<boolean>(
      "onboarding_complete"
    );

    if (isOnboardingComplete) {
      throw redirect({ to: "/search" });
    }
  },
  component: Welcome,
});
