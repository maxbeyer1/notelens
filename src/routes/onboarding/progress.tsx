// routes/onboarding/progress.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";

import ProgressScreen from "@/components/onboarding/ProgressScreen";

export const Route = createFileRoute("/onboarding/progress")({
  beforeLoad: ({ context }) => {
    const { isOnboardingComplete } = context.loaderData;

    if (isOnboardingComplete) {
      throw redirect({ to: "/search" });
    }
  },
  component: ProgressScreen,
});
