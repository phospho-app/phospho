"use client";

// Comp
import SessionsDataviz from "@/components/transcripts/sessions/session-dataviz";
// Models
import { SessionWithEvents } from "@/models/sessions";
import { dataStateStore, navigationStateStore } from "@/store/store";
import Link from "next/link";
import React, { useEffect } from "react";

// PropelAuth
import { Button } from "../../ui/button";
import { Card, CardContent, CardHeader } from "../../ui/card";
import { SessionsTable } from "./sessions-table";

const Sessions: React.FC = () => {
  const selectedProject = navigationStateStore(
    (state) => state.selectedProject,
  );
  const setUniqueEventNamesInData = dataStateStore(
    (state) => state.setUniqueEventNamesInData,
  );
  const sessionsWithEvents = dataStateStore(
    (state) => state.sessionsWithEvents,
  );

  const project_id = selectedProject?.id;

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
      <div className="hidden h-full flex-1 flex-col space-y-8 p-2 md:flex mx-2">
        <div>
          {!hasSessions && (
            <Card className="mb-4">
              <CardHeader className="text-2xl font-bold tracking-tight">
                Let's get serious.
              </CardHeader>
              <CardContent>
                <p className="text-gray-500">
                  Sessions group continuous user activity in your app. Discover
                  the story that bounds your users' journey.
                </p>
                <div className="flex flex-col justify-center items-center m-2">
                  <Link
                    href="https://docs.phospho.ai/guides/sessions-and-users#sessions"
                    target="_blank"
                  >
                    <Button variant="default">
                      Setup session tracking in your app
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="container px-0 space-y-2">
            <SessionsDataviz />
            <SessionsTable project_id={project_id} />
          </div>

          <div className="h-20"></div>
        </div>
      </div>
    </>
  );
};

export default Sessions;
