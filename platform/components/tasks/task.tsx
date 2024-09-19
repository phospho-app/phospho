"use client";

import { CenteredSpinner } from "@/components/small-spinner";
import TaskBox from "@/components/task-box";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Task, TaskWithEvents } from "@/models/models";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";
import useSWR from "swr";

interface TaskProps {
  task_id: string;
  showGoToTask?: boolean;
}

const TaskOverview: React.FC<TaskProps> = ({
  task_id,
  showGoToTask = false,
}) => {
  const { accessToken } = useUser();
  const [refresh, setRefresh] = useState(false);

  const { data: taskData, mutate: mutateTask } = useSWR(
    [`/api/tasks/${task_id}`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const task = taskData as TaskWithEvents;

  if (task === undefined) return <CenteredSpinner />;

  // To re-render the component when the flag is updated, we need to use a state
  // For the flag. This is because just having the task as a prop doesn't trigger
  // a re-render when the flag is updated (passage via reference)
  const setFlag = (flag: string) => {
    mutateTask({ ...task, flag: flag });
    setRefresh(!refresh);
  };

  return (
    <div className="flex flex-col space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-bold tracking-tight">
            <div className="flex justify-between">
              Message
              <div className="flex flex-row space-x-2">
                {showGoToTask && (
                  <Link href={`/org/transcripts/tasks/${task_id}`}>
                    <Button variant="secondary">
                      Go to Message
                      <ChevronRight />
                    </Button>
                  </Link>
                )}
                {task.session_id && (
                  <Link href={`/org/transcripts/sessions/${task.session_id}`}>
                    <Button variant="secondary">Go to Session</Button>
                  </Link>
                )}
              </div>
            </div>
          </CardTitle>
          <CardDescription>
            <ul>
              <li>
                <span className="font-bold">Task ID:</span> {task.id}
              </li>
              <li>
                <span className="font-bold">Created at:</span>{" "}
                {formatUnixTimestampToLiteralDatetime(task.created_at)}
              </li>
              <li>
                <span className="font-bold">Last eval source:</span>{" "}
                {task?.last_eval?.source ?? "None"}
              </li>
              <li>
                <span className="font-bold">Last eval date:</span>{" "}
                {task?.last_eval?.created_at
                  ? formatUnixTimestampToLiteralDatetime(
                      task?.last_eval?.created_at,
                    )
                  : "Never"}
              </li>
              <li>
                <span className="font-bold">Message position:</span>{" "}
                {task.task_position}
              </li>
              <li>
                <span className="font-bold">Is last message:</span>{" "}
                {task.is_last_task ? "Yes" : "No"}
              </li>
            </ul>
          </CardDescription>
        </CardHeader>
      </Card>
      <TaskBox
        task={task}
        setTask={(task: Task | null) => {
          mutateTask(task as TaskWithEvents);
        }}
        setFlag={setFlag}
      />
    </div>
  );
};

export default TaskOverview;
export { TaskOverview };
