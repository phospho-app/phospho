"use client";

import { InteractiveDatetime } from "@/components/interactive-datetime";
import { CenteredSpinner } from "@/components/small-spinner";
import TaskBox from "@/components/task-box";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { Task, TaskWithEvents } from "@/models/models";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, CopyIcon } from "lucide-react";
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
    <>
      <div className="flex justify-between items-center mt-4">
        <span className="text-xl font-bold">Message</span>
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
            <Link
              href={`/org/transcripts/sessions/${encodeURIComponent(task.session_id)}`}
            >
              <Button variant="secondary">Go to Session</Button>
            </Link>
          )}
          {task.metadata?.user_id && (
            <Link
              href={`/org/transcripts/users/${encodeURIComponent(task.metadata?.user_id)}`}
            >
              <Button variant="secondary">Go to User</Button>
            </Link>
          )}
        </div>
      </div>
      <Card className="flex flex-col sapce-y-1 p-2">
        <div className="flex flex-row items-center">
          <code className="bg-secondary p-1.5 text-xs">{task_id}</code>
          <Button
            variant="outline"
            className="m-1.5"
            size="icon"
            onClick={() => {
              navigator.clipboard.writeText(task_id);
            }}
          >
            <CopyIcon className="w-3 h-3" />
          </Button>
        </div>
        <div className="flex flex-row space-x-16">
          <div className="text-xs max-w-48">
            <span>Created at:</span>
            <InteractiveDatetime timestamp={task.created_at} />
          </div>
          {task.task_position && (
            <div className="flex flex-col">
              <div className="text-xl font-bold">#{task.task_position}</div>
              <span className="text-muted-foreground text-xs">position</span>
            </div>
          )}
          <div className="flex flex-col">
            <div className="text-xl font-bold">
              {task.is_last_task ? "Yes" : "No"}
            </div>
            <span className="text-muted-foreground text-xs">
              Is last message?
            </span>
          </div>
          {task?.last_eval?.source && (
            <div className="flex flex-col">
              <div className="text-xl font-bold">{task?.last_eval?.source}</div>
              <span className="text-muted-foreground text-xs">
                Last eval source
              </span>
            </div>
          )}
          {task?.last_eval?.created_at && (
            <div className="text-xs max-w-48">
              <span>Last eval date:</span>
              <InteractiveDatetime timestamp={task?.last_eval?.created_at} />
            </div>
          )}
        </div>
      </Card>
      <TaskBox
        task={task}
        setTask={(task: Task | null) => {
          mutateTask(task as TaskWithEvents);
        }}
        setFlag={setFlag}
      />
    </>
  );
};

export default TaskOverview;
export { TaskOverview };
