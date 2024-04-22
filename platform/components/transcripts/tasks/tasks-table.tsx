"use client";

import { DatePickerWithRange } from "@/components/date-range";
import DownloadButton from "@/components/download-csv";
import { TableNavigation } from "@/components/table-navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { Task, TaskWithEvents } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  ChevronFirstIcon,
  ChevronLastIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  FilterX,
} from "lucide-react";
import { Database, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import useSWR from "swr";

import { getColumns } from "./tasks-table-columns";

interface DataTableProps<TData, TValue> {
  // columns: any[]; // ColumnDef<TData, TValue>[];
}

export function TasksTable<TData, TValue>({}: DataTableProps<TData, TValue>) {
  const project_id = navigationStateStore((state) => state.project_id);

  const setTasksWithoutHumanLabel = dataStateStore(
    (state) => state.setTasksWithoutHumanLabel,
  );
  const router = useRouter();

  const tasksSorting = navigationStateStore((state) => state.tasksSorting);
  const setTasksSorting = navigationStateStore(
    (state) => state.setTasksSorting,
  );
  const tasksColumnsFilters = navigationStateStore(
    (state) => state.tasksColumnsFilters,
  );
  const setTasksColumnsFilters = navigationStateStore(
    (state) => state.setTasksColumnsFilters,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

  const [query, setQuery] = useState("");
  const { user, loading, accessToken } = useUser();
  const [isLoading, setIsLoading] = useState(false);

  const tasksPagination = navigationStateStore(
    (state) => state.tasksPagination,
  );
  const setTasksPagination = navigationStateStore(
    (state) => state.setTasksPagination,
  );

  let tasksWithEvents: TaskWithEvents[] = [];

  // Fetch all tasks
  let eventFilter: string[] | null = null;
  let flagFilter: string | null = null;
  if (tasksColumnsFilters.length > 0) {
    console.log("tasksColumnsFilters", tasksColumnsFilters);
    for (let filter of tasksColumnsFilters) {
      if (
        filter.id === "flag" &&
        (typeof filter?.value === "string" || filter?.value === null)
      ) {
        flagFilter = filter?.value;
      }
      if (filter.id === "events") {
        if (typeof filter?.value === "string") {
          eventFilter = [filter.value];
        } else {
          eventFilter = null;
        }
      }
    }
  }
  const { data: tasksData } = useSWR(
    project_id
      ? [
          `/api/projects/${project_id}/tasks`,
          accessToken,
          tasksPagination.pageIndex,
          JSON.stringify(eventFilter),
          JSON.stringify(flagFilter),
          JSON.stringify(dateRange),
          JSON.stringify(tasksSorting),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        filters: {
          event_name: eventFilter,
          flag: flagFilter,
          created_at_start: dateRange?.created_at_start,
          created_at_end: dateRange?.created_at_end,
        },
        pagination: {
          page: tasksPagination.pageIndex,
          page_size: tasksPagination.pageSize,
        },
        sorting: tasksSorting,
      }),
    { keepPreviousData: true },
  );
  if (
    project_id &&
    tasksData &&
    tasksData?.tasks !== undefined &&
    tasksData?.tasks !== null
  ) {
    tasksWithEvents = tasksData.tasks;
    setTasksWithoutHumanLabel(
      tasksData.tasks?.filter((task: Task) => {
        return task?.last_eval?.source !== "owner";
      }),
    );
  }

  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(eventFilter),
      JSON.stringify(flagFilter),
      JSON.stringify(dateRange),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        tasks_filter: {
          flag: flagFilter,
          event_name: eventFilter,
          created_at_start: dateRange?.created_at_start,
          created_at_end: dateRange?.created_at_end,
        },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;
  const maxNbPages = totalNbTasks
    ? Math.ceil(totalNbTasks / tasksPagination.pageSize)
    : -1;

  // console.log("taskscolumnsFilters", tasksColumnsFilters);

  const query_tasks = async () => {
    // Call the /search endpoint
    setIsLoading(true);
    const response = await fetch(`/api/projects/${project_id}/search/tasks`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken || "",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
      }),
    });
    const response_json = await response.json();
    console.log("Search response:", response_json);
    tasksColumnsFilters.push({
      id: "id",
      value: response_json.task_ids,
    });
    table.setColumnFilters(tasksColumnsFilters);
    setIsLoading(false);
  };

  const columns = getColumns();

  const table = useReactTable({
    data: tasksWithEvents,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setTasksSorting,
    // getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setTasksColumnsFilters,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setTasksPagination,
    state: {
      columnFilters: tasksColumnsFilters,
      sorting: tasksSorting,
      pagination: tasksPagination,
    },
    pageCount: maxNbPages,
    autoResetPageIndex: false,
    manualPagination: true,
  });

  if (!project_id) {
    return <></>;
  }

  console.log("Rendering tasks table", tasksWithEvents.length, table);

  return (
    <div>
      <div className="flex flex-row gap-x-2 items-center mb-2">
        <DatePickerWithRange />
        <div className="flex-grow">
          <Input
            placeholder="Search for a topic"
            value={
              // (table.getColumn("output")?.getFilterValue() as string) ?? ""
              query
            }
            onChange={(event) => {
              // table.getColumn("id")?.setFilterValue(event.target.value)
              // Reset the filters on id :

              setQuery(event.target.value);
              if (event.target.value === "") {
                // Remove the filters on id :
                table.setColumnFilters(
                  tasksColumnsFilters.filter((filter) => filter.id !== "id"),
                );
              }
            }}
            className="max-w-sm"
          />
        </div>
        <div>
          <Button
            onClick={async () => {
              table.setColumnFilters(
                tasksColumnsFilters.filter((filter) => filter.id !== "id"),
              );
              query_tasks();
            }}
            variant="outline"
          >
            <Sparkles className="h-4 w-4" />
            Search
          </Button>
        </div>
        {isLoading && (
          <svg
            className="animate-spin ml-1 h-5 w-5 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="black"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="black"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            ></path>
          </svg>
        )}
        <DownloadButton />
        <Button
          variant="secondary"
          onClick={() => {
            table.setColumnFilters([]);
            setQuery("");
            eventFilter = null;
            flagFilter = null;
          }}
          disabled={tasksColumnsFilters.length === 0}
        >
          <FilterX className="h-4 w-4 mr-1" />
          Clear filters
        </Button>
        <TableNavigation table={table} />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead
                      key={header.id}
                      colSpan={header.colSpan}
                      style={{
                        width: header.getSize(),
                      }}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table?.getRowModel()?.rows?.length ? (
              table?.getRowModel()?.rows.map((row) => (
                <TableRow
                  key={row.id}
                  // data-state={row.getIsSelected() && "selected"}
                  onClick={() => {
                    router.push(`/org/transcripts/tasks/${row.original.id}`);
                  }}
                  className="cursor-pointer"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No task found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      {table.getState().pagination.pageIndex + 1 > 5 && (
        <Alert className="mt-2 ">
          <div className="flex justify-between">
            <div></div>
            <div className="flex space-x-4">
              <Database className="w-8 h-8" />

              <div>
                <AlertTitle>Fetch tasks in a pandas Dataframe</AlertTitle>
                <AlertDescription>
                  <div>Load tasks with the phospho Python SDK</div>
                </AlertDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/integrations/python/analytics"
                target="_blank"
              >
                <Button>Learn more</Button>
              </Link>
            </div>
            <div></div>
          </div>
        </Alert>
      )}
    </div>
  );
}
