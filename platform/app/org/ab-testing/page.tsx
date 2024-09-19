"use client";

import { ABTesting } from "@/components/abtesting/abtesting";
import { SetupABTestingCallout } from "@/components/callouts/setup-abtesting";

export default function Page() {
  return (
    <>
      <SetupABTestingCallout />
      <ABTesting />
    </>
  );
}
