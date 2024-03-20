"use client";

import Events from "@/components/insights/events/manage-events";
import SuccessRateByEvent from "@/components/insights/events/success-rate-by-event";

export default function Page() {
  return (
    <>
      {/* <Alert>
        <Bell className="h-4 w-4" />
        <AlertTitle>
          Never miss what you're looking for. Track users' behaviours with
          events.
        </AlertTitle>
        <AlertDescription>
          Read our{" "}
          <Link
            href="https://docs.phospho.ai/guides/events"
            className="underline"
          >
            guide to events
          </Link>
        </AlertDescription>
      </Alert> */}
      <SuccessRateByEvent />
      <Events />
    </>
  );
}
