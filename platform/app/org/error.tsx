"use client";

import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>
        Something went wrong! Please make sure your browser is up to date.
      </h2>
      <code>{error.message}</code>
      <Button
        onClick={() => {
          navigationStateStore.persist.clearStorage();
          reset();
        }}
      >
        Reload
      </Button>
    </div>
  );
}
