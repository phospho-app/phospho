"use client";

import { Icons } from "@/components/small-spinner";
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
import { useToast } from "@/components/ui/use-toast";
import {
  DetectionEngine,
  DetectionScope,
  EventDefinition,
} from "@/models/models";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { sendUserFeedback } from "phospho";
import { useEffect, useState } from "react";

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
    <Card>
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

const dummyEventDefinitions: EventDefinition[] = [
  {
    event_name: "thank you",
    description: "The user said thank you to the assistant",
    detection_scope: DetectionScope.Task,
    detection_engine: DetectionEngine.LLM,
  },
];

export default function AddEvents({
  project_id,
  customEvents,
  phosphoTaskId,
  redirectTo = "/onboarding/plan",
}: {
  project_id: string;
  customEvents: EventDefinition[] | null;
  phosphoTaskId: string | null;
  redirectTo?: string;
}) {
  const router = useRouter();
  const { user, loading, accessToken } = useUser();
  const { toast } = useToast();

  const [isSelected, setIsSelected] = useState<{ [key: string]: boolean }>(
    dummyEventDefinitions?.reduce(
      (acc, eventDefintion) => ({
        ...acc,
        [eventDefintion.event_name]: false,
      }),
      {},
    ),
  );

  const [sendEventsLoading, setSendEventsLoading] = useState(false);

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

  const handleToggle = (eventName: string) => {
    setIsSelected((prevIsSelected) => ({
      ...prevIsSelected,
      [eventName]: !prevIsSelected[eventName],
    }));
  };

  const saveSelectedEvents = async () => {
    const selectedEvents = Object.entries(isSelected)
      ?.filter(([_key, value]) => value)
      ?.map(([key, _value]) => key);
    // Now get the full events from custom events
    // and save the selected events to the project
    const selectedEventDefinitions = customEvents?.filter((eventDefintion) =>
      selectedEvents.includes(eventDefintion.event_name),
    );
    console.log("Selected Event Definitions:", selectedEventDefinitions);

    const response = await fetch(`/api/projects/${project_id}/add-events`, {
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
    if (phosphoTaskId !== null) {
      try {
        sendUserFeedback({
          taskId: phosphoTaskId,
          projectId: "b20659d0932d4edbb2b9682d3e6a0ccb",
          flag:
            (selectedEventDefinitions?.length ?? 0) > 0 ? "success" : "failure",
          source: "user",
          notes: `Selected ${
            selectedEventDefinitions?.length ?? 0
          } events: ${selectedEventDefinitions
            ?.map((event) => event.event_name)
            .join(", ")}`,
        });
      } catch (e) {
        console.error("Error sending feedback to Phospho", e);
      }
    } else {
      console.error("Phospho task id is null");
    }
  };

  return (
    <>
      <Card className="max-w-1/2">
        <CardHeader>
          <CardTitle>Setup events for this project</CardTitle>
          <CardDescription>
            <div>
              According to your use case, here are some relevant events. Phospho
              will look for these events based on their descriptions.
            </div>
            <div className="pt-2">
              You can add more events later in Events/Manage section.
            </div>
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col space-y-2 border-gray-500">
          <div className="flex flex-col overflow-y-auto h-96">
            {customEvents &&
              customEvents?.map &&
              customEvents?.map((eventDefintion) => (
                <EventDisplay
                  eventDefintion={eventDefintion}
                  key={eventDefintion.event_name}
                  onToggle={() => handleToggle(eventDefintion.event_name)}
                  isSelected={isSelected[eventDefintion.event_name]}
                />
              ))}
            {customEvents === null && (
              <div className="flex flex-grow align-middle justify-center">
                <Icons.spinner className="h-4 w-4 animate-spin" />
                <div className="text-gray-500 text-xs">
                  Reticulating splines...
                </div>
              </div>
            )}
          </div>
          <div className="text-gray-500">
            Did you know? You can later setup events to trigger webhooks (slack,
            email, etc.)
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="link" onClick={() => router.push(redirectTo)}>
            Skip
          </Button>
          <Button
            onClick={async () => {
              console.log("Selected Events:", isSelected);
              setSendEventsLoading(true);
              saveSelectedEvents().then((response) => {
                setSendEventsLoading(false);
                router.push(redirectTo);
                toast({
                  title: "Your events have been saved! 🎉",
                  description: `You'll find them in Events/Manage.`,
                });
              });
            }}
            disabled={loading || customEvents === null}
          >
            {sendEventsLoading ? (
              <Icons.spinner className="w-4 h-4 animate-spin" />
            ) : (
              "Save and continue"
            )}
          </Button>
        </CardFooter>
      </Card>
    </>
  );
}
