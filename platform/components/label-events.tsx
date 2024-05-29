import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import { Event, SessionWithEvents, TaskWithEvents } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Check, PlusIcon, Trash } from "lucide-react";

export const EventDetectionDescription = ({
  event,
  eventDefinition,
}: {
  event: Event;
  eventDefinition: any;
}) => {
  const roundedScore = event.score_range?.value
    ? Math.round(event.score_range?.value * 100) / 100
    : null;

  // Create scoreType, a capitalized string of score_type
  const scoreType = event.score_range?.score_type
    ? event.score_range?.score_type.charAt(0).toUpperCase() +
      event.score_range?.score_type.slice(1)
    : null;

  return (
    <div className="p-1">
      <div className="flex flex-row justify-between mb-2 items-center">
        <h2 className="font-bold">{event.event_name}</h2>
        <Badge className="bg-green-500">{event.source}</Badge>
      </div>
      <div className="flex flex-col space-y-1">
        {eventDefinition?.description && (
          <p className="text-muted-foreground">{eventDefinition.description}</p>
        )}
        {roundedScore && scoreType && (
          <p>
            <span>{scoreType}:</span> {roundedScore}
          </p>
        )}
      </div>
    </div>
  );
};

export const InteractiveEventBadgeForTasks = ({
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
          <HoverCardContent side="top" className="text-sm text-left max-w-96">
            <EventDetectionDescription
              event={event}
              eventDefinition={eventDefinition}
            />
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
                "This feature is still being developed. Your changes were not saved.",
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

export const AddEventDropdownForTasks = ({
  task,
  setTask,
  className,
  setSheetOpen,
  setSheetToOpen,
}: {
  task: TaskWithEvents;
  setTask: (task: TaskWithEvents) => void;
  className?: string;
  setSheetOpen?: (open: boolean) => void;
  setSheetToOpen?: (sheet: string | null) => void;
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
        {setSheetOpen !== undefined && setSheetToOpen !== undefined && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={(mouseEvent) => {
                mouseEvent.stopPropagation();
                setSheetToOpen("edit");
                setSheetOpen(true);
              }}
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add a new event
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const InteractiveEventBadgeForSessions = ({
  event,
  session,
  setSession,
}: {
  event: Event;
  session: SessionWithEvents;
  setSession: (task: SessionWithEvents) => void;
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
            <EventDetectionDescription
              event={event}
              eventDefinition={eventDefinition}
            />
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
                "This feature is still being developed. Your changes were not saved.",
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
            // Call the API to remove the event from the session
            const response = await fetch(
              `/api/sessions/${session.id}/remove-event`,
              {
                method: "POST",
                headers: {
                  Authorization: "Bearer " + accessToken,
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  event_name: event.event_name,
                }),
              },
            );
            const response_json = await response.json();
            setSession(response_json);
          }}
        >
          <Trash className="w-4 h-4 mr-2" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export const AddEventDropdownForSessions = ({
  session,
  setSession,
  className,
}: {
  session: SessionWithEvents;
  setSession: (session: SessionWithEvents) => void;
  className?: string;
}) => {
  if (!session) {
    return <></>;
  }
  const { accessToken } = useUser();
  const events = session.events;
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
                    // Call the API to add the event to the task
                    const response = await fetch(
                      `/api/sessions/${session.id}/add-event`,
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
                    setSession(response_json);
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
