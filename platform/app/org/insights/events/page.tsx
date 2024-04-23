"use client";

import CreateEvent from "@/components/insights/events/create-event";
import EventsList from "@/components/insights/events/event-list";
import SuccessRateByEvent from "@/components/insights/events/success-rate-by-event";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { AlertCircle, PlusIcon, Wand2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Page() {
  const router = useRouter();

  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const [open, setOpen] = useState(false);
  const selectedProject = dataStateStore((state) => state.selectedProject);

  const events = selectedProject?.settings?.events || {};

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;
  const current_nb_events = Object.keys(events).length;

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
      {
        // too many events
        events && max_nb_events && current_nb_events >= max_nb_events && (
          <Alert className="text-red-700">
            <div className="flex space-x-4">
              <AlertCircle className="h-16 w-16" />
              <div>
                <AlertTitle className="font-bold">
                  Max event quota reached
                </AlertTitle>
                <AlertDescription>
                  <div className="flex-col space-y-4">
                    <div className="pb-2">
                      {max_nb_events}/{max_nb_events} events created. Add a
                      payment method to add more.
                    </div>
                    <Link href="/org/settings/billing">
                      <Button>Add payment method</Button>
                    </Link>
                  </div>
                </AlertDescription>
              </div>
            </div>
          </Alert>
        )
      }
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold tracking-tight pt-4">
            Tracked events
          </h2>
          <span className="text-gray-500 text-sm">
            Set up events to be automatically detected in logs.{" "}
            <Link
              className="underline "
              href="https://docs.phospho.ai/guides/events"
            >
              Learn more
            </Link>
          </span>
        </div>
        <div className="space-x-2">
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
            <Wand2 className="w-4 h-4 mr-1" /> Event suggestions
          </Button>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button
                disabled={max_nb_events && current_nb_events >= max_nb_events}
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Add Event
              </Button>
            </SheetTrigger>
            <SheetContent className="md:w-1/2">
              <CreateEvent setOpen={setOpen} />
            </SheetContent>
          </Sheet>
        </div>
      </div>

      <EventsList />
      <div className="flex justify-center text-gray-500">
        {
          // current number of events
          events && max_nb_events && current_nb_events < max_nb_events && (
            <p>
              {current_nb_events}/{max_nb_events} events created
            </p>
          )
        }
      </div>
    </>
  );
}
