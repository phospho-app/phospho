import { authMiddleware } from "@propelauth/nextjs/server/app-router";

export const middleware = authMiddleware;

// The middleware is responsible for keeping the user session up to date.
// It should be called on every request that requires authentication AND /api/auth/.* routes.
export const config = {
  matcher: [
    // REQUIRED: Match all request paths that start with /api/auth/
    "/api/auth/(.*)",
    // OPTIONAL: Don't match any static assets
    "/((?!_next/static|_next/image|favicon.ico).*)",
    // Don't match paths that don't require authentication
    "/((org|onboarding|checkout).*)"
  ],
};
