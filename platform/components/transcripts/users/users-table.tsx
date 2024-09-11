"use client";

import { TableNavigation } from "@/components/table-navigation";
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
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
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
import { FilterX } from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";

import { useColumns } from "./users-table-columns";

interface DataTableProps {}

export function UsersTable({}: DataTableProps) {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  // Fetch all users
  const { data: usersData } = useSWR(
    project_id ? [`/api/projects/${project_id}/users`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const usersMetadata = usersData?.users;

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [filters, setFilters] = React.useState<ColumnFiltersState>([]);

  const router = useRouter();

  const columns = useColumns();

  const table = useReactTable({
    data: usersMetadata,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setFilters,
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      columnFilters: filters,
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
      <div className="flex flex-row gap-x-2 items-center mb-2 justify-end">
        <Input
          placeholder="Filter usernames"
          value={(table.getColumn("user_id")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("user_id")?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
        <Button
          variant="secondary"
          onClick={() => {
            if (!table) return;
            table.setColumnFilters([]);
          }}
          disabled={filters?.length === 0}
        >
          <FilterX className="h-4 w-4 mr-1" />
          Clear
        </Button>
        <TableNavigation table={table} />
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
                      `/org/transcripts/users/${encodeURIComponent(row.original.user_id)}`,
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
