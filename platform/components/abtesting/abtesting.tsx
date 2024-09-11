"use client";

// Shadcn ui
import { Button } from "@/components/ui/button";
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
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

import { TableNavigation } from "../table-navigation";
import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { getColumns } from "./abtesting-columns";
import { ABTestingDataviz } from "./abtesting-dataviz";

interface DataTableProps<TData, TValue> {}

export function ABTesting<TData, TValue>({}: DataTableProps<TData, TValue>) {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const router = useRouter();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Fetch ABTests
  const { data: abTests } = useSWR(
    project_id ? [`/api/explore/${project_id}/ab-tests`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken)?.then((res) => {
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

  // We create a list of all the version IDs
  const versionIDs = abTests?.map((abtest) => abtest.version_id) ?? [];

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
      {abTests && (abTests?.length ?? 0) <= 1 && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Compare versions with AB Testing
                </CardTitle>
                <CardDescription>
                  <div className="text-muted-foreground">
                    When logging, add a <code>version_id</code> in{" "}
                    <code>metadata</code> to compare their analytics
                    distribution.
                  </div>
                </CardDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/guides/ab-test"
                target="_blank"
              >
                <Button>Setup AB Testing</Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}
      {abTests && abTests.length > 1 && (
        <h1 className="text-2xl font-bold">AB Testing</h1>
      )}
      <div className="pb-10">
        <ABTestingDataviz versionIDs={versionIDs} />
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

export default ABTesting;
