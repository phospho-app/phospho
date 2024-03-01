"use client";

import DownloadButton from "@/components/download-csv";
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
import { TaskWithEvents } from "@/models/tasks";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  ColumnFiltersState,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { FilterX } from "lucide-react";
import { Sparkles } from "lucide-react";
import React, { useState } from "react";

import { getColumns } from "./tasks-table-columns";

interface DataTableProps<TData, TValue> {
  // columns: any[]; // ColumnDef<TData, TValue>[];
  project_id: string;
}

export function TasksTable<TData, TValue>({
  project_id,
}: DataTableProps<TData, TValue>) {
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const tasksWithEvents = dataStateStore((state) => state.tasksWithEvents);

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const tasksColumnsFilters = navigationStateStore(
    (state) => state.tasksColumnsFilters,
  );
  const setTasksColumnsFilters = navigationStateStore(
    (state) => state.setTasksColumnsFilters,
  );

  const [query, setQuery] = useState("");
  const { user, loading, accessToken } = useUser();
  const [isLoading, setIsLoading] = useState(false);

  // console.log("taskscolumnsFilters", tasksColumnsFilters);

  const query_tasks = async () => {
    // Call the /search endpoint
    setIsLoading(true);
    const response = await fetch(
      `/api/projects/${selectedProject?.id}/search/tasks`,
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
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setTasksColumnsFilters,
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      columnFilters: tasksColumnsFilters,
      sorting,
    },
  });

  return (
    <div>
      <div className="flex flex-row gap-x-2">
        <div className="flex flex-col mb-2 flex-grow">
          <Input
            placeholder="Search for tasks about a topic"
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
        <div className="mr-4">
          <Button
            onClick={async () => {
              table.setColumnFilters(
                tasksColumnsFilters.filter((filter) => filter.id !== "id"),
              );
              query_tasks();
            }}
            variant="outline"
          >
            <Sparkles className="h-4 w-4 mr-1" />
            Search
          </Button>
        </div>
        {isLoading && (
          <svg
            className="animate-spin -ml-1 h-5 w-5 text-white"
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
          }}
        >
          <FilterX className="h-4 w-4 mr-1" />
          Clear all filters
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
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
                  data-state={row.getIsSelected() && "selected"}
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
    </div>
  );
}
