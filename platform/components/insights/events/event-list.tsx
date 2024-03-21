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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useSWRConfig } from "swr";

function EventsList() {
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { mutate } = useSWRConfig();
  const { accessToken } = useUser();

  const events = selectedProject?.settings?.events || {};

  if (!selectedProject) {
    return <></>;
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

      // Mutate state variable
      mutate(
        [`/api/projects/${project_id}`, accessToken],
        async (data: any) => {
          return { project: { ...data.project, settings: updatedSettings } };
        },
      );

      // Optional: You might want to reset the form or give some feedback to the user here
    } catch (error) {
      console.error("Error deleting event:", error);
    }
  };

  return (
    <>
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
                  ([eventName, eventDefinition], index) => {
                    return (
                      <TableRow key={index}>
                        <TableCell>{eventName}</TableCell>
                        <TableCell className="text-left">
                          {eventDefinition.description}
                        </TableCell>
                        <TableCell className="text-left">
                          {eventDefinition?.webhook &&
                          eventDefinition.webhook.length > 1 ? (
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
}

export default EventsList;
