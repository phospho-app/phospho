"use client";

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
import React, { useEffect, useState } from "react";
import useSWR from "swr";

const SessionOverview = ({ session_id }: { session_id: string }) => {
  const { accessToken } = useUser();
  const [sessionTasks, setSessionTasks] = useState<TaskWithEvents[]>([]);
  const [refresh, setRefresh] = useState(false);

  // Get the tasks from the API
  useEffect(() => {
    (async () => {
      const headers = {
        Authorization: "Bearer " + accessToken || "",
        "Content-Type": "application/json",
      };

      const task_response = await fetch(`/api/sessions/${session_id}/tasks`, {
        method: "GET",
        headers: headers,
      });
      const task_response_json = await task_response.json();
      // If responsse_json tasks are not null, sort them
      if (
        task_response_json?.tasks !== undefined &&
        task_response_json?.tasks !== null &&
        task_response_json.tasks.length > 0
      ) {
        // Sort the tasks by increasing created_at
        task_response_json.tasks.sort(
          (a: { created_at: number }, b: { created_at: number }) => {
            return a.created_at - b.created_at;
          },
        );
        setSessionTasks(task_response_json.tasks);
      }
    })();
  }, [session_id, accessToken]);

  const { data: sessionData }: { data: SessionWithEvents } = useSWR(
    [`/api/sessions/${session_id}`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      revalidateIfStale: false,
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      keepPreviousData: true,
    },
  );
  const session_with_events = sessionData;
  const uniqueEvents = session_with_events?.events?.filter(
    (event: Event, index: number, self: Event[]) =>
      index === self.findIndex((e: Event) => e.event_name === event.event_name),
  );

  const setTask = (task: TaskWithEvents) => {
    console.log("SET TASK", task);
    const updatedTasks = sessionTasks?.map((t: TaskWithEvents) => {
      if (t.id === task.id) {
        t.flag = task.flag;
        t.last_eval = task.last_eval;
        t.notes = task.notes;
        t.events = task.events;
      }
      return t;
    });
    // sessionTasks = updatedTasks;
    setSessionTasks(updatedTasks);
    // mutate(`/api/sessions/${session_id}/tasks`);
    setRefresh(!refresh);
  };

  const setFlag = (flag: string) => {};

  if (session_with_events === null || session_with_events === undefined) {
    return <></>;
  }

  return (
    <>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-xl font-bold tracking-tight">
            <div className="flex justify-between">Session</div>
          </CardTitle>
          <CardDescription>
            {uniqueEvents && (
              <div className="flex">
                <span className="font-bold mr-2">Events:</span>
                <div className="space-x-2">
                  {uniqueEvents?.map((event: Event) => (
                    <Badge variant="outline" key={event.id}>
                      {event.event_name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            <span className="font-bold">Created at:</span>{" "}
            {formatUnixTimestampToLiteralDatetime(
              session_with_events.created_at,
            )}
            <Collapsible>
              <CollapsibleTrigger>
                <Button variant="link">{">"}Raw Session Data</Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <pre className="whitespace-pre-wrap mx-2">
                  {JSON.stringify(session_with_events, null, 2)}
                </pre>
              </CollapsibleContent>
            </Collapsible>
          </CardDescription>
        </CardHeader>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-xl font-bold tracking-tight">
            Transcript
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sessionTasks?.map((task: TaskWithEvents, index) => (
            <TaskBox
              key={index}
              task={task}
              setTask={setTask}
              setFlag={setFlag}
              refresh={refresh}
            ></TaskBox>
          ))}
        </CardContent>
      </Card>
    </>
  );
};

export default SessionOverview;
