"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { UserMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import {
  ColumnFiltersState,
  SortingState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ChevronLeftIcon, ChevronRightIcon, FilterX } from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";

import { Button } from "../ui/button";
import { getColumns } from "./users-table-columns";

interface DataTableProps<TData, TValue> {
  usersMetadata: UserMetadata[];
}

export function UsersTable<TData, TValue>({
  usersMetadata,
}: DataTableProps<TData, TValue>) {
  const project_id = navigationStateStore((state) => state.project_id);

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const sessionsColumnsFilters = navigationStateStore(
    (state) => state.sessionsColumnsFilters,
  );
  const setSessionsColumnsFilters = navigationStateStore(
    (state) => state.setSessionsColumnsFilters,
  );
  const router = useRouter();

  const columns = getColumns();

  const table = useReactTable({
    data: usersMetadata,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setSessionsColumnsFilters,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      columnFilters: sessionsColumnsFilters,
      sorting,
    },
  });

  if (!project_id) {
    return <></>;
  }

  if (usersMetadata === undefined) {
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
          disabled={sessionsColumnsFilters.length === 0}
        >
          <FilterX className="h-4 w-4 mr-1" />
          Clear
        </Button>
        <div className="flex w-[100px] items-center justify-center text-sm font-medium">
          Page {table.getState().pagination.pageIndex + 1}/
          {table.getPageCount()}
        </div>
        <Button
          variant="outline"
          className="w-8 p-0"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <span className="sr-only">Go to previous page</span>
          <ChevronLeftIcon className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          className="w-8 p-0"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          <span className="sr-only">Go to next page</span>
          <ChevronRightIcon className="h-4 w-4" />
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
            {table !== null && table?.getRowModel()?.rows?.length ? (
              table?.getRowModel()?.rows?.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  onClick={() => {
                    router.push(
                      `/org/users/${encodeURIComponent(row.original.user_id)}`,
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
