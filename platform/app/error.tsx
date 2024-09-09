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
    <div className="flex flex-col space-y-2">
      <h2>
        Something went wrong! Please make sure your browser is up to date.
      </h2>
      <div className="max-w-3/4 bg-secondary p-3">
        <div>Details:</div>
        <code className="text-xs">{error.message}</code>
      </div>
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
