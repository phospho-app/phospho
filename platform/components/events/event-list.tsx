"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { Project, ScoreRangeType } from "@/models/models";
import { EventDefinition } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, Pencil, Sparkles, Trash } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR, { useSWRConfig } from "swr";

import CreateEvent from "./create-event";
import RunEvent from "./run-event";

function EllipsisVertical() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="1" />
      <circle cx="12" cy="5" r="1" />
      <circle cx="12" cy="19" r="1" />
    </svg>
  );
}

function EventRow({
  eventDefinition,
  handleDeleteEvent,
  handleOnClick,
}: {
  eventDefinition: EventDefinition;
  handleDeleteEvent: (eventNameToDelete: string) => void;
  handleOnClick: (eventName: string) => void;
}) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [alertOpen, setAlertOpen] = useState(false);
  const [tableIsClickable, setTableIsClickable] = useState(true);
  const [sheetToOpen, setSheetToOpen] = useState<string | null>(null);

  return (
    <TableRow
      onClick={(mouseEvent) => {
        mouseEvent.stopPropagation();
        if (tableIsClickable) {
          handleOnClick(eventDefinition.id ?? "");
        }
      }}
      className="cursor-pointer"
    >
      <TableCell>{eventDefinition.event_name}</TableCell>
      <TableCell className="text-left">{eventDefinition.description}</TableCell>
      <TableCell className="text-left">
        {eventDefinition?.webhook && eventDefinition.webhook.length > 1 ? (
          <Badge>active</Badge>
        ) : (
          <Badge variant="secondary">None</Badge>
        )}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex flex-row items-center justify-end">
          <Sheet
            open={sheetOpen}
            onOpenChange={setSheetOpen}
            key={`${eventDefinition.event_name}_edit`}
          >
            <AlertDialog
              open={alertOpen}
              onOpenChange={setAlertOpen}
              key={`${eventDefinition.event_name}_delete`}
            >
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    setSheetToOpen("run");
                  }}
                >
                  <Sparkles className="text-green-500 size-4 mr-2" />
                  Detect
                  <ChevronRight className="size-4 ml-2" />
                </Button>
              </SheetTrigger>
              <DropdownMenu>
                <DropdownMenuTrigger
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                  }}
                >
                  <Button size="icon" variant="ghost">
                    <EllipsisVertical />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <SheetTrigger asChild>
                    <DropdownMenuItem
                      onClick={(mouseEvent) => {
                        mouseEvent.stopPropagation();
                        setSheetToOpen("edit");
                      }}
                    >
                      <Pencil className="w-4 h-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                  </SheetTrigger>
                  <AlertDialogTrigger asChild>
                    <DropdownMenuItem
                      className=" text-red-500"
                      onClick={(mouseEvent) => {
                        mouseEvent.stopPropagation();
                        setAlertOpen(true);
                      }}
                    >
                      <div className="flex flex-row items-center">
                        <Trash className="w-4 h-4 mr-2" />
                        Delete
                      </div>
                    </DropdownMenuItem>
                  </AlertDialogTrigger>
                </DropdownMenuContent>
              </DropdownMenu>
              <AlertDialogContent className="md:w-1/3">
                <AlertDialogTitle>
                  Are you sure you want to delete &quot;
                  {eventDefinition.event_name}
                  &quot;?
                </AlertDialogTitle>
                <AlertDialogDescription>
                  <div>
                    This will delete{" "}
                    <span className="font-bold">all previous detections.</span>
                  </div>
                  <div>This action cannot be undone.</div>
                </AlertDialogDescription>
                <AlertDialogAction
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    handleDeleteEvent(eventDefinition.event_name);
                    setAlertOpen(false);
                  }}
                >
                  Delete event definition and all previous detections
                </AlertDialogAction>
                <AlertDialogCancel
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    setAlertOpen(false);
                  }}
                >
                  Cancel
                </AlertDialogCancel>
              </AlertDialogContent>
              <SheetContent
                className="md:w-1/2 overflow-auto"
                onOpenAutoFocus={(mouseEvent) => {
                  mouseEvent.stopPropagation();
                  setTableIsClickable(false);
                }}
                onCloseAutoFocus={(mouseEvent) => {
                  mouseEvent.stopPropagation();
                  setTableIsClickable(true);
                }}
              >
                {sheetToOpen === "run" && (
                  <RunEvent
                    setOpen={setSheetOpen}
                    eventToRun={eventDefinition}
                    key={eventDefinition.id}
                  />
                )}
                {sheetToOpen === "edit" && (
                  <CreateEvent
                    setOpen={setSheetOpen}
                    eventToEdit={eventDefinition}
                    key={eventDefinition.id}
                  />
                )}
              </SheetContent>
            </AlertDialog>
          </Sheet>
        </div>
      </TableCell>
    </TableRow>
  );
}

function EventsList({ event_type }: { event_type?: ScoreRangeType }) {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const { accessToken } = useUser();

  const project_id = navigationStateStore((state) => state.project_id);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const events = selectedProject?.settings?.events || {};
  const eventArray = Object.entries(events);
  // sort the events by name
  eventArray.sort((a, b) => a[0].localeCompare(b[0]));

  // Deletion event
  const handleDeleteEvent = async (eventNameToDelete: string) => {
    // Prepare the updated project settings
    if (!selectedProject?.settings) {
      return;
    }
    // Remove the event with name eventNameToDelete from the events object
    delete selectedProject.settings.events[eventNameToDelete];

    try {
      await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedProject),
      });
      mutate([`/api/projects/${project_id}`, accessToken], async () => {
        return { project: selectedProject };
      });
    } catch (error) {
      console.error("Error deleting event:", error);
    }
  };

  const handleOnClick = (eventId: string) => {
    router.push(`/org/insights/events/${encodeURI(eventId)}`);
  };

  // Make this a mapping such that we can write: event_type_to_none_label[event_type ]
  const event_type_to_none_label: { [key: string]: string } = {
    confidence: "Add a tag to get started",
    range: "Add a scorer to get started",
    category: "Add a classifier to get started",
    undefined: "Add an event to get started",
  };

  const noEvents =
    events === null ||
    eventArray.filter(
      ([, eventDefinition]) =>
        event_type === undefined ||
        eventDefinition.score_range_settings?.score_type === event_type,
    ).length === 0;

  return (
    <>
      <Card className="mt-4">
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Name</TableHead>
                <TableHead className="text-left">Description</TableHead>
                <TableHead className="text-left w-[100px]">Webhook</TableHead>
                <TableHead className="text-right justify-end w-[10%]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!noEvents &&
                eventArray.map(([, eventDefinition], index) => {
                  if (
                    event_type !== undefined &&
                    eventDefinition.score_range_settings?.score_type !==
                      event_type
                  ) {
                    return null;
                  }
                  return (
                    <EventRow
                      key={index}
                      eventDefinition={eventDefinition}
                      handleDeleteEvent={handleDeleteEvent}
                      handleOnClick={handleOnClick}
                    />
                  );
                })}
              {noEvents && (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="text-center text-muted-foreground"
                  >
                    {event_type_to_none_label[event_type ?? "undefined"]}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}

export default EventsList;
