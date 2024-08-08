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
import { EventDefinition, SessionWithEvents } from "@/models/models";
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
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";

import { getColumns } from "./sessions-table-columns";

interface DataTableProps<TData, TValue> {
  userFilter?: string | null;
  sessions_ids?: string[];
}

export function SessionsTable<TData, TValue>({
  userFilter = null, sessions_ids,
}: DataTableProps<TData, TValue>) {
  const project_id = navigationStateStore((state) => state.project_id);

  const sessionsSorting = navigationStateStore(
    (state) => state.sessionsSorting,
  );
  const setSessionsSorting = navigationStateStore(
    (state) => state.setSessionsSorting,
  );
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const sessionPagination = navigationStateStore(
    (state) => state.sessionsPagination,
  );
  const setSessionsPagination = navigationStateStore(
    (state) => state.setSessionsPagination,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

  const { accessToken } = useUser();
  const router = useRouter();

  const [tableIsClickable, setTableIsClickable] = React.useState<boolean>(true);
  const [sheetOpen, setSheetOpen] = React.useState<boolean>(false);
  const [sheetToOpen, setSheetToOpen] = React.useState<string | null>(null);
  const [eventDefinition, setEventDefinition] =
    React.useState<EventDefinition | null>(null);

  let sessionsWithEvents: SessionWithEvents[] = [];

  const { data: sessionsData, mutate: mutateSessions } = useSWR(
    project_id
      ? [
        `/api/projects/${project_id}/sessions`,
        accessToken,
        sessionPagination.pageIndex,
        JSON.stringify(dataFilters),
        JSON.stringify(sessionsSorting),
        JSON.stringify(sessions_ids),
      ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        ilters: {
          ...dataFilters,
          tasks_ids: sessions_ids,
        },
        pagination: {
          page: sessionPagination.pageIndex,
          page_size: sessionPagination.pageSize,
        },
        sorting: sessionsSorting,
      }),
    {
      keepPreviousData: true,
    },
  );
  if (sessionsData?.sessions) {
    sessionsWithEvents = sessionsData.sessions;
  }

  const { data: totalNbSessionsData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/sessions`,
      accessToken,
      JSON.stringify(userFilter),
      JSON.stringify(dateRange),
      "total_nb_sessions",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_sessions"],
        filters: {
          ...dataFilters,
          sessions_ids: sessions_ids,
        },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbSessions = totalNbSessionsData?.total_nb_sessions;

  const columns = getColumns({
    mutateSessions: mutateSessions,
    setSheetOpen: setSheetOpen,
    setSheetToOpen: setSheetToOpen,
    setEventDefinition: setEventDefinition,
  });

  console.log("SESSIONS SORTING", sessionsSorting);
  const table = useReactTable({
    data: sessionsWithEvents,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSessionsSorting,
    // getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setSessionsPagination,
    state: {
      sorting: sessionsSorting,
      pagination: sessionPagination,
    },
    pageCount: totalNbSessions
      ? Math.ceil(totalNbSessions / sessionPagination.pageSize)
      : 1,
    autoResetPageIndex: false,
    manualPagination: true,
    manualSorting: true,
  });

  if (!project_id) {
    return <></>;
  }

  return (
    <div>
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <div className="flex flex-row justify-between gap-x-2 items-center mb-2">
          <div className="flex flex-row space-x-2 items-center">
            <DatePickerWithRange />
            <FilterComponent variant="sessions" />
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
                table?.getRowModel()?.rows?.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    onClick={() => {
                      router.push(
                        `/org/transcripts/sessions/${encodeURIComponent(row.original.id)}`,
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
                    No session found.
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
          {sheetToOpen === "edit" && <CreateEvent setOpen={setSheetOpen} />}
        </SheetContent>
      </Sheet>
    </div>
  );
}
