"use client";

import { CenteredSpinner } from "@/components/small-spinner";
import { TableNavigation } from "@/components/table-navigation";
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
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  useReactTable,
} from "@tanstack/react-table";
import React, { useState } from "react";
import useSWR from "swr";

import FilterComponent from "../filters";
import { UserPreview } from "./user-preview";

export function UsersTable({
  forcedDataFilters,
}: {
  forcedDataFilters?: ProjectDataFilters | null;
}) {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const usersPagination = navigationStateStore(
    (state) => state.usersPagination,
  );
  const setUsersPagination = navigationStateStore(
    (state) => state.setUsersPagination,
  );
  const usersSorting = navigationStateStore((state) => state.usersSorting);
  const setUsersSorting = navigationStateStore(
    (state) => state.setUsersSorting,
  );

  // Merge forcedDataFilters with dataFilters
  const dataFiltersMerged = {
    ...dataFilters,
    ...forcedDataFilters,
  };

  const { data: usersCount }: { data: number | null | undefined } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/users`,
      accessToken,
      JSON.stringify(dataFiltersMerged),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["nb_users"],
        filters: dataFiltersMerged,
      }).then((data) => {
        if (data === undefined) return undefined;
        return data.nb_users;
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: usersMetadata }: { data: UserMetadata[] | null | undefined } =
    useSWR(
      project_id
        ? [
            `/api/projects/${project_id}/users`,
            accessToken,
            usersPagination.pageIndex,
            JSON.stringify(dataFiltersMerged),
            JSON.stringify(usersSorting),
          ]
        : null,
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          filters: dataFiltersMerged,
          sorting: usersSorting,
        }).then(async (res) => {
          if (res === undefined) return undefined;
          if (!res?.users) return null;
          return res.users;
        }),
      {
        keepPreviousData: true,
      },
    );

  const [sheetOpen, setSheetOpen] = useState(false);
  const [previewUserId, setPreviewUserId] = useState<string | undefined>();

  const maxNbPages = usersCount
    ? Math.ceil(usersCount / usersPagination.pageSize)
    : 1;

  const columns = useColumns();
  const table = useReactTable({
    data: usersMetadata ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setUsersSorting,
    // getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onPaginationChange: setUsersPagination,
    state: {
      sorting: usersSorting,
      // Note: the pagination is done client side. This is because computing the
      // users' metadata is slow : we need to crawl through all tasks to look for metadata.user_id
      // This can be fastened by creating a dedicated users table and using server side pagination.
      pagination: usersPagination,
    },
    pageCount: maxNbPages,
    autoResetPageIndex: false,
  });

  return (
    <div>
      <div className="flex flex-col gap-y-2 mb-2">
        <Input placeholder="Filter usernames" className="min-w-[20rem]" />
        <div className="flex flex-row gap-x-2 items-end justify-between">
          <FilterComponent variant="users" />
          <TableNavigation table={table} />
        </div>
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
