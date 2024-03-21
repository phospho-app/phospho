"use client";

import CreateEvent from "@/components/insights/events/create-event";
import EventsList from "@/components/insights/events/event-list";
import SuccessRateByEvent from "@/components/insights/events/success-rate-by-event";
import { Button } from "@/components/ui/button";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { Wand2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Page() {
  const router = useRouter();
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);

  if (!selectedProject) {
    return <></>;
  }

  const events = selectedProject.settings?.events || {};

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;

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
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold tracking-tight pt-4">
            Currently tracked events
          </h2>
          <span className="text-gray-500">
            Events are automatically detected in logged tasks.{" "}
            <Link
              className="underline "
              href="https://docs.phospho.ai/guides/events"
            >
              Learn more.
            </Link>
          </span>
        </div>
        <div>
          <Button
            variant="secondary"
            onClick={() => {
              router.push(
                `/onboarding/customize/${project_id}?redirect=events`,
              );
            }}
            disabled={
              max_nb_events && Object.keys(events).length >= max_nb_events
            }
          >
            <Wand2 className="w-4 h-4 mr-1" /> Events suggestions
          </Button>
        </div>
      </div>

      <EventsList />
      <CreateEvent />
    </>
  );
}
