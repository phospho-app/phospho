"use client";

import { Button } from "@/components/ui/button";
import { authFetcher } from "@/lib/fetcher";
import { Test } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
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

  return (
    <>
      {(tests === null || tests === undefined || tests?.length == 0) && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Test your app before deploying
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  Run offline tests to measure the success rate of your app.
                </CardDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/integrations/python/testing"
                target="_blank"
              >
                <Button>Create test</Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}
      <DataTable />
    </>
  );
};

export default Tests;
