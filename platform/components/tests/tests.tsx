"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Test } from "@/models/tests";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import React from "react";

import { DataTable } from "./tests-table";

const Tests: React.FC = () => {
  const tests = dataStateStore((state) => state.tests);

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

  // Create the columns for the data table
  const columns: ColumnDef<Test>[] = [
    {
      header: "Date",
      accessorKey: "created_at",
      cell: ({ row }) => (
        <span>
          {formatUnixTimestampToLiteralDatetime(
            Number(row.original.created_at),
          )}
        </span>
      ),
    },
    {
      header: "Status",
      accessorKey: "status",
      cell: (row) => (
        <span>
          <Badge variant={getVariant(row.getValue() as string)}>
            {row.getValue() as string}
          </Badge>
        </span>
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

  return (
    <>
      <div className="hidden h-full flex-1 flex-col space-y-8 p-2 md:flex mx-2">
        {tests && tests.length > 0 ? (
          <div>
            <h2 className="text-3xl font-bold tracking-tight mb-6">Tests</h2>

            <div className="container py-10 px-0">
              <DataTable columns={columns} data={tests} />
            </div>
          </div>
        ) : (
          <></>
        )}
        {tests === undefined || tests.length == 0 ? (
          <div className="flex flex-col justify-center items-center h-full">
            <p className="text-gray-500 mb-4">No tests (yet?)</p>
            <Link
              href="https://docs.phospho.ai/integrations/python/testing"
              target="_blank"
            >
              <Button variant="outline">
                Learn how to run tests with Python
              </Button>
            </Link>
          </div>
        ) : (
          <></>
        )}
      </div>
    </>
  );
};

export default Tests;
