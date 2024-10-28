"use client";

import { CopyButton } from "@/components/copy-button";
import SuggestEvent from "@/components/events/suggest-event";
import { InteractiveDatetime } from "@/components/interactive-datetime";
import {
  AddEventDropdownForSessions,
  InteractiveEventBadgeForSessions,
} from "@/components/label-events";
import { Spinner } from "@/components/small-spinner";
import TaskBox from "@/components/task-box";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { authFetcher } from "@/lib/fetcher";
import { Event, SessionWithEvents, TaskWithEvents } from "@/models/models";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronDown, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import useSWR from "swr";
import { useSWRConfig } from "swr";

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
  const {
    data: sessionTasksData,
  }: {
    data: TaskWithEvents[] | undefined;
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

  const uniqueEvents = sessionData?.events?.filter(
    (event: Event, index: number, self: Event[]) =>
      index === self.findIndex((e: Event) => e.event_name === event.event_name),
  );
  // Deduplicate the user ids in task.metadata.user_id if they exist
  const uniqueUsers = sessionTasksData
    ?.map((task) => task.metadata?.user_id)
    .filter((v, i, a) => a.indexOf(v) === i);

  const router = useRouter();

  return (
    <>
      <div className="flex flex-wrap justify-between items-center mt-4 gap-4">
        <span className="text-xl font-bold">Session</span>
        <div className="flex flex-wrap gap-2">
          {showGoToSession && (
            <Link href={`/org/transcripts/sessions/${session_id}`}>
              <Button variant="secondary" className="whitespace-nowrap">
                Go to Session
                <ChevronRight className="ml-1" />
              </Button>
            </Link>
          )}
          {uniqueUsers && uniqueUsers.length === 1 && (
            <Link href={`/org/transcripts/users/${uniqueUsers[0]}`}>
              <Button variant="secondary" className="whitespace-nowrap">
                Go to User
                <ChevronRight className="ml-1" />
              </Button>
            </Link>
          )}
          {uniqueUsers && uniqueUsers?.length > 1 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="secondary" className="whitespace-nowrap">
                  Go to Users
                  <ChevronDown className="ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {uniqueUsers?.map((user_id) => (
                  <DropdownMenuItem
                    key={`${session_id}-${user_id}`}
                    onClick={() =>
                      router.push(`/org/transcripts/users/${user_id}`)
                    }
                  >
                    {user_id}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
      <Card className="p-2">
        <div className="flex flex-row gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <code className="bg-secondary p-1.5 text-xs break-all max-w-full">
              {session_id}
            </code>
            <CopyButton text={session_id} />
          </div>
        </div>
        <div className="flex flex-row gap-8">
          {sessionData?.last_message_ts && (
            <div className="text-xs max-w-[120px]">
              <span className="text-muted-foreground">Last message</span>
              <InteractiveDatetime timestamp={sessionData?.last_message_ts} />
            </div>
          )}
          <div className="text-xs max-w-[120px]">
            <span className="text-muted-foreground">First message</span>
            <InteractiveDatetime timestamp={sessionData?.created_at} />
          </div>
          <div className="flex flex-col">
            <span className="text-muted-foreground text-xs">Length</span>
            <div className="text-xl font-bold">
              {sessionData?.session_length}
            </div>
          </div>
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
