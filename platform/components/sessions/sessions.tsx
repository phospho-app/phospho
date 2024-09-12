"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import SessionsDataviz from "@/components/transcripts/sessions/session-dataviz";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

import { SessionsTable } from "./sessions-table";

const Sessions: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  // Fetch the has session
  const { data: hasSessionData } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/has-sessions`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasSessions: boolean = hasSessionData?.has_sessions;

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks;

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <SendDataCallout />
      {hasTasks && !hasSessions && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Group messages by session
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  Group messages into sessions by adding a{" "}
                  <code>session_id</code> when logging.
                </CardDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/analytics/sessions-and-users"
                target="_blank"
              >
                <Button variant="default">Setup session tracking</Button>
              </Link>
            </div>
          </CardHeader>
        </Card>
      )}
      <SessionsDataviz />
      <SessionsTable />
    </>
  );
};

export default Sessions;
