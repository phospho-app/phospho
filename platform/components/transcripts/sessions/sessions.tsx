"use client";

import SessionsDataviz from "@/components/transcripts/sessions/SessionDataviz";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

import { SessionsTable } from "./SessionsTable";

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

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      {!hasSessions && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                  Group tasks into sessions
                </CardTitle>
                <CardDescription className="text-muted-foreground">
                  Group your tasks into sessions by adding a{" "}
                  <code>session_id</code> when logging.
                </CardDescription>
              </div>
              <Link
                href="https://docs.phospho.ai/guides/sessions-and-users#sessions"
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
