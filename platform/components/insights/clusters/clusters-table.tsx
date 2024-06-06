"use client";

import { TableNavigation } from "@/components/table-navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
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
import { Cluster, Clustering } from "@/models/models";
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
import { useRouter } from "next/navigation";
import React from "react";
import useSWR from "swr";

import { getColumns } from "./clusters-table-columns";

interface DataTableProps<TData, TValue> {
  clusterings?: Clustering[];
}

export function ClustersTable<TData, TValue>({
  clusterings = [],
}: DataTableProps<TData, TValue>) {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [filters, setFilters] = React.useState<ColumnFiltersState>([]);
  const router = useRouter();

  let latestClustering = undefined;
  if (clusterings.length > 0) {
    console.log("clusterings", clusterings);
    latestClustering = clusterings[0];
  }

  const [selectedClustering, setSelectedClustering] = React.useState<
    Clustering | undefined
  >(latestClustering);

  const {
    data: clustersData,
  }: {
    data: Cluster[] | null | undefined;
  } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/clusters`,
          accessToken,
          selectedClustering?.id,
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        clustering_id: selectedClustering?.id,
        limit: 100,
      }).then((res) =>
        res?.clusters.sort((a: Cluster, b: Cluster) => b.size - a.size),
      ),
    {
      keepPreviousData: true,
    },
  );

  const columns = getColumns();

  const table = useReactTable({
    data: clustersData ?? [],
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

  return (
    <div>
      <div className="flex flex-row gap-x-2 items-center mb-2 justify-between">
        <div>
          <Select
            onValueChange={(value: string) => {
              if (value === "no-clustering") {
                setSelectedClustering(undefined);
                return;
              }
              setSelectedClustering(
                clusterings.find((clustering) => clustering.id === value),
              );
            }}
            defaultValue={selectedClustering?.id ?? "no-clustering"}
          >
            <SelectTrigger>
              <div>
                {clusterings?.length > 0 && (
                  <span>
                    {formatUnixTimestampToLiteralDatetime(
                      selectedClustering?.created_at ??
                        latestClustering?.created_at ??
                        0,
                    )}
                  </span>
                )}
                {clusterings?.length === 0 && (
                  <span className="text-muted-foreground">
                    No clustering available
                  </span>
                )}
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {clusterings.map((clustering) => (
                  <SelectItem key={clustering.id} value={clustering.id}>
                    {formatUnixTimestampToLiteralDatetime(
                      clustering.created_at,
                    )}
                  </SelectItem>
                ))}
                {clusterings.length === 0 && (
                  <SelectItem value="no-clustering">
                    No clustering available
                  </SelectItem>
                )}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
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
                      `/org/insights/clusters/${encodeURIComponent(row.original.id)}`,
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
                  No cluster found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
