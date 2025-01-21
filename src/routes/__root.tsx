import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";
import { AnimatePresence } from "framer-motion";

export const Route = createRootRoute({
  component: () => (
    <>
      <AnimatePresence mode="wait">
        <Outlet />
      </AnimatePresence>
      {process.env.NODE_ENV === "development" && <TanStackRouterDevtools />}
    </>
  ),
});
