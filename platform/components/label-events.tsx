import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { authFetcher } from "@/lib/fetcher";
import { cn } from "@/lib/utils";
import {
  Event,
  EventDefinition,
  Project,
  SessionWithEvents,
  TaskWithEvents,
  UserEventMetadata,
} from "@/models/models";
import { useUser } from "@propelauth/nextjs/client";
import { DropdownMenuGroup } from "@radix-ui/react-dropdown-menu";
import { Check, PlusIcon, Trash } from "lucide-react";
import useSWR from "swr";

export const EventDetectionDescription = ({
  event,
  eventDefinition,
}: {
  event: Event;
  eventDefinition: EventDefinition;
}) => {
  const roundedConfidenceScore = event.score_range?.value
    ? Math.round(event.score_range?.value * 100)
    : null;

  return (
    <div className="p-1">
      <div className="flex flex-row justify-between mb-2 items-center">
        <h2 className="font-bold">{event.event_name}</h2>
        <HoverCard openDelay={0} closeDelay={0}>
          <HoverCardTrigger>
            <Badge className="bg-green-500">{event.source}</Badge>
          </HoverCardTrigger>
          <HoverCardContent>Source</HoverCardContent>
        </HoverCard>
      </div>
      <div className="flex flex-col space-y-1">
        {eventDefinition?.description && (
          <p className="text-muted-foreground">{eventDefinition.description}</p>
        )}
        {roundedConfidenceScore &&
          event.score_range?.score_type == "confidence" && (
            <div>Confidence: {roundedConfidenceScore}%</div>
          )}
        {roundedConfidenceScore && event.score_range?.score_type == "range" && (
          <div>
            Score:{" "}
            {event?.score_range?.corrected_value?.toFixed(2) ??
              event?.score_range?.value?.toFixed(2)}
            /{event.score_range?.max}
          </div>
        )}
        {event.score_range?.score_type == "category" && (
          <div>
            Category:{" "}
            {event?.score_range?.corrected_label ?? event.score_range?.label}
          </div>
        )}
      </div>
    </div>
  );
};

export const EventBadge = ({ event }: { event: Event }) => {
  const roundedScore = event.score_range?.value
    ? Math.round(event.score_range?.value * 100) / 100
    : null;

  const badgeStyle = event.confirmed
    ? "border bg-green-500 hover:border-green-500"
    : "border hover:border-green-500";

  const score_type = event.score_range?.score_type ?? "confidence";

  return (
    <Badge variant="outline" className={badgeStyle}>
      {score_type === "confidence" && <span>{event.event_name}</span>}
      {score_type === "range" && (
        <span>
          {event.event_name}{" "}
          {event?.score_range?.corrected_value ?? roundedScore}/
          {event.score_range?.max}
        </span>
      )}
      {score_type === "category" && (
        <span>
          {event.event_name}:{" "}
          {event?.score_range?.corrected_label ?? event.score_range?.label}
        </span>
      )}
    </Badge>
  );
};

export const UserEventMetadataBadge = ({
  event,
}: {
  event: UserEventMetadata;
}) => {
  const badgeStyle = "border hover:border-green-500";
  //TODO Get this info from the event user data
  // const score_type = event.score_range?.score_type ?? "confidence";

  return (
    <Badge variant="outline" className={badgeStyle}>
      {event.event_name} ({event.count})
    </Badge>
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
  const project_id = task.project_id;
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  if (!selectedProject) {
    return <></>;
  }

  // Find the event definition in the project settings
  const eventDefinition = selectedProject.settings?.events[event.event_name];

  if (!eventDefinition) {
    return <></>;
  }

  return (
    <DropdownMenu>
      <HoverCard openDelay={0} closeDelay={0}>
        <DropdownMenuTrigger asChild>
          <HoverCardTrigger>
            <EventBadge event={event} />
          </HoverCardTrigger>
        </DropdownMenuTrigger>
        <HoverCardContent className="text-sm text-left w-96 z-60" side="top">
          <EventDetectionDescription
            event={event}
            eventDefinition={eventDefinition}
          />
        </HoverCardContent>
      </HoverCard>
      <DropdownMenuContent align="start">
        <DropdownMenuItem
          onClick={async (mouseEvent) => {
            mouseEvent.stopPropagation();
            // Call the API to remove the event from the task
            const response = await fetch(
              `/api/events/${event.project_id}/confirm/${event.id}`,
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
            setTask({
              ...task,
              events: task.events.map((e) => {
                if (e.id === event.id) {
                  return response_json;
                }
                return e;
              }),
            });
          }}
        >
          <Check className="w-4 h-4 mr-2" />
          Confirm
        </DropdownMenuItem>
        {event?.score_range?.score_type === "category" && (
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>Change class</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              {// Create one dropdown item for each category
              eventDefinition?.score_range_settings?.categories?.map(
                (category) => {
                  return (
                    <DropdownMenuItem
                      key={category}
                      onClick={async (mouseEvent) => {
                        mouseEvent.stopPropagation();
                        const response = await fetch(
                          `/api/events/${event.project_id}/label/${event.id}`,
                          {
                            method: "POST",
                            headers: {
                              Authorization: "Bearer " + accessToken,
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                              new_label: category,
                            }),
                          },
                        );
                        const response_json = await response.json();
                        setTask({
                          ...task,
                          events: task.events.map((e) => {
                            if (e.id === event.id) {
                              return response_json;
                            }
                            return e;
                          }),
                        });
                      }}
                    >
                      {category}
                    </DropdownMenuItem>
                  );
                },
              )}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        )}
        {event?.score_range?.score_type === "range" &&
          eventDefinition?.score_range_settings?.max != undefined &&
          eventDefinition?.score_range_settings?.min != undefined && (
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>Change score</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                {
                  // Create one dropdown item for each integer in the range
                  Array.from(
                    {
                      length:
                        eventDefinition?.score_range_settings?.max -
                        eventDefinition?.score_range_settings?.min +
                        1,
                    },
                    (_, i) =>
                      (eventDefinition?.score_range_settings?.min ?? 1) + i,
                  ).map((score) => {
                    return (
                      <DropdownMenuItem
                        key={score}
                        onClick={async (mouseEvent) => {
                          mouseEvent.stopPropagation();
                          const response = await fetch(
                            `/api/events/${event.project_id}/value/${event.id}`,
                            {
                              method: "POST",
                              headers: {
                                Authorization: "Bearer " + accessToken,
                                "Content-Type": "application/json",
                              },
                              body: JSON.stringify({
                                new_value: score,
                              }),
                            },
                          );
                          const response_json = await response.json();
                          setTask({
                            ...task,
                            events: task.events.map((e) => {
                              if (e.id === event.id) {
                                return response_json;
                              }
                              return e;
                            }),
                          });
                        }}
                      >
                        {score}
                      </DropdownMenuItem>
                    );
                  })
                }
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          )}
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
  const { accessToken } = useUser();
  const project_id = task.project_id;
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  if (!task) {
    return <></>;
  }

  const events = task.events;

  if (!selectedProject) {
    return <></>;
  }

  // Project events is an object : {event_name: EventDefinition}
  const projectEvents = selectedProject.settings?.events;

  if (!projectEvents) {
    return <></>;
  }

  const eventsNotInTask = Object.entries(projectEvents).filter(
    ([event_name]) => {
      // If the event is already in the task, don't show it
      return !events?.some((e) => e.event_name === event_name);
    },
  );
  if (eventsNotInTask.length === 0) {
    return <></>;
  }

  function addEvent({
    event,
    scoreRangeValue,
    scoreCategoryLabel,
  }: {
    event: EventDefinition;
    scoreRangeValue?: number;
    scoreCategoryLabel?: string;
  }) {
    // Call the API to add the event to the task
    fetch(`/api/tasks/${task.id}/add-event`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event: event,
        score_range_value: scoreRangeValue,
        score_category_label: scoreCategoryLabel,
      }),
    })
      .then((response) => response.json())
      .then((response_json) => {
        setTask(response_json);
      });
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Badge
          variant="outline"
          className={cn("hover:border-green-500", className)}
        >
          +
        </Badge>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="center">
        <DropdownMenuGroup className="overflow-y-auto max-h-[20rem]">
          {Object.entries(projectEvents).map(([event_name, event]) => {
            // If the event is already in the task, don't show it
            if (events?.some((e) => e.event_name === event_name)) {
              return <></>;
            }

            const score_type =
              event.score_range_settings?.score_type ?? "confidence";

            return (
              <HoverCard openDelay={0} closeDelay={0} key={event.id}>
                <HoverCardTrigger>
                  {score_type === "confidence" && (
                    <DropdownMenuItem
                      key={event_name}
                      onClick={async (mouseEvent) => {
                        mouseEvent.stopPropagation();
                        addEvent({ event });
                      }}
                    >
                      {event_name}
                    </DropdownMenuItem>
                  )}
                  {score_type === "range" && (
                    <DropdownMenuSub key={event_name}>
                      <DropdownMenuSubTrigger>
                        {event_name}
                      </DropdownMenuSubTrigger>
                      <DropdownMenuSubContent>
                        {
                          // Create one dropdown item for each value in the range (min to max)
                          Array.from(
                            { length: event.score_range_settings?.max ?? 1 },
                            (_, i) => i + 1,
                          ).map((value) => {
                            return (
                              <DropdownMenuItem
                                key={value}
                                onClick={async (mouseEvent) => {
                                  mouseEvent.stopPropagation();
                                  addEvent({
                                    event,
                                    scoreRangeValue: value,
                                  });
                                }}
                              >
                                {value}
                              </DropdownMenuItem>
                            );
                          })
                        }
                      </DropdownMenuSubContent>
                    </DropdownMenuSub>
                  )}
                  {score_type === "category" && (
                    <DropdownMenuSub key={event_name}>
                      <DropdownMenuSubTrigger>
                        {event_name}
                      </DropdownMenuSubTrigger>
                      <DropdownMenuSubContent>
                        {// Create one dropdown item for each category
                        event.score_range_settings?.categories?.map(
                          (category) => {
                            return (
                              <DropdownMenuItem
                                key={category}
                                onClick={async (mouseEvent) => {
                                  mouseEvent.stopPropagation();
                                  addEvent({
                                    event,
                                    scoreCategoryLabel: category,
                                  });
                                }}
                              >
                                {category}
                              </DropdownMenuItem>
                            );
                          },
                        )}
                      </DropdownMenuSubContent>
                    </DropdownMenuSub>
                  )}
                </HoverCardTrigger>
                <HoverCardContent side="left" className="text-sm w-96 z-60">
                  <h2 className="font-bold">{event_name}</h2>
                  <div>{event.description}</div>
                </HoverCardContent>
              </HoverCard>
            );
          })}
        </DropdownMenuGroup>
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
  const project_id = session.project_id;
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  if (!selectedProject) {
    return <></>;
  }

  // Find the event definition in the project settings
  const eventDefinition = selectedProject.settings?.events[event.event_name];

  if (!eventDefinition) {
    return <></>;
  }

  return (
    <DropdownMenu>
      <HoverCard openDelay={0} closeDelay={0}>
        <DropdownMenuTrigger asChild>
          <HoverCardTrigger>
            <EventBadge event={event} />
          </HoverCardTrigger>
        </DropdownMenuTrigger>
        <HoverCardContent className="text-sm text-left w-96 z-60" side="top">
          <EventDetectionDescription
            event={event}
            eventDefinition={eventDefinition}
          />
        </HoverCardContent>
      </HoverCard>
      <DropdownMenuContent align="start">
        <DropdownMenuItem
          onClick={async (mouseEvent) => {
            mouseEvent.stopPropagation();
            // Call the API to remove the event from the task
            const response = await fetch(
              `/api/events/${event.project_id}/confirm/${event.id}`,
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
            setSession({
              ...session,
              events: session.events.map((e) => {
                if (e.id === event.id) {
                  return response_json;
                }
                return e;
              }),
            });
          }}
        >
          <Check className="w-4 h-4 mr-2" />
          Confirm
        </DropdownMenuItem>
        {event?.score_range?.score_type === "category" && (
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>Change class</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              {// Create one dropdown item for each category
              eventDefinition?.score_range_settings?.categories?.map(
                (category) => {
                  return (
                    <DropdownMenuItem
                      key={category}
                      onClick={async (mouseEvent) => {
                        mouseEvent.stopPropagation();
                        const response = await fetch(
                          `/api/events/${event.project_id}/label/${event.id}`,
                          {
                            method: "POST",
                            headers: {
                              Authorization: "Bearer " + accessToken,
                              "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                              new_label: category,
                            }),
                          },
                        );
                        const response_json = await response.json();
                        setSession({
                          ...session,
                          events: session.events.map((e) => {
                            if (e.id === event.id) {
                              return response_json;
                            }
                            return e;
                          }),
                        });
                      }}
                    >
                      {category}
                    </DropdownMenuItem>
                  );
                },
              )}
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        )}
        {event?.score_range?.score_type === "range" &&
          eventDefinition?.score_range_settings?.max != undefined &&
          eventDefinition?.score_range_settings?.min != undefined && (
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>Change score</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                {
                  // Create one dropdown item for each integer in the range
                  Array.from(
                    {
                      length:
                        eventDefinition?.score_range_settings?.max -
                        eventDefinition?.score_range_settings?.min +
                        1,
                    },
                    (_, i) =>
                      (eventDefinition?.score_range_settings?.min ?? 1) + i,
                  ).map((score) => {
                    return (
                      <DropdownMenuItem
                        key={score}
                        onClick={async (mouseEvent) => {
                          mouseEvent.stopPropagation();
                          const response = await fetch(
                            `/api/events/${event.project_id}/value/${event.id}`,
                            {
                              method: "POST",
                              headers: {
                                Authorization: "Bearer " + accessToken,
                                "Content-Type": "application/json",
                              },
                              body: JSON.stringify({
                                new_value: score,
                              }),
                            },
                          );
                          const response_json = await response.json();
                          setSession({
                            ...session,
                            events: session.events.map((e) => {
                              if (e.id === event.id) {
                                return response_json;
                              }
                              return e;
                            }),
                          });
                        }}
                      >
                        {score}
                      </DropdownMenuItem>
                    );
                  })
                }
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          )}
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
  setSheetOpen,
  setSheetToOpen,
}: {
  session: SessionWithEvents;
  setSession: (session: SessionWithEvents) => void;
  className?: string;
  setSheetOpen?: (open: boolean) => void;
  setSheetToOpen?: (sheet: string | null) => void;
}) => {
  const { accessToken } = useUser();
  const project_id = session.project_id;
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  if (!session) {
    return <></>;
  }
  const events = session.events;

  if (!selectedProject) {
    return <></>;
  }

  // Project events is an object : {event_name: EventDefinition}
  const projectEvents = selectedProject.settings?.events;

  if (!projectEvents) {
    return <></>;
  }

  const eventsNotInSession = Object.entries(projectEvents).filter(
    ([event_name]) => {
      // If the event is already in the task, don't show it
      return !events?.some((e) => e.event_name === event_name);
    },
  );
  if (eventsNotInSession.length === 0) {
    return <></>;
  }

  function addEvent({
    event,
    scoreRangeValue,
    scoreCategoryLabel,
  }: {
    event: EventDefinition;
    scoreRangeValue?: number;
    scoreCategoryLabel?: string;
  }) {
    // Call the API to add the event to the task
    fetch(`/api/sessions/${session.id}/add-event`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        event: event,
        score_range_value: scoreRangeValue,
        score_category_label: scoreCategoryLabel,
      }),
    })
      .then((response) => response.json())
      .then((response_json) => {
        setSession(response_json);
      });
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
      <DropdownMenuContent align="center">
        <DropdownMenuGroup className="overflow-y-auto max-h-[20rem]">
          {Object.entries(projectEvents).map(([event_name, event]) => {
            // If the event is already in the task, don't show it
            if (events?.some((e) => e.event_name === event_name)) {
              return <></>;
            }

            const score_type =
              event.score_range_settings?.score_type ?? "confidence";

            return (
              <HoverCard openDelay={0} closeDelay={0} key={event.id}>
                <HoverCardTrigger>
                  {score_type === "confidence" && (
                    <DropdownMenuItem
                      key={event_name}
                      onClick={async (mouseEvent) => {
                        mouseEvent.stopPropagation();
                        addEvent({ event });
                      }}
                    >
                      {event_name}
                    </DropdownMenuItem>
                  )}
                  {score_type === "range" && (
                    <DropdownMenuSub key={event_name}>
                      <DropdownMenuSubTrigger>
                        {event_name}
                      </DropdownMenuSubTrigger>
                      <DropdownMenuSubContent>
                        {
                          // Create one dropdown item for each value in the range (min to max)
                          Array.from(
                            { length: event.score_range_settings?.max ?? 1 },
                            (_, i) => i + 1,
                          ).map((value) => {
                            return (
                              <DropdownMenuItem
                                key={value}
                                onClick={async (mouseEvent) => {
                                  mouseEvent.stopPropagation();
                                  addEvent({
                                    event,
                                    scoreRangeValue: value,
                                  });
                                }}
                              >
                                {value}
                              </DropdownMenuItem>
                            );
                          })
                        }
                      </DropdownMenuSubContent>
                    </DropdownMenuSub>
                  )}
                  {score_type === "category" && (
                    <DropdownMenuSub key={event_name}>
                      <DropdownMenuSubTrigger>
                        {event_name}
                      </DropdownMenuSubTrigger>
                      <DropdownMenuSubContent>
                        {// Create one dropdown item for each category
                        event.score_range_settings?.categories?.map(
                          (category) => {
                            return (
                              <DropdownMenuItem
                                key={category}
                                onClick={async (mouseEvent) => {
                                  mouseEvent.stopPropagation();
                                  addEvent({
                                    event,
                                    scoreCategoryLabel: category,
                                  });
                                }}
                              >
                                {category}
                              </DropdownMenuItem>
                            );
                          },
                        )}
                      </DropdownMenuSubContent>
                    </DropdownMenuSub>
                  )}
                </HoverCardTrigger>
                <HoverCardContent side="left" className="text-sm w-96 z-60">
                  <h2 className="font-bold">{event_name}</h2>
                  <div>{event.description}</div>
                </HoverCardContent>
              </HoverCard>
            );
          })}
        </DropdownMenuGroup>
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
