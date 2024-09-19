"use client";

import { DatePickerWithRange } from "@/components/date-range";
import CreateEvent from "@/components/events/create-event";
import RunEvent from "@/components/events/run-event";
import FilterComponent from "@/components/filters";
import RunAnalysisInPast from "@/components/run-analysis-past";
import { SessionPreview } from "@/components/sessions/session-preview";
import { useColumns } from "@/components/sessions/sessions-table-columns";
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
  SessionWithEvents,
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
import React, { useState } from "react";
import useSWR, { KeyedMutator } from "swr";

interface DataTableProps {
  userFilter?: string | null;
  forcedDataFilters?: ProjectDataFilters;
}

function SessionsTable({
  userFilter = null,
  forcedDataFilters,
}: DataTableProps) {
  const project_id = navigationStateStore((state) => state.project_id);
  const sessionsSorting = navigationStateStore(
    (state) => state.sessionsSorting,
  );
  const setSessionsSorting = navigationStateStore(
    (state) => state.setSessionsSorting,
  );
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const dataFiltersMerged = {
    ...dataFilters,
    ...forcedDataFilters,
  };

  const sessionPagination = navigationStateStore(
    (state) => state.sessionsPagination,
  );
  const setSessionsPagination = navigationStateStore(
    (state) => state.setSessionsPagination,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

  const { accessToken } = useUser();

  const [, setTableIsClickable] = useState<boolean>(true);
  const [sheetOpen, setSheetOpen] = useState<boolean>(false);
  const [sheetToOpen, setSheetToOpen] = useState<string | null>(null);
  const [previewSessionId, setPreviewSessionId] = useState<string | null>(null);
  const [eventDefinition, setEventDefinition] =
    useState<EventDefinition | null>(null);

  const {
    data: sessionsWithEvents,
    mutate: mutateSessions,
  }: {
    data: SessionWithEvents[] | undefined;
    mutate: KeyedMutator<SessionWithEvents[]>;
  } = useSWR(
    project_id
      ? [
          `/api/projects/${project_id}/sessions`,
          accessToken,
          sessionPagination.pageIndex,
          JSON.stringify(dataFiltersMerged),
          JSON.stringify(sessionsSorting),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        filters: dataFiltersMerged,
        pagination: {
          page: sessionPagination.pageIndex,
          page_size: sessionPagination.pageSize,
        },
        sorting: sessionsSorting,
      }).then((res) => {
        if (res === undefined) return undefined;
        if (!res?.sessions) return [];
        return res.sessions;
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: totalNbSessionsData, isLoading: isTotalNbSessionsLoading } =
    useSWR(
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
          filters: dataFiltersMerged,
        }),
      {
        keepPreviousData: true,
      },
    );

  const totalNbSessions: number | null | undefined = isTotalNbSessionsLoading
    ? undefined
    : (totalNbSessionsData?.total_nb_sessions ?? null);

  const columns = useColumns({
    mutateSessions: mutateSessions,
    setSheetOpen: setSheetOpen,
    setSheetToOpen: setSheetToOpen,
    setEventDefinition: setEventDefinition,
  });

  const table = useReactTable({
    data: sessionsWithEvents ?? [],
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
        <div className="mb-2 flex flex-col items-start justify-between gap-y-2 md:flex-row md:items-center md:gap-y-0 md:gap-x-2">
          <div className="flex flex-col items-start gap-y-2 md:flex-row md:items-center md:gap-y-0 md:gap-x-2 ">
            <DatePickerWithRange nbrItems={totalNbSessions} />
            <FilterComponent variant="sessions" />
            <RunAnalysisInPast />
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
                      setSheetOpen(true);
                      setSheetToOpen("preview");
                      setPreviewSessionId(row.original.id);
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
          {sheetToOpen === "preview" && (
            <SessionPreview
              setOpen={setSheetOpen}
              session_id={previewSessionId}
            />
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

export { SessionsTable };
