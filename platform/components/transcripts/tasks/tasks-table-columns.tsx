import {
  AddEventDropdown,
  InteractiveEventBadge,
} from "@/components/label-events";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Event, TaskWithEvents } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Check,
  ChevronDown,
  ChevronRight,
  FilterX,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import useSWR, { KeyedMutator, useSWRConfig } from "swr";

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
}: {
  mutateTasks: KeyedMutator<any>;
}): ColumnDef<TaskWithEvents>[] {
  const project_id = navigationStateStore((state) => state.project_id);
  const tasksPagination = navigationStateStore(
    (state) => state.tasksPagination,
  );
  const setTasksPagination = navigationStateStore(
    (state) => state.setTasksPagination,
  );

  const { accessToken } = useUser();

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
    {
      filterFn: (row, id, filterValue) => {
        // if is in the filtervalue
        if (filterValue === null) return true;
        return filterValue.includes(row.original.id);
      },
      header: ({ column }) => {
        return <></>;
      },
      accessorKey: "id",
      cell: ({ row }) => {
        return <></>;
      },
      enableHiding: true,
    },
    // Date
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Date
            {
              // Show the sorting icon based on the current sorting state
              column.getIsSorted() === "desc" ? (
                <ArrowUp className="ml-2 h-4 w-4" />
              ) : (
                <ArrowDown className="ml-2 h-4 w-4" />
              )
            }
          </Button>
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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost">
                <Sparkles className="h-4 w-4 mr-1 text-green-500" />
                Eval
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem
                onClick={() => {
                  column.setFilterValue("success");
                  setTasksPagination({
                    ...tasksPagination,
                    pageIndex: 0,
                  });
                }}
              >
                Success
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  column.setFilterValue("failure");
                  setTasksPagination({
                    ...tasksPagination,
                    pageIndex: 0,
                  });
                }}
              >
                Failure
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  column.setFilterValue(null);
                  setTasksPagination({
                    ...tasksPagination,
                    pageIndex: 0,
                  });
                }}
              >
                <FilterX className="h-4 w-4 mr-1" />
                Clear filter
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
      accessorKey: "flag",
      cell: (row) => (
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Badge
              variant={
                (row.getValue() as string) === "success"
                  ? "secondary"
                  : (row.getValue() as string) === "failure"
                    ? "destructive"
                    : "secondary"
              }
              className="hover:border-green-500"
            >
              {row.getValue() as string}
            </Badge>
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
        </DropdownMenu>
      ),
    },
    // Events
    {
      filterFn: (row, id, filterValue) => {
        if (filterValue === null) return true;
        // If the filter value is not null, return whether
        // the filterValue is in [event.event_name] array
        return (row.original.events as Event[]).some(
          (event) => event.event_name === filterValue,
        );
      },
      header: ({ column }) => {
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                onClick={() =>
                  column.toggleSorting(column.getIsSorted() === "asc")
                }
              >
                <Sparkles className="h-4 w-4 mr-1 text-green-500" />
                Events
                <ChevronDown size={16} className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              {uniqueEventNamesInData.map((eventName) => (
                <DropdownMenuItem
                  key={eventName}
                  onClick={() => {
                    column.setFilterValue(eventName);
                    setTasksPagination({
                      ...tasksPagination,
                      pageIndex: 0,
                    });
                  }}
                >
                  {eventName}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                key="event_clear"
                onClick={() => {
                  column.setFilterValue(null);
                  setTasksPagination({
                    ...tasksPagination,
                    pageIndex: 0,
                  });
                }}
              >
                <FilterX className="h-4 w-4 mr-1" />
                Clear filter
              </DropdownMenuItem>
            </DropdownMenuContent>
            <DropdownMenu />
          </DropdownMenu>
        );
      },
      accessorKey: "events",
      cell: (row) => (
        <div className="group flex items-center justify-between space-x-2">
          <div className="flex flex-wrap space-x-2 space-y-1">
            {(row.getValue() as Event[]).map((event: Event) => {
              return (
                <>
                  <InteractiveEventBadge
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
                </>
              );
            })}
          </div>
          {/* <div className="flex-grow"></div> */}
          <div className="w-10">
            <AddEventDropdown
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
            />
          </div>
        </div>
      ),
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
                ? input.length > 50
                  ? input.substring(0, 50) + "..."
                  : input
                : "-"}
            </PopoverTrigger>
            <PopoverContent className="text-sm">{input}</PopoverContent>
          </Popover>
        );
      },
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
                ? output.length > 50
                  ? output.substring(0, 50) + "..."
                  : output
                : "-"}
            </PopoverTrigger>
            <PopoverContent className="text-sm">{output}</PopoverContent>
          </Popover>
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
