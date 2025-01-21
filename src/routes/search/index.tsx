// routes/search/index.tsx
import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/search/")({
  beforeLoad: ({ context }) => {
    const { isOnboardingComplete } = context.loaderData;

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
