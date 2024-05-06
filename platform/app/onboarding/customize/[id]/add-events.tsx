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
import { DetectionScope, EventDefinition } from "@/models/models";
import { navigationStateStore } from "@/store/store";
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

const dummyEventDefinitions: EventDefinition[] = [];

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
  let selectedOrgId =
    navigationStateStore((state) => state.selectedOrgId) ?? "";
  const { loading, accessToken } = useUser();
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

  const generateEvents = (eventType: string) => {
    if (eventType === "text") {
      customEvents = [
        {
          project_id: project_id,
          event_name: "Text generation",
          description: "Generate text for a given prompt",
          org_id: selectedOrgId,
          detection_scope: DetectionScope.Session,
        },
        {
          project_id: project_id,
          event_name: "Text completion",
          description: "Complete a given text prompt",
          org_id: selectedOrgId,
          detection_scope: DetectionScope.Session,
        },
      ];
    } else if (eventType === "support") {
      customEvents = [
        {
          project_id: project_id,
          event_name: "Customer support",
          description: "Provide customer support",
          org_id: selectedOrgId,
          detection_scope: DetectionScope.Session,
        },
        {
          project_id: project_id,
          event_name: "Customer feedback",
          description: "Collect customer feedback",
          org_id: selectedOrgId,
          detection_scope: DetectionScope.Session,
        },
      ];
    } else {
      customEvents = [
        {
          project_id: project_id,
          event_name: "LLM app",
          description: "Use the LLM app",
          org_id: selectedOrgId,
          detection_scope: DetectionScope.Session,
        },
        {
          project_id: project_id,
          event_name: "LLM app feedback",
          description: "Provide feedback on the LLM app",
          org_id: selectedOrgId,
          detection_scope: DetectionScope.Session,
        },
      ];
    }
  };

  return (
    <>
      <Card className="max-w-1/2">
        <CardHeader>
          <CardTitle>Setup events for this project</CardTitle>
          <CardDescription>
            <div>
              Phospho helps you monitor your application by tracking events,
              here's what we recommend.
            </div>
            <div className="pt-2">
              You can add more events later in Events/Manage section.
            </div>
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col space-y-2 border-gray-500">
          <div className="flex justify-center items-center">
            <Button className="mr-4" onClick={() => generateEvents("text")}>
              Text generation
            </Button>
            <Button className="mr-4" onClick={() => generateEvents("support")}>
              Customer support
            </Button>
            <Button className="mr-4" onClick={() => generateEvents("LLM")}>
              LLM app
            </Button>
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
