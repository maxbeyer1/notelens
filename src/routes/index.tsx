import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  beforeLoad: ({ context }) => {
    const { isOnboardingComplete } = context.loaderData;

    if (isOnboardingComplete) {
      throw redirect({ to: "/search" });
    } else {
      throw redirect({ to: "/onboarding" });
    }
  },
});
