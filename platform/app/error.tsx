"use client";

import { Button } from "@/components/ui/button";

export default function Error({ reset }: { reset: () => void }) {
  return (
    <div>
      <h2>
        Something went wrong! Please make sure your browser is up to date.
      </h2>
      <Button onClick={() => reset()}>Reload</Button>
    </div>
  );
}
