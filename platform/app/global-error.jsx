"use client";

import * as Sentry from "@sentry/nextjs";
import Error from "next/error";
import { useEffect } from "react";

export default function GlobalError({ error }) {
  useEffect(() => {
    if (process.env.APP_ENV !== "local") {
      Sentry.captureException(error);
    }
  }, [error]);

  return (
    <html>
      <body>
        <div>
        <Error />
        </div>
      </body>
    </html>
  );
}
