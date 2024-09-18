"use client";

import { CenteredSpinner } from "@/components/small-spinner";
import TaskBox from "@/components/task-box";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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

  // const flagTask = async (flag: string) => {
  //   if (user === null || user === undefined) return;
  //   if (task === null || task === undefined) return;

  //   // Create a project object in the database with the URL
  //   const creation_response = await fetch(`/api/tasks/${task.id}/human-eval`, {
  //     method: "POST",
  //     headers: {
  //       Authorization: "Bearer " + accessToken,
  //       "Content-Type": "application/json",
  //     },
  //     body: JSON.stringify({
  //       human_eval: flag,
  //     }),
  //   });
  //   const creation_response_json = await creation_response.json();
  //   mutateTask(creation_response_json);
  // };

  if (task === undefined) return <CenteredSpinner />;

  // To re-render the component when the flag is updated, we need to use a state
  // For the flag. This is because just having the task as a prop doesn't trigger
  // a re-render when the flag is updated (passage via reference)
  const setFlag = (flag: string) => {
    mutateTask({ ...task, flag: flag });
    setRefresh(!refresh);
  };

  // const goToNextTask = () => {
  //   // Remove the current task (if it's in the list)
  //   if (!tasksWithoutHumanLabel) return;

  //   const index = tasksWithoutHumanLabel.findIndex((t) => t.id === task.id);
  //   if (index !== -1) {
  //     tasksWithoutHumanLabel.splice(index, 1);
  //   }
  //   setTasksWithoutHumanLabel(tasksWithoutHumanLabel);

  //   // Fetch the next task without label
  //   if (tasksWithoutHumanLabel.length === 0) {
  //     return;
  //   }
  //   const nextUnlabeledTask = tasksWithoutHumanLabel[0];
  //   if (nextUnlabeledTask) {
  //     router.push(`/org/transcripts/tasks/${nextUnlabeledTask.id}`);
  //   }
  // };

  // const onDislikeShowNext = () => {
  //   // Flag the task as a failure
  //   flagTask("failure");
  //   goToNextTask();
  // };
  // const onLikeShowNext = () => {
  //   // Flag the task as a success
  //   flagTask("success");
  //   goToNextTask();
  // };

  return (
    <div className="flex flex-col space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-bold tracking-tight">
            <div className="flex justify-between">
              Messages
              <div className="flex flex-row space-x-2">
                {showGoToTask && (
                  <Link href={`/org/transcripts/tasks/${task_id}`}>
                    <Button variant="secondary">
                      Go to Messages
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
