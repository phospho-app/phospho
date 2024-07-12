"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Test } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  useReactTable,
} from "@tanstack/react-table";
import * as React from "react";
import useSWR from "swr";

interface DataTableProps<TData, TValue> {}

export function DataTable<TData, TValue>({}: DataTableProps<TData, TValue>) {
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    [],
  );

  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const { data: testsData } = useSWR(
    project_id ? [`/api/projects/${project_id}/tests`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken),
    {
      keepPreviousData: true,
    },
  );
  const tests = (testsData?.tests ?? []) as Test[];

  // Create the columns for the data table
  const getVariant = (status: string) => {
    switch (status) {
      case "started":
        return "secondary";
      case "completed":
        return "default";
      case "canceled":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const columns: ColumnDef<Test>[] = [
    {
      header: "Date",
      accessorKey: "created_at",
      cell: ({ row }) => (
        <div>
          {formatUnixTimestampToLiteralDatetime(
            Number(row.original.created_at),
          )}
        </div>
      ),
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (row) => (
        <Badge variant={getVariant(row.getValue() as string)}>
          {row.getValue() as string}
        </Badge>
      ),
    },
    {
      header: "Score",
      accessorKey: "summary",
      cell: ({ row }) => (
        <span>
          {row.original?.summary?.overall_score != null
            ? row.original.summary.overall_score.toFixed(2)
            : ""}
        </span>
      ),
    },
  ];

  const table = useReactTable({
    data: tests,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onColumnFiltersChange: setColumnFilters,
    getFilteredRowModel: getFilteredRowModel(),
    state: {
      columnFilters,
    },
  });

  return (
    <div>
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
              table?.getRowModel().rows.map((row) => (
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
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
