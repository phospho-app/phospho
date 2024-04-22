"use client";

import { DatePickerWithRange } from "@/components/date-range";
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
import { SessionWithEvents } from "@/models/models";
import { navigationStateStore } from "@/store/store";
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
  Database,
  FilterX,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import useSWR from "swr";

import { getColumns } from "./sessions-table-columns";

interface DataTableProps<TData, TValue> {
  userFilter?: string | null;
}

export function SessionsTable<TData, TValue>({
  userFilter = null,
}: DataTableProps<TData, TValue>) {
  const project_id = navigationStateStore((state) => state.project_id);

  const sessionsSorting = navigationStateStore(
    (state) => state.sessionsSorting,
  );
  const setSessionsSorting = navigationStateStore(
    (state) => state.setSessionsSorting,
  );
  const sessionsColumnsFilters = navigationStateStore(
    (state) => state.sessionsColumnsFilters,
  );
  const setSessionsColumnsFilters = navigationStateStore(
    (state) => state.setSessionsColumnsFilters,
  );
  const sessionPagination = navigationStateStore(
    (state) => state.sessionsPagination,
  );
  const setSessionsPagination = navigationStateStore(
    (state) => state.setSessionsPagination,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState("");
  const { accessToken } = useUser();
  const router = useRouter();

  let sessionsWithEvents: SessionWithEvents[] = [];

  // Filtering
  let eventFilter: string[] | null = null;
  if (sessionsColumnsFilters.length > 0) {
    console.log("tasksColumnsFilters", sessionsColumnsFilters);
    for (let filter of sessionsColumnsFilters) {
      if (filter.id === "events") {
        if (typeof filter?.value === "string") {
          eventFilter = [filter.value];
        } else {
          eventFilter = null;
        }
      }
    }
  }
  console.log("Event filter:", eventFilter);
  const { data: sessionsData } = useSWR(
    project_id
      ? [
          `/api/projects/${project_id}/sessions`,
          accessToken,
          sessionPagination.pageIndex,
          JSON.stringify(eventFilter),
          JSON.stringify(userFilter),
          JSON.stringify(dateRange),
          JSON.stringify(sessionsSorting),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        filters: {
          event_name: eventFilter,
          user_id: userFilter,
          created_at_start: dateRange?.created_at_start,
          created_at_end: dateRange?.created_at_end,
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
        sessions_filter: {
          event_name: eventFilter,
        },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbSessions = totalNbSessionsData?.total_nb_sessions;

  const query_tasks = async () => {
    // Call the /search endpoint
    setIsLoading(true);
    const response = await fetch(
      `/api/projects/${project_id}/search/sessions`,
      {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken || "",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
        }),
      },
    );
    const response_json = await response.json();
    console.log("Search response:", response_json);
    sessionsColumnsFilters.push({
      id: "id",
      value: response_json.session_ids,
    });
    table.setColumnFilters(sessionsColumnsFilters);
    setIsLoading(false);
  };

  const columns = getColumns();

  const table = useReactTable({
    data: sessionsWithEvents,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSessionsSorting,
    // getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setSessionsColumnsFilters,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setSessionsPagination,
    state: {
      columnFilters: sessionsColumnsFilters,
      sorting: sessionsSorting,
      pagination: sessionPagination,
    },
    pageCount: totalNbSessions
      ? Math.ceil(totalNbSessions / sessionPagination.pageSize)
      : 0,
    autoResetPageIndex: false,
    manualPagination: true,
    manualSorting: true,
  });

  if (!project_id) {
    return <></>;
  }

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
              setQuery(event.target.value);
              if (event.target.value === "") {
                // Remove the filter
                table.setColumnFilters(
                  sessionsColumnsFilters.filter((filter) => filter.id !== "id"),
                );
              }
            }}
            className="max-w-sm"
          />
        </div>
        <Button onClick={query_tasks} variant="outline">
          <Sparkles className="h-4 w-4" />
          Search
        </Button>
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
        <Button
          variant="secondary"
          onClick={() => {
            table.setColumnFilters([]);
            setQuery("");
            eventFilter = null;
          }}
          disabled={sessionsColumnsFilters.length === 0}
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
