import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import { Event, TaskWithEvents } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Check, Trash } from "lucide-react";

import { Badge } from "./ui/badge";

export const InteractiveEventBadge = ({
  event,
  task,
  setTask,
}: {
  event: Event;
  task: TaskWithEvents;
  setTask: (task: TaskWithEvents) => void;
}) => {
  const { accessToken } = useUser();

  const selectedProject = dataStateStore((state) => state.selectedProject);

  if (!selectedProject) {
    return <></>;
  }

  // Find the event definition in the project settings
  const eventDefinition = selectedProject.settings?.events[event.event_name];
  const { toast } = useToast();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <HoverCard openDelay={80} closeDelay={30}>
          <HoverCardTrigger>
            <Badge variant="outline" className="border hover:border-green-500">
              {event.event_name}
            </Badge>
          </HoverCardTrigger>
          <HoverCardContent side="top" className="text-sm text-left w-64">
            <h2 className="font-bold">{event.event_name}</h2>
            <p>Source: {event.source}</p>
            {eventDefinition?.description && (
              <p>{eventDefinition.description}</p>
            )}
          </HoverCardContent>
        </HoverCard>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuItem
          onClick={(mouseEvent) => {
            mouseEvent.stopPropagation();
            toast({
              title: "Coming soon 🛠️",
              description:
                "This feature is still being developed. Your changes were not be saved.",
            });
          }}
        >
          <Check className="w-4 h-4 mr-2" />
          Confirm
        </DropdownMenuItem>
        <DropdownMenuItem
          className="text-red-500"
          onClick={async (mouseEvent) => {
            mouseEvent.stopPropagation();
            // Call the API to remove the event from the task
            const response = await fetch(`/api/tasks/${task.id}/remove-event`, {
              method: "POST",
              headers: {
                Authorization: "Bearer " + accessToken,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                event_name: event.event_name,
              }),
            });
            const response_json = await response.json();
            setTask(response_json);
          }}
        >
          <Trash className="w-4 h-4 mr-2" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const AddEventDropdown = ({
  task,
  setTask,
  className,
}: {
  task: TaskWithEvents;
  setTask: (task: TaskWithEvents) => void;
  className?: string;
}) => {
  if (!task) {
    return <></>;
  }
  const { accessToken } = useUser();
  const events = task.events;
  const selectedProject = dataStateStore((state) => state.selectedProject);

  if (!selectedProject) {
    return <></>;
  }

  // Project events is an object : {event_name: EventDefinition}
  const projectEvents = selectedProject.settings?.events;

  if (!projectEvents) {
    return <></>;
  }

  const eventsNotInTask = Object.entries(projectEvents).filter(
    ([event_name, event]) => {
      // If the event is already in the task, don't show it
      return !events?.some((e) => e.event_name === event_name);
    },
  );
  if (eventsNotInTask.length === 0) {
    return <></>;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Badge
          variant="outline"
          className={cn(" hover:border-green-500", className)}
        >
          +
        </Badge>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        {Object.entries(projectEvents).map(([event_name, event]) => {
          // If the event is already in the task, don't show it
          if (events?.some((e) => e.event_name === event_name)) {
            return <></>;
          }

          return (
            <HoverCard openDelay={50} closeDelay={50}>
              <HoverCardTrigger>
                <DropdownMenuItem
                  key={event_name}
                  onClick={async (mouseEvent) => {
                    mouseEvent.stopPropagation();
                    // Call the API to ad the event to the task
                    const response = await fetch(
                      `/api/tasks/${task.id}/add-event`,
                      {
                        method: "POST",
                        headers: {
                          Authorization: "Bearer " + accessToken,
                          "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                          event: event,
                        }),
                      },
                    );
                    const response_json = await response.json();
                    setTask(response_json);
                  }}
                >
                  {event_name}
                </DropdownMenuItem>
              </HoverCardTrigger>
              <HoverCardContent side="right" className="text-sm w-64">
                <h2 className="font-bold">{event_name}</h2>
                <div>{event.description}</div>
              </HoverCardContent>
            </HoverCard>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
