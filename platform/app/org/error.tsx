"use client";

import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
import { RotateCw } from "lucide-react";

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
      <div className="max-w-3/4 bg-secondary p-3 flex flex-col space-y-2">
        <div>Details:</div>
        <code className="text-xs">{navigator.userAgent}</code>
        <code className="text-xs">{error.message}</code>
      </div>
      <Button
        className="max-w-1/4"
        onClick={() => {
          navigationStateStore.persist.clearStorage();
          window.location.reload();
          reset();
        }}
      >
        <RotateCw className="mr-2 size-4" />
        Reload
      </Button>
    </div>
  );
}
