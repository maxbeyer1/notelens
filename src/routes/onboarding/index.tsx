// routes/onboarding/index.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";

import Welcome from "@/components/onboarding/Welcome";

export const Route = createFileRoute("/onboarding/")({
  beforeLoad: ({ context }) => {
    const { isOnboardingComplete } = context.loaderData;

    if (isOnboardingComplete) {
      throw redirect({ to: "/search" });
    }
  },
  component: () => {
    return <Welcome />;
  },
});
