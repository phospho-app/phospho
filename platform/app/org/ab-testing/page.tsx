"use client";

import { ABTesting } from "@/components/abtesting/abtesting";
import { SetupABTestingCallout } from "@/components/callouts/setup-abtesting";

export default function Page() {
  return (
    <div className="flex flex-col gap-y-2">
      <SetupABTestingCallout />
      <ABTesting />
    </div>
  );
}
