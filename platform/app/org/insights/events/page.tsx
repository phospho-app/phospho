"use client";

import Events from "@/components/insights/events/manage-events";
import SuccessRateByEvent from "@/components/insights/events/success-rate-by-event";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { navigationStateStore } from "@/store/store";
import { Bell } from "lucide-react";
import Link from "next/link";

export default function Page() {
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );

  if (!selectedProject?.id) {
    return <></>;
  }

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
      <SuccessRateByEvent project_id={selectedProject.id} />
      <Events />
    </>
  );
}
