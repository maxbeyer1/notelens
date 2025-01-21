import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import type { RouterContext } from "@/types/router";

export const router = createRouter({
  routeTree,
  context: {
    isOnboardingComplete: false,
  } satisfies RouterContext,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
    context: RouterContext;
  }
}
