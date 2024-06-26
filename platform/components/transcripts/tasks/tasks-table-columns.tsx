import {
  AddEventDropdownForTasks,
  InteractiveEventBadgeForTasks,
} from "@/components/label-events";
import { SentimentSettings } from "@/components/sentiment-settings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { getLanguageLabel } from "@/lib/utils";
import {
  Event,
  EventDefinition,
  Project,
  TaskWithEvents,
} from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  Check,
  ChevronRight,
  EllipsisVertical,
  PenSquare,
  Play,
  PlusIcon,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import useSWR, { KeyedMutator } from "swr";

async function flagTask({
  task_id,
  flag,
  accessToken,
  project_id,
  mutateTasks,
}: {
  task_id: string;
  flag: string;
  accessToken?: string;
  project_id?: string | null;
  mutateTasks: KeyedMutator<any>;
}) {
  if (!accessToken) return;
  if (!project_id) return;

  const creation_response = await fetch(`/api/tasks/${task_id}/flag`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + accessToken,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      flag: flag,
    }),
  });
  mutateTasks((data: any) => {
    // Edit the Task with the same task id
    data.tasks = data.tasks.map((task: TaskWithEvents) => {
      if (task.id === task_id) {
        task.flag = flag;
      }
      return task;
    });
    return data;
  });
}

export function getColumns({
  mutateTasks,
  setSheetOpen,
  setSheetToOpen,
  setEventDefinition,
}: {
  mutateTasks: KeyedMutator<any>;
  setSheetOpen: (open: boolean) => void;
  setSheetToOpen: (sheet: string | null) => void;
  setEventDefinition: (event: EventDefinition | null) => void;
}): ColumnDef<TaskWithEvents>[] {
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

  let uniqueEventNamesInData: string[] = [];
  const { data: uniqueEvents } = useSWR(
    project_id
      ? [`/api/projects/${project_id}/unique-events`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  if (project_id && uniqueEvents?.events) {
    uniqueEventNamesInData = Array.from(
      new Set(
        uniqueEvents.events.map((event: Event) => event.event_name as string),
      ),
    );
  }

  const columns: ColumnDef<TaskWithEvents>[] = [
    // id
    // {
    //   header: ({ column }) => {
    //     return <></>;
    //   },
    //   accessorKey: "id",
    //   cell: ({ row }) => {
    //     return <></>;
    //   },
    //   enableHiding: true,
    // },
    // Date
    {
      header: ({ column }) => {
        return (
          <div className="flex flex-row items-center space-x-2 justify-between">
            Date
            <Button
              variant="ghost"
              size="icon"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
            >
              {
                // Show the sorting icon based on the current sorting state
                column.getIsSorted() === "desc" ? (
                  <ArrowUp className="h-4 w-4" />
                ) : (
                  <ArrowDown className="h-4 w-4" />
                )
              }
            </Button>
          </div>
        );
      },
      accessorKey: "created_at",
      cell: ({ row }) => (
        <div>
          {formatUnixTimestampToLiteralDatetime(
            Number(row.original.created_at),
          )}
        </div>
      ),
    },
    // Flag
    {
      header: ({ column }) => {
        return (
          <div className="flex items-center">
            <Sparkles className="h-4 w-4 mr-1 text-green-500" />
            Eval
          </div>
        );
      },
      accessorKey: "flag",
      cell: (row) => (
        <DropdownMenu>
          <HoverCard openDelay={50} closeDelay={50}>
            <DropdownMenuTrigger>
              <HoverCardTrigger asChild>
                <div className="flex flex-row items-center">
                  <Badge
                    variant={
                      (row.getValue() as string) === "success"
                        ? "secondary"
                        : (row.getValue() as string) === "failure"
                          ? "destructive"
                          : "secondary"
                    }
                    className="hover:border-green-500 "
                  >
                    {row.getValue() as string}
                    {row.getValue() === null && <div className="h-3 w-6"></div>}
                  </Badge>
                  {row.row.original.notes && (
                    <PenSquare className="h-4 w-4 ml-1" />
                  )}
                </div>
              </HoverCardTrigger>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem
                onClick={(mouseEvent) => {
                  // This is used to avoid clicking on the row as well
                  mouseEvent.stopPropagation();
                  // Flag the task as success
                  flagTask({
                    task_id: row.row.original.id,
                    flag: "success",
                    accessToken: accessToken,
                    project_id: project_id,
                    mutateTasks: mutateTasks,
                  });
                }}
              >
                {(row.getValue() as string) === "success" && (
                  <Check className="h-4 w-4 mr-1" />
                )}
                Success
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(mouseEvent) => {
                  // This is used to avoid clicking on the row as well
                  mouseEvent.stopPropagation();
                  // Flag the task as failure
                  flagTask({
                    task_id: row.row.original.id,
                    flag: "failure",
                    accessToken: accessToken,
                    project_id: project_id,
                    mutateTasks: mutateTasks,
                  });
                }}
              >
                {(row.getValue() as string) === "failure" && (
                  <Check className="h-4 w-4 mr-1" />
                )}
                Failure
              </DropdownMenuItem>
            </DropdownMenuContent>
            <HoverCardContent align="start">
              <div className="flex flex-col space-y-1">
                {!row.row.original.last_eval && <span>No eval</span>}
                {row.row.original.last_eval && (
                  <div>
                    <span className="font-bold">Last eval source: </span>
                    <span>{row.row.original.last_eval?.source}</span>
                  </div>
                )}
                {row.row.original.notes && (
                  <div>
                    <span className="font-bold">Notes: </span>
                    <span>{row.row.original.notes}</span>
                  </div>
                )}
              </div>
            </HoverCardContent>
          </HoverCard>
        </DropdownMenu>
      ),
    },
    // Events
    {
      header: ({ column }) => {
        return (
          <div className="flex items-center space-x-2 justify-between">
            <div className="flex flex-row items-center space-x-1">
              <Sparkles className="h-4 w-4 text-green-500" />
              <div>Events</div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <EllipsisVertical className="w-5 h-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel>
                  <div className="flex flex-row items-center">
                    <Sparkles className="w-4 h-4 text-green-500 mr-1" />
                    <div>Detect event</div>
                  </div>
                </DropdownMenuLabel>
                {eventArray.map(([event_name, event_definition]) => {
                  return (
                    <DropdownMenuItem
                      key={event_definition.event_name}
                      onClick={(mouseEvent) => {
                        // This is used to avoid clicking on the row as well
                        mouseEvent.stopPropagation();
                        setEventDefinition(event_definition);
                        setSheetOpen(true);
                        setSheetToOpen("run");
                      }}
                    >
                      {event_definition.event_name}
                    </DropdownMenuItem>
                  );
                })}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={(mouseEvent) => {
                    // This is used to avoid clicking on the row as well
                    mouseEvent.stopPropagation();
                    setSheetToOpen("edit");
                    setSheetOpen(true);
                    setEventDefinition(null);
                  }}
                >
                  <PlusIcon className="w-4 h-4 mr-1" />
                  Add new event
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        );
      },
      accessorKey: "events",
      cell: (row) => (
        <div className="group flex items-center justify-between space-y-1">
          <div className="flex flex-wrap space-x-1">
            {(row.getValue() as Event[]).map((event: Event) => {
              return (
                <InteractiveEventBadgeForTasks
                  key={event.event_name}
                  event={event}
                  task={row.row.original as TaskWithEvents}
                  setTask={(task: TaskWithEvents) => {
                    // Use mutateTasks
                    mutateTasks((data: any) => {
                      // Edit the Task with the same task id
                      data.tasks = data.tasks.map(
                        (existingTask: TaskWithEvents) => {
                          if (existingTask.id === task.id) {
                            return task;
                          }
                          return existingTask;
                        },
                      );
                      return data;
                    });
                  }}
                />
              );
            })}
          </div>
          {/* <div className="flex-grow"></div> */}
          <div className="w-10">
            <AddEventDropdownForTasks
              key={row.row.original.id}
              task={row.row.original as TaskWithEvents}
              className="hidden group-hover:block"
              setTask={(task: TaskWithEvents) => {
                // Use mutateTasks
                mutateTasks((data: any) => {
                  // Edit the Task with the same task id
                  data.tasks = data.tasks.map(
                    (existingTask: TaskWithEvents) => {
                      if (existingTask.id === task.id) {
                        return task;
                      }
                      return existingTask;
                    },
                  );
                  return data;
                });
              }}
              setSheetOpen={setSheetOpen}
              setSheetToOpen={setSheetToOpen}
            />
          </div>
        </div>
      ),
    },
    // Language
    {
      header: ({ column }) => {
        return (
          <div className="flex items-center">
            <Sparkles className="h-4 w-4 mr-1 text-green-500" />
            Language
          </div>
        );
      },
      accessorKey: "language",
      cell: (row) => (
        <HoverCard openDelay={80} closeDelay={30}>
          <HoverCardTrigger>
            <Badge variant={"secondary"}>{row.getValue() as string}</Badge>
          </HoverCardTrigger>
          <HoverCardContent side="top" className="text-sm text-center">
            {getLanguageLabel(row.getValue() as string)}
          </HoverCardContent>
        </HoverCard>
      ),
      maxSize: 10,
    },
    // Sentiment Analysis
    {
      header: ({ column }) => {
        return (
          <div className="flex justify-between items-center space-x-2">
            <div className="flex flex-row items-center">
              <Sparkles className="h-4 w-4 mr-1 text-green-500" />
              Sentiment
            </div>
            <SentimentSettings />
          </div>
        );
      },
      accessorKey: "sentiment.label",
      cell: (row) => {
        const sentiment_label = row.getValue() as string;
        return (
          <div>
            <HoverCard openDelay={80} closeDelay={30}>
              <HoverCardTrigger>
                <Badge
                  className={
                    sentiment_label == "positive"
                      ? "border-green-500"
                      : sentiment_label == "negative"
                        ? "border-red-500"
                        : ""
                  }
                  variant={"secondary"}
                >
                  {sentiment_label}
                </Badge>
              </HoverCardTrigger>
              <HoverCardContent side="top" className="text-sm text-left w-50">
                <h2 className="font-bold">Sentiment label</h2>
                <p>Automatic sentiment analysis of the Task input</p>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      maxSize: 10,
    },
    {
      header: "Input",
      accessorKey: "input",
      cell: (row) => {
        const input = row.getValue() as string; // asserting the type as string
        return (
          <Popover>
            <PopoverTrigger
              onClick={(mouseEvent) => {
                mouseEvent.stopPropagation();
              }}
              className="text-left"
            >
              {input
                ? input.length > 80
                  ? input.substring(0, 80) + "..."
                  : input
                : "-"}
            </PopoverTrigger>
            <PopoverContent className="text-sm">{input}</PopoverContent>
          </Popover>
        );
      },
      minSize: 100,
    },
    {
      header: "Output",
      accessorKey: "output",
      cell: (row) => {
        const output = row.getValue() as string; // asserting the type as string
        return (
          <Popover>
            <PopoverTrigger
              onClick={(mouseEvent) => {
                mouseEvent.stopPropagation();
              }}
              className="text-left"
            >
              {output
                ? output.length > 80
                  ? output.substring(0, 80) + "..."
                  : output
                : "-"}
            </PopoverTrigger>
            <PopoverContent className="text-sm">{output}</PopoverContent>
          </Popover>
        );
      },
      minSize: 100,
    },
    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const task = row.original;
        // Match the task object with this key
        // Handle undefined edge case
        if (!task) return <></>;
        return (
          <Link href={`/org/transcripts/tasks/${encodeURIComponent(task.id)}`}>
            <Button variant="ghost" size="icon">
              <ChevronRight />
            </Button>
          </Link>
        );
      },
      size: 10,
      minSize: 10,
      maxSize: 10,
    },
  ];
  return columns;
}
