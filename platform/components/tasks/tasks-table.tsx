"use client";

import CreateEvent from "@/components/events/create-event";
import RunEvent from "@/components/events/run-event";
import FilterComponent from "@/components/filters";
import RunAnalysisInPast from "@/components/run-analysis-past";
import { CenteredSpinner } from "@/components/small-spinner";
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
import {
  EventDefinition,
  ProjectDataFilters,
  TaskWithEvents,
} from "@/models/models";
import { navigationStateStore } from "@/store/store";
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
import React, { useEffect, useState } from "react";
import useSWR, { KeyedMutator } from "swr";

import { TaskPreview } from "./task-preview";
import { useColumns } from "./tasks-table-columns";

interface DataTableProps {
  forcedDataFilters?: ProjectDataFilters | null;
}

function TasksTable({ forcedDataFilters }: DataTableProps) {
  const project_id = navigationStateStore((state) => state.project_id);
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

  const [sheetOpen, setSheetOpen] = useState<boolean>(false);
  const [sheetToOpen, setSheetToOpen] = useState<string | null>(null);
  const [eventDefinition, setEventDefinition] =
    useState<EventDefinition | null>(null);
  const [taskPreviewId, setTaskToPreviewId] = useState<string | null>(null);

  // Merge forcedDataFilters with dataFilters
  const dataFiltersMerged = {
    ...dataFilters,
    ...forcedDataFilters,
  };

  const {
    data: tasksWithEvents,
    mutate: mutateTasks,
  }: {
    data: TaskWithEvents[] | undefined;
    mutate: KeyedMutator<TaskWithEvents[]>;
  } = useSWR(
    project_id
      ? [
          `/api/projects/${project_id}/tasks`,
          accessToken,
          tasksPagination.pageIndex,
          JSON.stringify(dataFiltersMerged),
          JSON.stringify(tasksSorting),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        filters: dataFiltersMerged,
        pagination: {
          page: tasksPagination.pageIndex,
          page_size: tasksPagination.pageSize,
        },
        sorting: tasksSorting,
      }).then((res) => {
        if (res === undefined) return undefined;

        if (!res?.tasks) return [];

        return res.tasks;
      }),
    { keepPreviousData: true },
  );

  const { data: totalNbTasks }: { data: number | null } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(dataFiltersMerged),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: dataFiltersMerged,
      }).then((res) => {
        if (res === undefined) return undefined;
        if (!res?.total_nb_tasks) return null;
        return res?.total_nb_tasks;
      }),
    {
      keepPreviousData: true,
    },
  );

  const maxNbPages = totalNbTasks
    ? Math.ceil(totalNbTasks / tasksPagination.pageSize)
    : 1;

  useEffect(() => {
    // Reset to first page
    if (tasksPagination.pageIndex > maxNbPages) {
      setTasksPagination({
        ...tasksPagination,
        pageIndex: 0,
      });
    }
  }, [maxNbPages, setTasksPagination, tasksPagination]);

  const columns = useColumns({
    mutateTasks: mutateTasks,
    setSheetOpen: setSheetOpen,
    setSheetToOpen: setSheetToOpen,
    setEventDefinition: setEventDefinition,
  });

  const table = useReactTable({
    data: tasksWithEvents ?? [],
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
    <>
      <div className="flex flex-col items-start justify-between gap-y-2 md:flex-row md:items-end md:gap-y-0 md:gap-x-2">
        <div className="flex flex-col items-start gap-y-2 md:flex-row md:items-center md:gap-y-0 md:gap-x-2 ">
          <FilterComponent variant="tasks" />
          <RunAnalysisInPast />
        </div>
        <TableNavigation table={table} />
      </div>
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen} modal={false}>
        <SheetContent className="md:w-1/2 overflow-auto" overlay={false}>
          {sheetToOpen === "run" && eventDefinition !== null && (
            <RunEvent setOpen={setSheetOpen} eventToRun={eventDefinition} />
          )}
          {sheetToOpen === "edit" && <CreateEvent setOpen={setSheetOpen} />}
          {sheetToOpen === "preview" && <TaskPreview task_id={taskPreviewId} />}
        </SheetContent>
        {tasksWithEvents === undefined && <CenteredSpinner />}
        {tasksWithEvents && (
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
                      data-state={
                        row.original.id === taskPreviewId && "selected"
                      }
                      onClick={() => {
                        setTaskToPreviewId(row.original.id);
                        setSheetToOpen("preview");
                        setSheetOpen(true);
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
                      No messages found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        )}
        {maxNbPages > 1 && (
          <div className="flex justify-center mt-2">
            <TableNavigation table={table} />
          </div>
        )}
        {table.getState().pagination.pageIndex + 1 > 5 && (
          <Alert className="mt-2 ">
            <div className="flex justify-between">
              <div></div>
              <div className="flex space-x-4 ">
                <Database className="w-8 h-8" />
                <div>
                  <AlertTitle>Fetch data in a pandas Dataframe</AlertTitle>
                  <AlertDescription>
                    <div>Load data with the phospho Python SDK</div>
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
      </Sheet>
    </>
  );
}

export { TasksTable };
