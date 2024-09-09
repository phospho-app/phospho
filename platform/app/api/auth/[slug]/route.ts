import { getRouteHandlers } from "@propelauth/nextjs/server/app-router";

// postLoginRedirectPathFn is optional, but if you want to redirect the user to a different page after login, you can do so here.
const routeHandlers = getRouteHandlers({
  postLoginRedirectPathFn: () => {
    return "/";
  },
});
export const GET = routeHandlers.getRouteHandler;
export const POST = routeHandlers.postRouteHandler;
