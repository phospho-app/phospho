"use client";

import { NoDataDashboard } from "@/components/dashboard/no-data-dashboard";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { TaskWithEvents } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { ThumbsDown, ThumbsUp } from "lucide-react";
import Link from "next/link";
import React, { useEffect } from "react";

import TasksDataviz from "./tasks-dataviz";
import { TasksTable } from "./tasks-table";

const Tasks: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const tasksWithEvents = dataStateStore((state) => state.tasksWithEvents);
  const setUniqueEventNamesInData = dataStateStore(
    (state) => state.setUniqueEventNamesInData,
  );

  const hasTasks = dataStateStore((state) => state.hasTasks);
  const hasLabelledTasks = dataStateStore((state) => state.hasLabelledTasks);
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  useEffect(() => {
    if (tasksWithEvents !== null && tasksWithEvents.length > 0) {
      const uniqueEventNames: string[] = Array.from(
        new Set(
          tasksWithEvents
            .map((task: TaskWithEvents) => task.events)
            .flat()
            .map((event: any) => event.event_name as string),
        ),
      );
      setUniqueEventNamesInData(uniqueEventNames);
    }
  }, [project_id, tasksWithEvents?.length]);

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <div className="hidden h-full flex-1 flex-col space-y-8 p-2 md:flex mx-2 relative">
        <div>
          {/* {hasTasks === false && (
            <Card className="mb-4">
              <CardHeader className="text-2xl font-bold tracking-tight">
                A bit empty in here...
              </CardHeader>
              <CardContent>
                <p className="text-gray-500">
                  Tasks are the key user interactions in your app. Get a bird's
                  eye view of your user's activity by logging tasks to phospho.
                </p>
                <div className="flex flex-col justify-center items-center m-2">
                  <Link
                    href="https://docs.phospho.ai/getting-started"
                    target="_blank"
                  >
                    <Button variant="default">
                      Setup task logging in your app
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )} */}
          {hasTasks === false && (
            <>
              <div className="absolute z-10 w-10/12 m-auto left-0 right-0 top-0 bottom-0">
                <NoDataDashboard />
              </div>
            </>
          )}
          <div
            className={
              hasTasks === true
                ? "container px-0 space-y-2"
                : "container px-0 space-y-2 blur-sm"
            }
          >
            <TasksDataviz />
            {hasTasks === true &&
              hasLabelledTasks !== null &&
              selectedOrgMetadata?.plan === "pro" &&
              hasLabelledTasks?.has_enough_labelled_tasks === false && (
                <Card className="bg-secondary">
                  <CardHeader>
                    <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                      <div className="flex flex-row place-items-center">
                        <span className="mr-2">
                          Label{" "}
                          {hasLabelledTasks.enough_labelled_tasks -
                            hasLabelledTasks.currently_labelled_tasks}{" "}
                          tasks to improve automatic task evaluation
                        </span>
                        <ThumbsDown size={24} /> <ThumbsUp size={24} />
                      </div>
                    </CardTitle>
                    <CardDescription className="flex justify-between">
                      <div className="flex-col text-gray-500 space-y-0.5">
                        <p>
                          Automatic evaluations are made with your labels. We
                          only found {hasLabelledTasks.currently_labelled_tasks}
                          /{hasLabelledTasks.enough_labelled_tasks} labels.
                        </p>
                        <p>
                          Go to a task to label it or automate the process with
                          the API.
                        </p>
                      </div>
                      <Link
                        href="https://docs.phospho.ai/guides/evaluation"
                        target="_blank"
                      >
                        <Button variant="default">Learn more</Button>
                      </Link>
                    </CardDescription>
                  </CardHeader>
                </Card>
              )}
            <TasksTable />
          </div>

          <div className="h-20"></div>
        </div>
      </div>
    </>
  );
};

export default Tasks;
