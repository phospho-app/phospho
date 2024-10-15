"use client";

import { CenteredSpinner } from "@/components/small-spinner";
import { TableNavigation } from "@/components/table-navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useColumns } from "@/components/users/users-table-columns";
import { authFetcher } from "@/lib/fetcher";
import { ProjectDataFilters, UserMetadata } from "@/models/models";
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
import React, { useEffect, useState } from "react";
import useSWR from "swr";

import { UserPreview } from "./user-preview";

export function UsersTable({
  forcedDataFilters,
}: {
  forcedDataFilters?: ProjectDataFilters | null;
}) {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  // const dataFilters = navigationStateStore((state) => state.dataFilters);

  // Merge forcedDataFilters with dataFilters
  // const dataFiltersMerged = {
  //   ...dataFilters,
  //   ...forcedDataFilters,
  // };

  // Fetch all users
  const { data: usersMetadata }: { data: UserMetadata[] | null | undefined } =
    useSWR(
      project_id ? [`/api/projects/${project_id}/users`, accessToken] : null,
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          filters: {}, // TODO: Implement filters
        }).then(async (res) => {
          if (res === undefined) return undefined;
          if (!res?.users) return null;
          return res.users;
        }),
      {
        keepPreviousData: true,
      },
    );

  const [sorting, setSorting] = useState<SortingState>([]);
  const [filters, setFilters] = useState<ColumnFiltersState>([]);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [previewUserId, setPreviewUserId] = useState<string | undefined>();

  const columns = useColumns();
  const table = useReactTable({
    data: usersMetadata ?? [],
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

  useEffect(() => {
    /* Set default filters based on parsedDataFilters from the searchParams.
    Note: Only the event filters are implemented for users filtering. */
    if (forcedDataFilters?.event_name) {
      console.log("parsedDataFilters", forcedDataFilters);
      table.getColumn("events")?.setFilterValue(forcedDataFilters.event_name);
    }
  }, [forcedDataFilters, table]);

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

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        {usersMetadata === undefined && <CenteredSpinner />}
        {usersMetadata && (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                {usersMetadata &&
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
                {usersMetadata && table?.getRowModel()?.rows?.length ? (
                  table?.getRowModel()?.rows?.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.getIsSelected() && "selected"}
                      onClick={() => {
                        setSheetOpen(true);
                        setPreviewUserId(row.original.user_id);
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
        )}
        {table.getPageCount() > 1 && (
          <div className="flex justify-center mt-2">
            <TableNavigation table={table} />
          </div>
        )}
        <SheetContent className="md:w-1/2 overflow-auto">
          <UserPreview user_id={previewUserId} />
        </SheetContent>
      </Sheet>
    </div>
  );
}
