import * as Sentry from "@sentry/browser";

export function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    // this is the Sentry.init call from `sentry.server.config.js|ts`
    Sentry.init({
      dsn: "https://bda6e96e12236ac5c62183100155a483@o4506399435325440.ingest.sentry.io/4506400006078464",

      // Adjust this value in production, or use tracesSampler for greater control
      tracesSampleRate: 0.1,

      // Setting this option to true will print useful information to the console while you're setting up Sentry.
      debug: false,
    });
  }

  // This is the Sentry.init call from `sentry.edge.config.js|ts`
  if (process.env.NEXT_RUNTIME === "edge") {
    Sentry.init({
      dsn: "https://bda6e96e12236ac5c62183100155a483@o4506399435325440.ingest.sentry.io/4506400006078464",

      // Adjust this value in production, or use tracesSampler for greater control
      tracesSampleRate: 0.1,

      // Setting this option to true will print useful information to the console while you're setting up Sentry.
      debug: false,
    });
  }
}
