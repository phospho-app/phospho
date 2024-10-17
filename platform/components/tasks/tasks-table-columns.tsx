import { InteractiveDatetime } from "@/components/interactive-datetime";
import {
  AddEventDropdownForTasks,
  InteractiveEventBadgeForTasks,
} from "@/components/label-events";
import { RunEventsSettings } from "@/components/settings/events-settings";
import { SentimentSettings } from "@/components/settings/sentiment-settings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { getLanguageLabel } from "@/lib/utils";
import {
  Event,
  EventDefinition,
  Project,
  TaskWithEvents,
} from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ChevronRight,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import React from "react";
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
  mutateTasks: KeyedMutator<TaskWithEvents[]>;
}) {
  if (!accessToken) return;
  if (!project_id) return;

  await fetch(`/api/tasks/${task_id}/human-eval`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + accessToken,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      human_eval: flag,
    }),
  });
  mutateTasks((data: TaskWithEvents[] | undefined) => {
    if (!data) return data;
    // Edit the Task with the same task id
    data = data.map((task: TaskWithEvents) => {
      if (task.id === task_id) {
        task.flag = flag;
      }
      return task;
    });
    return data;
  });
}

export function useColumns({
  mutateTasks,
  setSheetOpen,
  setSheetToOpen,
  setEventDefinition,
}: {
  mutateTasks: KeyedMutator<TaskWithEvents[]>;
  setSheetOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setSheetToOpen: React.Dispatch<React.SetStateAction<string | null>>;
  setEventDefinition: React.Dispatch<
    React.SetStateAction<EventDefinition | null>
  >;
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

  const columns: ColumnDef<TaskWithEvents>[] = [
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
      cell: ({ row }) => {
        const value = row.original.created_at;
        return <InteractiveDatetime timestamp={value} />;
      },
    },
    // Input
    {
      header: "User message",
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
            <PopoverContent className="text-sm overflow-y-auto max-h-[20rem]">
              {input}
            </PopoverContent>
          </Popover>
        );
      },
    },
    {
      header: "Assistant response",
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
            <PopoverContent className="text-sm overflow-y-auto max-h-[20rem]">
              {output}
            </PopoverContent>
          </Popover>
        );
      },
    },
    // Human evaluation
    {
      header: "Human evaluation",
      accessorKey: "human_eval.flag",
      cell: (row) => {
        const human_eval = row.getValue() as string; // asserting the type as string
        return (
          <div className="flex justify-center group">
            {human_eval && human_eval == "success" && (
              <ThumbsUp className="h-6 w-6 text-green-500" />
            )}{" "}
            {human_eval && human_eval == "failure" && (
              <ThumbsDown className="h-6 w-6 text-red-500" />
            )}{" "}
            {!human_eval && (
              <div className="flex space-x-2 invisible group group-hover:visible p-6">
                <ThumbsUp
                  className="h-6 w-6 text-green-500 cursor-pointer hover:fill-green-500"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    flagTask({
                      task_id: row.row.original.id,
                      flag: "success",
                      accessToken: accessToken,
                      project_id: project_id,
                      mutateTasks: mutateTasks,
                    });
                  }}
                />
                <ThumbsDown
                  className="h-6 w-6 text-red-500 cursor-pointer hover:fill-red-500"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    flagTask({
                      task_id: row.row.original.id,
                      flag: "failure",
                      accessToken: accessToken,
                      project_id: project_id,
                      mutateTasks: mutateTasks,
                    });
                  }}
                />
              </div>
            )}
          </div>
        );
      },
    },
    // Language
    {
      header: () => {
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
    },
    // Events
    {
      header: () => {
        return (
          <div className="flex items-center space-x-2 justify-between">
            <div className="flex flex-row items-center space-x-1">
              <Sparkles className="h-4 w-4 text-green-500" />
              <div>Events</div>
            </div>
            <RunEventsSettings
              eventArray={eventArray}
              setSheetOpen={setSheetOpen}
              setSheetToOpen={setSheetToOpen}
              setEventDefinition={setEventDefinition}
            />
          </div>
        );
      },
      accessorKey: "events",
      cell: (row) => (
        <div className="group flex items-center justify-between">
          <div className="flex flex-wrap items-center justify-center w-full">
            {(row.getValue() as Event[]).map((event: Event) => {
              return (
                <InteractiveEventBadgeForTasks
                  key={`${event.event_name}_task_${row.row.original.id}`}
                  event={event}
                  task={row.row.original as TaskWithEvents}
                  setTask={(task: TaskWithEvents) => {
                    // Use mutateTasks
                    mutateTasks((data: TaskWithEvents[] | undefined) => {
                      if (!data) return data;
                      data = data.map((exisingTask: TaskWithEvents) => {
                        if (exisingTask.id === task.id) {
                          return task;
                        }
                        return exisingTask;
                      });
                      return data;
                    });
                  }}
                />
              );
            })}
            <AddEventDropdownForTasks
              key={`add_event_task_${row.row.original.id}`}
              task={row.row.original as TaskWithEvents}
              setTask={(task: TaskWithEvents) => {
                mutateTasks((data: TaskWithEvents[] | undefined) => {
                  if (!data) return data;
                  data = data.map((exisingTask: TaskWithEvents) => {
                    if (exisingTask.id === task.id) {
                      return task;
                    }
                    return exisingTask;
                  });
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

    // Sentiment Analysis
    {
      header: () => {
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
                <span>Automatic sentiment analysis of the user message</span>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
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
          <Button variant="ghost" size="icon">
            <ChevronRight />
          </Button>
        );
      },
    },
  ];
  return columns;
}
