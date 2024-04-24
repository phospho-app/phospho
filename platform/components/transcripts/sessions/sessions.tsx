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
import { dataStateStore, navigationStateStore } from "@/store/store";
import Link from "next/link";
import React from "react";

import { SessionsTable } from "./sessions-table";

const Sessions: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const hasSessions = dataStateStore((state) => state.hasSessions);

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
                <CardDescription>
                  <p className="text-gray-500">
                    Add a session_id when logging tasks to group them into
                    sessions.
                  </p>
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
      <div className="hidden h-full flex-1 flex-col space-y-2 md:flex ">
        <SessionsDataviz />
        <SessionsTable />
      </div>
    </>
  );
};

export default Sessions;
