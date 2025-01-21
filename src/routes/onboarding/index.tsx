// routes/onboarding/index.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";

import Welcome from "@/components/onboarding/Welcome";

export const Route = createFileRoute("/onboarding/")({
  beforeLoad: ({ context }) => {
    if (context.isOnboardingComplete) {
      throw redirect({ to: "/search" });
    }
  },
  component: Welcome,
});
