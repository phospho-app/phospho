"use client";

import SmallSpinner from "@/components/small-spinner";
import TaskBox from "@/components/task-box";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Task, TaskWithEvents } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

interface TaskProps {
  task_id: string;
}

const TaskOverview: React.FC<TaskProps> = ({ task_id }) => {
  const { user, loading, accessToken } = useUser();
  const [task, setTask] = useState<TaskWithEvents | null>(null);
  const [refresh, setRefresh] = useState(false);

  const router = useRouter();
  const tasksWithoutHumanLabel = dataStateStore(
    (state) => state.tasksWithoutHumanLabel,
  );
  const setTasksWithoutHumanLabel = dataStateStore(
    (state) => state.setTasksWithoutHumanLabel,
  );

  useEffect(() => {
    // Get Task
    (async () => {
      const headers = {
        Authorization: "Bearer " + accessToken || "",
        "Content-Type": "application/json",
      };
      const task_response = await fetch(`/api/tasks/${task_id}`, {
        method: "GET",
        headers: headers,
      });
      const task_response_json = await task_response.json();
      setTask(task_response_json);
    })();
  }, [task_id, loading]);

  const flagTask = async (flag: string) => {
    if (user === null || user === undefined) return;
    if (task === null || task === undefined) return;

    // Create a project object in the database with the URL
    const creation_response = await fetch(`/api/tasks/${task.id}/flag`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        flag: flag,
        source: "owner",
      }),
    });
    const creation_response_json = await creation_response.json();
    setTask(creation_response_json);
  };

  if (task === null || task === undefined) return <SmallSpinner />;

  // To re-render the component when the flag is updated, we need to use a state
  // For the flag. This is because just having the task as a prop doesn't trigger
  // a re-render when the flag is updated (passage via reference)
  const flag = task.flag;
  const setFlag = (flag: string) => {
    setTask({ ...task, flag: flag });
    setRefresh(!refresh);
  };

  const goToNextTask = () => {
    // Remove the current task (if it's in the list)
    if (!tasksWithoutHumanLabel) return;

    const index = tasksWithoutHumanLabel.findIndex((t) => t.id === task.id);
    if (index !== -1) {
      tasksWithoutHumanLabel.splice(index, 1);
    }
    setTasksWithoutHumanLabel(tasksWithoutHumanLabel);

    // Fetch the next task without label
    if (tasksWithoutHumanLabel.length === 0) {
      return;
    }
    const nextUnlabeledTask = tasksWithoutHumanLabel[0];
    if (nextUnlabeledTask) {
      router.push(`/org/transcripts/tasks/${nextUnlabeledTask.id}`);
    }
  };

  const onDislikeShowNext = () => {
    // Flag the task as a failure
    flagTask("failure");
    goToNextTask();
  };
  const onLikeShowNext = () => {
    // Flag the task as a success
    flagTask("success");
    goToNextTask();
  };

  return (
    <>
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-xl font-bold tracking-tight">
            <div className="flex justify-between">
              Task
              {task.session_id && (
                <Link href={`/org/transcripts/sessions/${task.session_id}`}>
                  <Button variant="secondary">Go to Session</Button>
                </Link>
              )}
            </div>
          </CardTitle>
          <CardDescription>
            <div>
              <div>
                <span className="font-bold">Task ID:</span> {task.id}
              </div>
              <div>
                <span className="font-bold">Created at:</span>{" "}
                {formatUnixTimestampToLiteralDatetime(task.created_at)}
              </div>
              <div>
                <span className="font-bold">Last eval source:</span>{" "}
                {task?.last_eval?.source ?? "None"}
              </div>
              <div>
                <span className="font-bold">Last eval date:</span>{" "}
                {task?.last_eval?.created_at
                  ? formatUnixTimestampToLiteralDatetime(
                      task?.last_eval?.created_at,
                    )
                  : "Never"}
              </div>
            </div>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <TaskBox
            task={task}
            setTask={(task: Task | null) => {
              setTask(task as TaskWithEvents);
            }}
            setFlag={setFlag}
            refresh={refresh}
          ></TaskBox>
        </CardContent>
        <CardFooter className="flex justify-around ">
          {tasksWithoutHumanLabel && tasksWithoutHumanLabel.length > 0 && (
            <div className="flex-col justify-items-center">
              <div className="text-gray-500 mb-1">
                Override evaluation and show next task
              </div>
              <div className="flex space-x-4 justify-center">
                <Button
                  variant="secondary"
                  onClick={onDislikeShowNext}
                  className="w-32"
                >
                  <ThumbsDown className="w-4 h-4 mr-2" />
                  Show next
                </Button>
                <Button
                  variant="secondary"
                  onClick={onLikeShowNext}
                  className="w-32"
                >
                  <ThumbsUp className="w-4 h-4 mr-2" />
                  Show next
                </Button>
              </div>
            </div>
          )}
          {tasksWithoutHumanLabel && tasksWithoutHumanLabel.length === 0 && (
            <div className="flex space-x-4 items-center text-gray-500">
              You labeled all the tasks! 🎉
            </div>
          )}
        </CardFooter>
      </Card>
    </>
  );
};

export default TaskOverview;
