"use client";

import TaskBox from "@/components/task-box";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Event } from "@/models/events";
import { SessionWithEvents } from "@/models/sessions";
import { Task, TaskWithEvents } from "@/models/tasks";
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

const SessionOverview = ({ session_id }: { session_id: string }) => {
  const { accessToken } = useUser();
  let unique_events: Event[] = [];
  const [sessionTasks, setSessionTasks] = useState<TaskWithEvents[]>([]);

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
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "GET").then((response) => {
        // Set the unique events
        unique_events = response.events?.filter(
          (event: Event, index: number, self: Event[]) =>
            index ===
            self.findIndex((e: Event) => e.event_name === event.event_name),
        );
        return response;
      }),
    {
      revalidateIfStale: false,
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );
  const session_with_events = sessionData;

  const setTask = (task: Task) => {
    console.log("SET TASK", task);
    const updatedTasks = sessionTasks?.map((t: TaskWithEvents) => {
      if (t.id === task.id) {
        t.flag = task.flag;
        t.last_eval = task.last_eval;
        t.notes = task.notes;
      }
      return t;
    });
    // sessionTasks = updatedTasks;
    setSessionTasks(updatedTasks);
    // mutate(`/api/sessions/${session_id}/tasks`);
  };

  const setFlag = (flag: string) => {};

  if (session_with_events === null || session_with_events === undefined) {
    return <></>;
  }

  return (
    <div>
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl font-bold tracking-tight">
            Session Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p>
            <strong className="text-xl font-semibold">Events:</strong>{" "}
            {unique_events &&
              unique_events?.map((event: Event) => (
                <Badge className="mx-2">
                  <p key={event.id}>{event.event_name}</p>
                </Badge>
              ))}
          </p>
          <p className="mt-2 mb-2">
            <strong className="text-xl font-semibold">Created at:</strong>{" "}
            {formatUnixTimestampToLiteralDatetime(
              session_with_events.created_at,
            )}
          </p>
          <Collapsible>
            <CollapsibleTrigger>
              <Button variant="link">{">"} View Raw Session Data</Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <pre className="whitespace-pre-wrap mx-2">
                {JSON.stringify(session_with_events, null, 2)}
              </pre>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-3xl font-bold tracking-tight">
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
            ></TaskBox>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

export default SessionOverview;
