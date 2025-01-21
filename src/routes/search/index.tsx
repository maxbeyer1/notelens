import { createFileRoute, redirect } from "@tanstack/react-router";

import { store } from "@/lib/store";

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
  component: () => (
    // TODO: search component here
    <div>Search Interface</div>
  ),
});
