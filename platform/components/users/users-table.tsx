"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { dataStateStore, navigationStateStore } from "@/store/store";
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
import React from "react";

import { Button } from "../ui/button";
import { getColumns } from "./users-table-columns";

interface DataTableProps<TData, TValue> {
  project_id: string;
}

export function UsersTable<TData, TValue>({
  project_id,
}: DataTableProps<TData, TValue>) {
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const usersMetadata = dataStateStore((state) => state.usersMetadata);

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const sessionsColumnsFilters = navigationStateStore(
    (state) => state.sessionsColumnsFilters,
  );
  const setSessionsColumnsFilters = navigationStateStore(
    (state) => state.setSessionsColumnsFilters,
  );

  const columns = getColumns();

  const table = useReactTable({
    data: usersMetadata,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setSessionsColumnsFilters,
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      columnFilters: sessionsColumnsFilters,
      sorting,
    },
  });

  if (!selectedProject) {
    return <></>;
  }

  return (
    <div>
      <div className="flex flex-row gap-x-4 justify-end mb-2">
        <Button
          variant="secondary"
          onClick={() => {
            if (!table) return;
            table.setColumnFilters([]);
          }}
        >
          <FilterX className="h-4 w-4 mr-1" />
          Clear all filters
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table !== null &&
              table.getHeaderGroups().map((headerGroup) => (
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
            {table !== null && table?.getRowModel()?.rows?.length ? (
              table?.getRowModel()?.rows?.map((row) => (
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
                  No users found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
