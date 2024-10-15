"use client";

import SuggestEvent from "@/components/events/suggest-event";
import {
  AddEventDropdownForSessions,
  InteractiveEventBadgeForSessions,
} from "@/components/label-events";
import { Spinner } from "@/components/small-spinner";
import TaskBox from "@/components/task-box";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Event, SessionWithEvents, TaskWithEvents } from "@/models/models";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, CopyIcon } from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";
import useSWR from "swr";
import { useSWRConfig } from "swr";

import { InteractiveDatetime } from "../interactive-datetime";

const SessionStats = ({
  session_id,
  showGoToSession = false,
}: {
  session_id: string;
  showGoToSession?: boolean;
}) => {
  const { accessToken } = useUser();
  const { mutate } = useSWRConfig();

  const {
    data: sessionData,
    mutate: mutateSessionData,
  }: {
    data: SessionWithEvents | undefined;
    mutate: (data: SessionWithEvents | undefined) => void;
  } = useSWR(
    [`/api/sessions/${session_id}`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      revalidateIfStale: false,
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      keepPreviousData: true,
    },
  );

  const uniqueEvents = sessionData?.events?.filter(
    (event: Event, index: number, self: Event[]) =>
      index === self.findIndex((e: Event) => e.event_name === event.event_name),
  );

  return (
    <>
      <div className="flex justify-between items-center">
        <span className="text-xl font-bold tracking-tight">Session</span>
        {showGoToSession && (
          <Link href={`/org/transcripts/sessions/${session_id}`}>
            <Button variant="secondary">
              Go to Session
              <ChevronRight />
            </Button>
          </Link>
        )}
      </div>
      <Card className="flex flex-col space-y-1 p-2">
        <div className="flex flex-row items-center">
          <code className="bg-secondary p-1.5 text-xs">{session_id}</code>
          <Button
            variant="outline"
            className="m-1.5"
            size="icon"
            onClick={() => {
              navigator.clipboard.writeText(session_id);
            }}
          >
            <CopyIcon className="w-3 h-3" />
          </Button>
        </div>
        <div className="text-xs w-48">
          Created at:
          <InteractiveDatetime timestamp={sessionData?.created_at} />
        </div>
        <div className="flex">
          <div className="gap-x-0.5 gap-y-0.5 flex flex-wrap items-center">
            {uniqueEvents &&
              sessionData &&
              uniqueEvents?.map((event: Event) => (
                <InteractiveEventBadgeForSessions
                  key={event.id}
                  event={event}
                  session={sessionData}
                  setSession={(session: SessionWithEvents) => {
                    mutateSessionData(session);
                    // Fetch the session list
                    mutate((key: string[]) =>
                      key.includes(
                        `/api/projects/${sessionData.project_id}/sessions`,
                      ),
                    );
                  }}
                />
              ))}
            {sessionData && (
              <AddEventDropdownForSessions
                session={sessionData}
                setSession={(session: SessionWithEvents) => {
                  mutateSessionData(session);
                  // Fetch the session list
                  mutate((key: string[]) =>
                    key.includes(
                      `/api/projects/${sessionData.project_id}/sessions`,
                    ),
                  );
                }}
              />
            )}
            <SuggestEvent sessionId={session_id} />
          </div>
        </div>
        <div className="gap-x-0.5 gap-y-0.5 flex flex-wrap">
          {sessionData?.metadata &&
            Object.entries(sessionData.metadata)
              .sort(([key1], [key2]) => {
                if (key1 < key2) return -1;
                if (key1 > key2) return 1;
                return 0;
              })
              .map(([key, value]) => {
                if (typeof value === "string" || typeof value === "number") {
                  const shortValue =
                    typeof value === "string" && value.length > 50
                      ? value.substring(0, 50) + "..."
                      : value;
                  return (
                    <Badge
                      variant="outline"
                      className="text-xs font-normal"
                      key={key}
                    >
                      <div>
                        {key}: {shortValue}
                      </div>
                    </Badge>
                  );
                }
                return null;
              })}
        </div>
        <Collapsible>
          <CollapsibleTrigger asChild>
            <Button variant="link">{">"}Raw Session Data</Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <pre className="whitespace-pre-wrap mx-2 bg-secondary p-2 text-xs">
              {JSON.stringify(sessionData, null, 2)}
            </pre>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </>
  );
};

const SessionTranscript = ({ session_id }: { session_id: string }) => {
  const { accessToken } = useUser();
  const [refresh, setRefresh] = useState(false);

  const {
    data: sessionTasksData,
    mutate: mutateSessionTasks,
  }: {
    data: TaskWithEvents[] | undefined;
    mutate: (
      data: TaskWithEvents[] | undefined,
      shouldRevalidate?: boolean,
    ) => void;
  } = useSWR(
    [`/api/sessions/${session_id}/tasks`, accessToken],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "GET").then((res) => {
        if (res === undefined) return undefined;
        const tasks = res.tasks as TaskWithEvents[];
        // If responsse_json tasks are not null, sort them
        if (tasks !== undefined && tasks !== null && tasks.length > 0) {
          // Sort the tasks by increasing created_at
          tasks.sort((a: { created_at: number }, b: { created_at: number }) => {
            return a.created_at - b.created_at;
          });
          return tasks;
        }
        return [];
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      <div className="text-xl font-bold ">Transcript</div>
      {sessionTasksData === undefined && <Spinner />}
      {sessionTasksData?.map((task: TaskWithEvents, index) => (
        <TaskBox
          key={index}
          task={task}
          setTask={(task: TaskWithEvents) => {
            // use mutate session task to change the task with the same id
            const newTasks = sessionTasksData?.map((t) => {
              if (t.id === task.id) {
                return task;
              }
              return t;
            });
            mutateSessionTasks(newTasks, false);
          }}
          setFlag={(flag: string) => {
            const newTasks = sessionTasksData?.map((t) => {
              if (t.id === task.id) {
                t.flag = flag;
              }
              return t;
            });
            mutateSessionTasks(newTasks, false);
            setRefresh(!refresh);
          }}
        />
      ))}
    </>
  );
};
const SessionOverview = ({ session_id }: { session_id: string }) => {
  return (
    <div className="flex flex-col space-y-4 mt-4">
      <SessionStats session_id={session_id} />
      <SessionTranscript session_id={session_id} />
    </div>
  );
};

export { SessionOverview, SessionStats, SessionTranscript };
