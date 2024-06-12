"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components//ui/table";
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
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, Pencil, Sparkles, Trash } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useSWRConfig } from "swr";

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
  eventDefinition: any;
  handleDeleteEvent: (eventNameToDelete: string) => void;
  handleOnClick: (eventName: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [tableIsClickable, setTableIsClickable] = useState(true);
  const [sheetToOpen, setSheetToOpen] = useState<string | null>(null);

  return (
    <TableRow
      onClick={(mouseEvent) => {
        mouseEvent.stopPropagation();
        if (tableIsClickable) {
          handleOnClick(eventDefinition.id);
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
            open={open}
            onOpenChange={setOpen}
            key={`${eventDefinition.event_name}_edit`}
          >
            <AlertDialog>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    setSheetToOpen("run");
                  }}
                >
                  <Sparkles className="text-green-500 h-4 w-4 mr-2" />
                  Detect
                  <ChevronRight className="h-4 w-4 ml-2" />
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
                  {/* <SheetTrigger asChild>
                    <DropdownMenuItem
                      onClick={(mouseEvent) => {
                        mouseEvent.stopPropagation();
                        setSheetToOpen("run");
                      }}
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Detect
                    </DropdownMenuItem>
                  </SheetTrigger> */}
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
                  <DropdownMenuItem
                    className=" text-red-500"
                    onClick={(mouseEvent) => {
                      mouseEvent.stopPropagation();
                    }}
                  >
                    <AlertDialogTrigger>
                      <div className="flex flex-row items-center">
                        <Trash className="w-4 h-4 mr-2" />
                        Delete
                      </div>
                    </AlertDialogTrigger>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <AlertDialogContent className="md:w-1/3">
                <AlertDialogTitle>
                  Are you sure you want to delete the event "
                  {eventDefinition.event_name}"?
                </AlertDialogTitle>
                <AlertDialogDescription>
                  <div>
                    This will delete <span className="font-bold">all</span>{" "}
                    previous detections of this event.
                  </div>
                  <div>This action cannot be undone.</div>
                </AlertDialogDescription>
                <AlertDialogAction
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    handleDeleteEvent(eventDefinition.event_name);
                  }}
                >
                  Delete event and all previous detections
                </AlertDialogAction>
                <AlertDialogCancel
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                  }}
                >
                  Cancel
                </AlertDialogCancel>
              </AlertDialogContent>
            </AlertDialog>
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
                  setOpen={setOpen}
                  eventToRun={eventDefinition}
                  key={eventDefinition.id}
                />
              )}
              {sheetToOpen === "edit" && (
                <CreateEvent
                  setOpen={setOpen}
                  eventNameToEdit={eventDefinition.event_name}
                  key={eventDefinition.id}
                />
              )}
            </SheetContent>
          </Sheet>
        </div>
      </TableCell>
    </TableRow>
  );
}

function EventsList() {
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { mutate } = useSWRConfig();
  const { accessToken } = useUser();

  const events = selectedProject?.settings?.events || {};
  const eventArray = Object.entries(events);
  // sort the events by name
  eventArray.sort((a, b) => a[0].localeCompare(b[0]));
  const router = useRouter();

  // Deletion event
  const handleDeleteEvent = async (eventNameToDelete: string) => {
    // Prepare the updated project settings
    if (!selectedProject?.settings) {
      return;
    }
    // Remove the event with name eventNameToDelete from the events object
    delete selectedProject.settings.events[eventNameToDelete];

    try {
      const creation_response = await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(selectedProject),
      });
      mutate(
        [`/api/projects/${project_id}`, accessToken],
        async (data: any) => {
          return { project: selectedProject };
        },
      );
    } catch (error) {
      console.error("Error deleting event:", error);
    }
  };

  const handleOnClick = (eventId: string) => {
    router.push(`/org/insights/events/${encodeURI(eventId)}`);
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
                  <TableHead className="text-right justify-end"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {eventArray.map(([eventName, eventDefinition], index) => (
                  <EventRow
                    key={index}
                    eventDefinition={eventDefinition}
                    handleDeleteEvent={handleDeleteEvent}
                    handleOnClick={handleOnClick}
                  />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}

export default EventsList;
