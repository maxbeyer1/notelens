import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";
import { AnimatePresence } from "framer-motion";

// TODO: need to implement this check
const getOnboardingStatus = async () => {
  // Check if vector DB exists/is setup
  // Return true if onboarding is complete
  return false;
};

export const Route = createRootRoute({
  component: () => (
    <>
      <AnimatePresence mode="wait">
        <Outlet />
      </AnimatePresence>
      {process.env.NODE_ENV === "development" && <TanStackRouterDevtools />}
    </>
  ),
  loader: async () => {
    const isOnboardingComplete = await getOnboardingStatus();
    return {
      isOnboardingComplete,
    };
  },
});
