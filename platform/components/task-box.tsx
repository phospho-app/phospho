"use client";

import ThumbsUpAndDown from "@/components/thumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Event, Task, TaskWithEvents } from "@/models/models";
import React from "react";
import ReactMarkdown from "react-markdown";

import { AddEventDropdown, InteractiveEventBadge } from "./label-events";

const TaskBox = ({
  task,
  setTask,
  setFlag,
  refresh,
}: {
  task: TaskWithEvents;
  setTask: (task: TaskWithEvents) => void;
  setFlag: (flag: string) => void;
  refresh: boolean;
}) => {
  return (
    <div className="flex flex-col space-y-1 p-1 border-2 border-secondary rounded-md mb-2">
      <div className="flex justify-between align-top">
        <div className="space-x-2 flex justify-between items-center">
          {task?.events?.map((event) => {
            return (
              <InteractiveEventBadge
                key={event.event_name}
                event={event}
                task={task}
                setTask={setTask}
              />
            );
          })}
          <AddEventDropdown task={task} setTask={setTask} />
        </div>
        <ThumbsUpAndDown
          task={task}
          setTask={(task: Task | null) => {
            setTask(task as TaskWithEvents);
          }}
          flag={task.flag}
          setFlag={setFlag}
          key={task.id}
        />
      </div>
      <div className="flex flex-col space-y-0.5 ">
        <div className="flex justify-start">
          <div>
            <div className="text-muted-foreground ml-4 text-sm">User:</div>
            <div className="bg-secondary min-w-[200px] rounded-lg px-2 py-1 mx-2 whitespace-pre-wrap">
              {task.input && (
                <ReactMarkdown className="m-1">{task.input}</ReactMarkdown>
              )}
            </div>
          </div>
        </div>
        {task.output && (
          <div className="flex justify-start pt-1">
            <div className="flex flex-col">
              <div className="text-muted-foreground ml-4 text-sm">
                Assistant:
              </div>
              <div className="bg-green-500 text-secondary min-w-[200px] rounded-lg px-2 py-1 mx-2 whitespace-pre-wrap">
                {task.output && (
                  <ReactMarkdown className="m-1">{task.output}</ReactMarkdown>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      <Collapsible>
        <CollapsibleTrigger>
          <Button variant="link">{">"}Raw Task Data</Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <pre className="whitespace-pre-wrap mx-2">
            {JSON.stringify(task, null, 2)}
          </pre>
        </CollapsibleContent>
      </Collapsible>
      <div>
        {task.metadata &&
          Object.entries(task.metadata)
            .sort(
              // sort by alphabetic key
              ([key1, value1], [key2, value2]) => {
                if (key1 < key2) {
                  return -1;
                }
                if (key1 > key2) {
                  return 1;
                }
                return 0;
              },
            )
            .map(([key, value]) => {
              // console.log("key :", key);
              if (typeof value === "string" || typeof value === "number") {
                // If it's a string larger than 50 characters, display only the
                // first 50 characters
                const shortValue =
                  typeof value === "string" && value.length > 50
                    ? value.substring(0, 50) + "..."
                    : value;
                return (
                  <Badge variant="outline" className="mx-2 text-xs font-normal">
                    <p key={key}>
                      {key}: {shortValue}
                    </p>
                  </Badge>
                );
              }
            })}
      </div>
    </div>
  );
};

export default TaskBox;
export { TaskBox };
