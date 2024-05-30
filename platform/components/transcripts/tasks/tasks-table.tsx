"use client";

import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import CreateEvent from "@/components/insights/events/create-event";
import RunEvent from "@/components/insights/events/run-event";
import { TableNavigation } from "@/components/table-navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { EventDefinition, Task, TaskWithEvents } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Database } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";

import { getColumns } from "./tasks-table-columns";

interface DataTableProps<TData, TValue> {
  // columns: any[]; // ColumnDef<TData, TValue>[];
  tasks_ids?: string[];
}

export function TasksTable<TData, TValue>({
  tasks_ids,
}: DataTableProps<TData, TValue>) {
  const project_id = navigationStateStore((state) => state.project_id);
  const setTasksWithoutHumanLabel = dataStateStore(
    (state) => state.setTasksWithoutHumanLabel,
  );
  const tasksSorting = navigationStateStore((state) => state.tasksSorting);
  const setTasksSorting = navigationStateStore(
    (state) => state.setTasksSorting,
  );
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const tasksPagination = navigationStateStore(
    (state) => state.tasksPagination,
  );
  const setTasksPagination = navigationStateStore(
    (state) => state.setTasksPagination,
  );
  const { accessToken } = useUser();
  const router = useRouter();
  const [sheetOpen, setSheetOpen] = React.useState<boolean>(false);
  const [sheetToOpen, setSheetToOpen] = React.useState<string | null>(null);
  const [eventDefinition, setEventDefinition] =
    React.useState<EventDefinition | null>(null);
  const [tableIsClickable, setTableIsClickable] = React.useState<boolean>(true);

  let tasksWithEvents: TaskWithEvents[] = [];

  console.log("TASKS DATA FILTERS", dataFilters);
  console.log("TASKS_IDS", tasks_ids);

  const { data: tasksData, mutate: mutateTasks } = useSWR(
    project_id
      ? [
          `/api/projects/${project_id}/tasks`,
          accessToken,
          tasksPagination.pageIndex,
          JSON.stringify(dataFilters),
          JSON.stringify(tasksSorting),
          JSON.stringify(tasks_ids),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        filters: {
          ...dataFilters,
          tasks_ids: tasks_ids,
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
      JSON.stringify(dataFilters),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: {
          ...dataFilters,
          tasks_ids: tasks_ids,
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
    : 1;

  const columns = getColumns({
    mutateTasks: mutateTasks,
    setSheetOpen,
    setSheetToOpen,
    setEventDefinition,
  });

  const table = useReactTable({
    data: tasksWithEvents,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setTasksSorting,
    // getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setTasksPagination,
    state: {
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

  return (
    <div>
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <div className="flex flex-row justify-between items-center mb-2 gap-x-2">
          <div className="flex flew-row  gap-x-2">
            <DatePickerWithRange />
            <FilterComponent variant="tasks" />
          </div>
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
                      router.push(
                        `/org/transcripts/tasks/${encodeURIComponent(row.original.id)}`,
                      );
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
                    No tasks found.
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
          {sheetToOpen === "run" && eventDefinition !== null && (
            <RunEvent setOpen={setSheetOpen} eventToRun={eventDefinition} />
          )}
          {sheetToOpen === "edit" && (
            <CreateEvent
              setOpen={setSheetOpen}
              // No event name to edit. This menas that it always creates a new event
              // eventNameToEdit={eventDefinition?.event_name}
            />
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
