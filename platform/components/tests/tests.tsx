"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Test } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { DataTable } from "./tests-table";

const Tests: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  // Fetch tests
  const { data: testsData } = useSWR(
    project_id ? [`/api/projects/${project_id}/tests`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken),
    {
      keepPreviousData: true,
    },
  );
  const tests = testsData?.tests as Test[];

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
      {(tests === undefined || tests.length == 0) && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Test your app before deploying
                </CardTitle>
                <CardDescription>
                  <p className="text-gray-500">
                    Run offline tests to measure the success rate of your app.
                  </p>
                </CardDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/integrations/python/testing"
                target="_blank"
              >
                <Button>Run tests</Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}

      <DataTable columns={columns} data={tests} />
    </>
  );
};

export default Tests;
