import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  beforeLoad: ({ context }) => {
    if (context.isOnboardingComplete) {
      throw redirect({ to: "/search" });
    } else {
      throw redirect({ to: "/onboarding" });
    }
  },
});
