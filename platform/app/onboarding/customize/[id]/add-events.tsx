"use client";

import { Spinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useToast } from "@/components/ui/use-toast";
import { getEventsFromTemplateName } from "@/lib/events-lib";
import { authFetcher } from "@/lib/fetcher";
import { EventDefinition, Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { TestTubeDiagonal } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import useSWR from "swr";

function EventDisplay({
  eventDefintion,
  onToggle,
  isSelected,
}: {
  eventDefintion: EventDefinition;
  onToggle: () => void;
  isSelected: boolean;
}) {
  // This is a single component that displays an event definition
  // It also has a tickbox to enable or disable the event for the project
  return (
    <Card className="text-wrap">
      <CardHeader className="pb-2">
        <div className="flex flex-row items-center space-x-4">
          <Checkbox
            className="h-8 w-8"
            onClick={onToggle}
            checked={isSelected}
          />
          <CardTitle>{eventDefintion.event_name}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <CardDescription>{eventDefintion.description}</CardDescription>
      </CardContent>
    </Card>
  );
}

const dummyEventDefinitions: EventDefinition[] = [];

export default function AddEvents({
  project_id,
  redirectTo = "/onboarding/plan",
}: {
  project_id: string;
  redirectTo?: string;
}) {
  const router = useRouter();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const { loading, accessToken } = useUser();
  const { toast } = useToast();

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const [sendEventsLoading, setSendEventsLoading] = useState(false);
  const [customEvents, setCustomEvents] = useState<EventDefinition[] | null>(
    null,
  );
  const [isSelected, setIsSelected] = useState<{ [key: string]: boolean }>(
    dummyEventDefinitions?.reduce(
      (acc, eventDefintion) => ({
        ...acc,
        [eventDefintion.event_name]: false,
      }),
      {},
    ),
  );

  useEffect(() => {
    if (customEvents) {
      setIsSelected(
        customEvents.reduce(
          (acc, eventDefintion) => ({
            ...acc,
            [eventDefintion.event_name]: true,
          }),
          {},
        ),
      );
    }
  }, [customEvents]);

  useEffect(() => {
    if (selectedOrgId && customEvents === null) {
      setCustomEvents(
        getEventsFromTemplateName(
          "Knowledge assistant",
          selectedOrgId,
          project_id,
        ),
      );
    }
  }, [selectedOrgId, customEvents, project_id]);

  const handleToggle = (eventName: string) => {
    setIsSelected((prevIsSelected) => ({
      ...prevIsSelected,
      [eventName]: !prevIsSelected[eventName],
    }));
  };

  const saveSelectedEvents = async () => {
    const selectedEvents = Object.entries(isSelected)
      ?.filter(([, value]) => value)
      ?.map(([key]) => key);
    // Now get the full events from custom events
    // and save the selected events to the project
    const selectedEventDefinitions = customEvents?.filter((eventDefintion) =>
      selectedEvents.includes(eventDefintion.event_name),
    );

    await fetch(`/api/projects/${project_id}/add-events`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        // provide a list of the selected events in customEvents
        events: selectedEventDefinitions,
      }),
    });
  };

  if (!selectedOrgId) {
    return <></>;
  }

  return (
    <>
      <Card className="w-1/2">
        <CardHeader>
          <CardTitle className="flex items-end">
            <TestTubeDiagonal className="w-8 h-8 mr-2 text-green-500" />
            Here are some pre-defined analytics for your project{" "}
            {selectedProject?.project_name ?? ""}
          </CardTitle>
          <CardDescription>
            phospho runs automated analytics to augment your data with tags,
            scores, and labels.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col space-y-2 border-muted-foreground">
          <div className="flex justify-center align-items">
            <ToggleGroup
              type="single"
              defaultValue="Knowledge assistant"
              variant="outline"
            >
              <ToggleGroupItem
                value="Knowledge assistant"
                onClick={() =>
                  setCustomEvents(
                    getEventsFromTemplateName(
                      "Knowledge assistant",
                      selectedOrgId,
                      project_id,
                    ),
                  )
                }
              >
                Knowledge assistant
              </ToggleGroupItem>
              <ToggleGroupItem
                value="Sales assistant"
                onClick={() =>
                  setCustomEvents(
                    getEventsFromTemplateName(
                      "Sales assistant",
                      selectedOrgId,
                      project_id,
                    ),
                  )
                }
              >
                Sales assistant
              </ToggleGroupItem>
              <ToggleGroupItem
                value="Customer support"
                onClick={() =>
                  setCustomEvents(
                    getEventsFromTemplateName(
                      "Customer support",
                      selectedOrgId,
                      project_id,
                    ),
                  )
                }
              >
                Customer support
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
          <div className="flex flex-col space-y-2 overflow-y-auto h-96">
            {customEvents &&
              customEvents?.map &&
              customEvents?.map((eventDefinition) => (
                <EventDisplay
                  eventDefintion={eventDefinition}
                  key={eventDefinition.event_name}
                  onToggle={() => handleToggle(eventDefinition.event_name)}
                  isSelected={isSelected[eventDefinition.event_name]}
                />
              ))}
          </div>
          <div className="text-muted-foreground text-sm">
            You can change this later in the Analytics section.
          </div>
        </CardContent>
        <CardFooter>
          <Button
            className="w-full"
            onClick={async () => {
              setSendEventsLoading(true);
              saveSelectedEvents().then(() => {
                router.push(redirectTo);
                toast({
                  title: "Your config has been saved! 🎉",
                  description: `Change it later in Analytics`,
                });
              });
            }}
            disabled={loading || sendEventsLoading}
          >
            {sendEventsLoading && <Spinner className="mr-1" />}
            Save and continue
          </Button>
        </CardFooter>
      </Card>
    </>
  );
}
