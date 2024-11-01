"use client";

import CreateEvent from "@/components/events/create-event";
import EventsList from "@/components/events/event-list";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata, Project, ScoreRangeType } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  AlertCircle,
  PlusIcon,
  Scale,
  Shapes,
  Tag,
  TextSearch,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";

function EventCategoryTitle({
  title,
  icon,
  buttonLabel,
  description,
  max_nb_events,
  current_nb_events,
  defaultEventType: defaultEventCategory,
}: {
  title: string;
  icon: JSX.Element;
  buttonLabel: string;
  description?: string;
  max_nb_events: number;
  current_nb_events: number;
  defaultEventType?: ScoreRangeType;
}) {
  let isDisabled = max_nb_events && current_nb_events >= max_nb_events;
  if (isDisabled === 0) {
    isDisabled = false;
  }

  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <div className="flex justify-between items-end">
        <div>
          <h2 className="flex flex-row text-xl font-bold tracking-tight pt-4 items-center">
            {icon}
            {title}
          </h2>
          <span className="text-muted-foreground text-sm">{description}</span>
        </div>
        <SheetTrigger asChild>
          <Button disabled={isDisabled}>
            <PlusIcon className="size-4 mr-1" />
            {buttonLabel}
          </Button>
        </SheetTrigger>
      </div>
      <SheetContent className="md:w-1/2 overflow-auto">
        <CreateEvent
          setOpen={setOpen}
          defaultEventType={defaultEventCategory}
        />
      </SheetContent>
    </Sheet>
  );
}

export default function Page() {
  const { accessToken } = useUser();

  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const { data: orgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const events = selectedProject?.settings?.events || {};

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;
  const current_nb_events = Object.keys(events).length;

  return (
    <>
      {/* <div className="flex justify-between items-end">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Analytics</h2>
          <span className="text-muted-foreground text-sm">
            Your data is automatically augmented using these event detectors.{" "}
            <Link
              className="underline "
              href="https://docs.phospho.ai/guides/events"
            >
              Learn more
            </Link>
          </span>
        </div> 
      </div>
        
        */}
      <Card className="bg-secondary">
        <CardHeader>
          <div className="flex items-center">
            <TextSearch className="h-16 w-16 mr-4 hover:text-green-500 transition-colors" />
            <div>
              <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center mb-0">
                Event Analytics
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Your data is automatically augmented using the event detectors
                set up below.{" "}
                <Link
                  className="underline "
                  href="https://docs.phospho.ai/guides/events"
                >
                  Learn more
                </Link>
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* <Button
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
          </Button> */}
      {/* <Alert>
        <Bell className="size-4" />
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

      {
        // too many events
        events && max_nb_events && current_nb_events >= max_nb_events && (
          <Alert className="text-red-700">
            <div className="flex space-x-4">
              <AlertCircle className="h-16 w-16" />
              <div>
                <AlertTitle className="font-bold">
                  Max custom analytics quota reached
                </AlertTitle>
                <AlertDescription>
                  <div className="flex-col space-y-4">
                    <div className="pb-2">
                      {max_nb_events}/{max_nb_events} custom analytics created.
                      Add a payment method to create more.
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
      <EventCategoryTitle
        title="Taggers"
        icon={<Tag className="size-6 mr-2" />}
        buttonLabel="Add tagger"
        description="Detect if a topic is present in the text."
        max_nb_events={max_nb_events}
        current_nb_events={current_nb_events}
        defaultEventType={ScoreRangeType.confidence}
      />
      <EventsList event_type={ScoreRangeType.confidence} />

      <EventCategoryTitle
        title="Scorers"
        icon={<Scale className="size-6 mr-2" />}
        buttonLabel="Add scorer"
        description="Score text on a numerical scale."
        max_nb_events={max_nb_events}
        current_nb_events={current_nb_events}
        defaultEventType={ScoreRangeType.range}
      />
      <EventsList event_type={ScoreRangeType.range} />

      <EventCategoryTitle
        title="Classifiers"
        icon={<Shapes className="size-6 mr-2" />}
        buttonLabel="Add classifier"
        description="Classify text into categories."
        max_nb_events={max_nb_events}
        current_nb_events={current_nb_events}
        defaultEventType={ScoreRangeType.category}
      />
      <EventsList event_type={ScoreRangeType.category} />

      <div className="flex justify-center text-muted-foreground">
        {
          // current number of events
          events && max_nb_events && current_nb_events < max_nb_events && (
            <p>
              {current_nb_events}/{max_nb_events} custom analytics created
            </p>
          )
        }
      </div>
      {/* <SuccessRateByEvent /> */}
    </>
  );
}
