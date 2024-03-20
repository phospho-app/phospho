"use client";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components//ui/table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Wand2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useSWRConfig } from "swr";

function CreateEventButton({
  current_nb_events,
  max_nb_events,
  onClick,
}: {
  current_nb_events: number;
  max_nb_events: number | null;
  onClick: (e: any) => void;
}) {
  if (max_nb_events === null) {
    return <Button onClick={onClick}>Create event</Button>;
  }
  if (current_nb_events >= max_nb_events) {
    return (
      <>
        <Button disabled>Create event</Button>
        <p className="text-red-700">
          {max_nb_events}/{max_nb_events} events created.{" "}
          <Link href="/org/settings/billing" className="underline">
            Upgrade plan to create more.
          </Link>
        </p>
      </>
    );
  }
  return (
    <>
      <Button onClick={onClick}>Create event</Button>
      <p>
        {current_nb_events}/{max_nb_events} events created
      </p>
    </>
  );
}

interface EventDetail {
  description: string;
  webhook?: string;
}

const EventsList = ({
  events,
  handleDeleteEvent,
  refresh,
}: {
  events: any | null;
  handleDeleteEvent: (eventNameToDelete: string) => void;
  refresh: boolean;
}) => {
  return (
    <>
      <h2 className="text-2xl font-bold tracking-tight pt-4">
        Currently tracked events
      </h2>
      <Card className="mt-4">
        <CardContent>
          {events === null && <div>No events</div>}
          {events && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Name</TableHead>
                  <TableHead className="text-left">Description</TableHead>
                  <TableHead className="text-left">Webhook</TableHead>
                  <TableHead className="text-right"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(events).map(
                  ([eventName, eventDetails], index) => {
                    const details = eventDetails as EventDetail;

                    return (
                      <TableRow key={index}>
                        <TableCell>{eventName}</TableCell>
                        <TableCell className="text-left">
                          {details.description}
                        </TableCell>
                        <TableCell className="text-left">
                          {details?.webhook && details.webhook.length > 1 ? (
                            <Badge>active</Badge>
                          ) : (
                            <Badge variant="secondary">None</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="link"
                            onClick={() => handleDeleteEvent(eventName)}
                          >
                            Delete
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  },
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
};

// TODO : Refacto this form to use zod (use the create event form as an example)

export default function Events() {
  const { accessToken, loading } = useUser();
  const { mutate } = useSWRConfig();
  const router = useRouter();

  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const setUniqueEventNames = dataStateStore(
    (state) => state.setUniqueEventNames,
  );
  const [events, setEvents] = useState<any>(null);
  const [refresh, setRefresh] = useState(false);

  const project_settings = selectedProject?.settings ?? {};
  const init_events = project_settings.events ?? null;

  const [newEventName, setNewEventName] = useState("");
  const [newEventDescription, setNewEventDescription] = useState("");
  const [newEventWebhook, setNewEventWebhook] = useState("");
  const [newEventWebhookHeader, setNewEventWebhookHeader] =
    useState<string>("");

  // Max number of events
  const plan = selectedOrgMetadata?.plan;
  const max_nb_events = plan === "hobby" ? 10 : plan === "pro" ? 100 : null;

  useEffect(() => {
    setEvents(init_events);
    setRefresh(!refresh);
  }, [init_events, loading]);

  if (!selectedProject) {
    return <div>No selected project</div>;
  }

  function handleEventNameChange(e: React.ChangeEvent<HTMLInputElement>) {
    setNewEventName(e.target.value);
  }

  function handleEventDescriptionChange(
    e: React.ChangeEvent<HTMLTextAreaElement>,
  ) {
    setNewEventDescription(e.target.value);
  }

  function handleWebhookChange(e: React.ChangeEvent<HTMLInputElement>) {
    setNewEventWebhook(e.target.value);
  }

  function handleWebhookHeaderChange(e: React.ChangeEvent<HTMLInputElement>) {
    setNewEventWebhookHeader(e.target.value);
  }

  async function onSubmit() {
    if (!selectedProject) return;

    // Add the new event to the existing events
    const updatedEvents = {
      [newEventName]: {
        description: newEventDescription,
        webhook: newEventWebhook,
        webhook_headers:
          newEventWebhookHeader !== null
            ? { Authorization: newEventWebhookHeader }
            : null,
      }, // Use the new event's name as a key
      ...events,
    };
    const updatedSettings = {
      ...selectedProject?.settings,
      events: updatedEvents,
    };

    try {
      const creation_response = await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          settings: updatedSettings,
        }),
      });

      const responseData = await creation_response.json();
      console.log("response", responseData);

      // Optional: You might want to reset the form or give some feedback to the user here
      setNewEventName("");
      setNewEventDescription("");
      setEvents(updatedEvents);
      setRefresh(!refresh);
      setUniqueEventNames(Object.keys(updatedEvents));
      mutate(
        [`/api/projects/${project_id}`, accessToken],
        async (data: any) => {
          return { project: { ...data.project, settings: updatedSettings } };
        },
      );
    } catch (error) {
      console.error("Error submitting event:", error);
      // Handle the error appropriately
    }
  }

  // Deletion event
  const handleDeleteEvent = async (eventNameToDelete: string) => {
    console.log("Deleting event ", eventNameToDelete);
    // Remove the event with name eventNameToDelete from the events object
    const updatedEvents = { ...events };
    delete updatedEvents[eventNameToDelete];

    // Prepare the updated project settings
    const updatedSettings = {
      ...selectedProject.settings,
      events: updatedEvents,
    };

    console.log("updated settings", updatedSettings);

    try {
      const creation_response = await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          settings: updatedSettings,
        }),
      });

      const responseData = await creation_response.json();
      console.log("response", responseData);

      // Update state variable
      setEvents(updatedEvents);
      setRefresh(!refresh);
      setUniqueEventNames(Object.keys(updatedEvents));
      mutate(
        [`/api/projects/${project_id}`, accessToken],
        async (data: any) => {
          return { project: { ...data.project, settings: updatedSettings } };
        },
      );

      // Optional: You might want to reset the form or give some feedback to the user here
    } catch (error) {
      console.error("Error deleting event:", error);
      // Handle the error appropriately
    }
  };

  return (
    <>
      <div>
        <EventsList
          events={events}
          handleDeleteEvent={handleDeleteEvent}
          refresh={refresh}
        />
        <div>
          <span className="flex flex-row justify-between mt-8">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">
                Add a new event
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
            <Button
              variant="secondary"
              onClick={() => {
                router.push(
                  `/onboarding/customize/${selectedProject.id}?redirect=events`,
                );
              }}
              disabled={
                events &&
                max_nb_events &&
                Object.keys(events).length >= max_nb_events
              }
            >
              <Wand2 className="w-4 h-4 mr-1" /> Events suggestions
            </Button>
          </span>
        </div>
        <Card>
          <CardContent className="grid gap-2 pt-4">
            <div className="grid gap-2">
              <Label htmlFor="subject">Name</Label>
              <Input
                id="subject"
                placeholder="e.g.: rude tone of voice, user frustration, user says 'I want to cancel'..."
                value={newEventName}
                onChange={handleEventNameChange}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe how to know this event is happening, like you'd do to a 5 years old. Refer to speakers as 'the user' and 'the assistant'."
                value={newEventDescription}
                onChange={handleEventDescriptionChange}
              />
            </div>
            <Accordion type="single" collapsible>
              <AccordionItem value="webhook">
                <AccordionTrigger>
                  <span className="text-sm flex flex-row items-center text-gray-500">
                    Advanced settings (Optional)
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Webhook</Label>
                    <Input
                      id="webhook"
                      placeholder="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
                      value={newEventWebhook}
                      onChange={handleWebhookChange}
                    />
                    <Label htmlFor="description">Authorization Header</Label>
                    <Input
                      id="webhook_headers"
                      placeholder="Bearer sk-..."
                      value={newEventWebhookHeader}
                      onChange={handleWebhookHeaderChange}
                    />
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
          <CardFooter className="justify-between space-x-2">
            {events !== null && (
              <CreateEventButton
                onClick={(e) => {
                  e.preventDefault();
                  onSubmit();
                }}
                current_nb_events={Object.keys(events).length}
                max_nb_events={max_nb_events}
              />
            )}
            {events === null && (
              <CreateEventButton
                onClick={(e) => {
                  e.preventDefault();
                  onSubmit();
                }}
                current_nb_events={0}
                max_nb_events={max_nb_events}
              />
            )}
          </CardFooter>
        </Card>

        <div className="h-20"></div>
      </div>
    </>
  );
}
