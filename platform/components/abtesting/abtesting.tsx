"use client";

import { getColumns } from "@/components/abtesting/abtesting-columns";
import { ABTestingDataviz } from "@/components/abtesting/abtesting-dataviz";
import { TableNavigation } from "@/components/table-navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { authFetcher } from "@/lib/fetcher";
import { ABTest } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

function ABTesting() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const router = useRouter();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Fetch ABTests
  const { data: abTests }: { data: ABTest[] | null | undefined } = useSWR(
    project_id ? [`/api/explore/${project_id}/ab-tests`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken).then((res) => {
        if (res === undefined) return undefined;
        if (!res.abtests) return null;
        const abtests = res.abtests as ABTest[];
        // Round the score and score_std to 2 decimal places
        abtests.forEach((abtest) => {
          abtest.score = Math.round(abtest.score * 10000) / 100;
          if (abtest.score_std) {
            abtest.score_std = Math.round(abtest?.score_std * 10000) / 100;
          }
        });
        return abtests;
      }),
    {
      keepPreviousData: true,
    },
  );

  const columns = getColumns();

  const table = useReactTable({
    data: abTests ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  if (!isClient) {
    return <></>;
  }

  return (
    <>
      {abTests && abTests.length > 1 && (
        <h1 className="text-2xl font-bold">AB Testing</h1>
      )}
      <div className="pb-10">
        <ABTestingDataviz />
        <div className="flex flex-row items-center mb-2 justify-end">
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
                        `/org/ab-testing/${encodeURIComponent(row.original.version_id)}`,
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
                    No AB test found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </>
  );
}

export { ABTesting };
