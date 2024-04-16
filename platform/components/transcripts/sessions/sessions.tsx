"use client";

import SessionsDataviz from "@/components/transcripts/sessions/session-dataviz";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SessionWithEvents } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import Link from "next/link";
import React, { useEffect } from "react";

import { SessionsTable } from "./sessions-table";

const Sessions: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const setUniqueEventNamesInData = dataStateStore(
    (state) => state.setUniqueEventNamesInData,
  );
  const sessionsWithEvents = dataStateStore(
    (state) => state.sessionsWithEvents,
  );
  const hasSessions = dataStateStore((state) => state.hasSessions);

  useEffect(() => {
    if (sessionsWithEvents !== null && sessionsWithEvents.length > 0) {
      const uniqueEventNames: string[] = Array.from(
        new Set(
          sessionsWithEvents
            .map((task: SessionWithEvents) => task.events)
            .flat()
            .map((event: any) => event.event_name as string),
        ),
      );
      setUniqueEventNamesInData(uniqueEventNames);
    }
  }, [project_id, sessionsWithEvents?.length]);

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      {!hasSessions && (
        <Card className="bg-secondary">
          <CardHeader>
            <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
              Group tasks into sessions
            </CardTitle>
            <CardDescription className="flex justify-between">
              <p className="text-gray-500">
                Add a session_id when logging tasks to group them into sessions.
              </p>
              <div className="flex flex-col justify-center items-center m-2">
                <Link
                  href="https://docs.phospho.ai/guides/sessions-and-users#sessions"
                  target="_blank"
                >
                  <Button variant="default">Setup session tracking</Button>
                </Link>
              </div>
            </CardDescription>
          </CardHeader>
        </Card>
      )}
      <div className="hidden h-full flex-1 flex-col space-y-8 p-2 md:flex mx-2">
        <div>
          <div className="container px-0 space-y-2">
            <SessionsDataviz />
            <SessionsTable />
          </div>

          <div className="h-20"></div>
        </div>
      </div>
    </>
  );
};

export default Sessions;
