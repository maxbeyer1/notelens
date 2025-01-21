// routes/onboarding/progress.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";

import ProgressScreen from "@/components/onboarding/ProgressScreen";
import WebSocketTest from "@/components/WebSocketTest";
import { store } from "@/lib/store";

export const Route = createFileRoute("/onboarding/progress")({
  beforeLoad: async () => {
    const isOnboardingComplete = await store.get<boolean>(
      "onboarding_complete"
    );

    if (isOnboardingComplete) {
      throw redirect({ to: "/search" });
    }
  },
  // component: ProgressScreen,
  component: WebSocketTest,
});
