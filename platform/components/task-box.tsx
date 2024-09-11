"use client";

import ThumbsUpAndDown from "@/components/thumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { getLanguageLabel } from "@/lib/utils";
import { Task, TaskWithEvents } from "@/models/models";
import React from "react";
import ReactMarkdown from "react-markdown";

import {
  AddEventDropdownForTasks,
  InteractiveEventBadgeForTasks,
} from "./label-events";

const TaskBox = ({
  task,
  setTask,
  setFlag,
}: {
  task: TaskWithEvents;
  setTask: (task: TaskWithEvents) => void;
  setFlag: (flag: string) => void;
}) => {
  return (
    <div className="flex flex-col space-y-1 p-1 border-2 border-secondary rounded-md mb-2">
      <div className="flex justify-between align-top">
        <div className="space-x-2 flex justify-between items-center">
          {task?.events?.map((event) => {
            return (
              <InteractiveEventBadgeForTasks
                key={event.event_name}
                event={event}
                task={task}
                setTask={setTask}
              />
            );
          })}
          <AddEventDropdownForTasks task={task} setTask={setTask} />
          {task?.language != null && (
            <Badge variant="outline">
              User language: {getLanguageLabel(task?.language)}
            </Badge>
          )}
          {task?.sentiment?.label != null && (
            <Badge variant="outline">Sentiment: {task?.sentiment?.label}</Badge>
          )}
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
      <div className="flex flex-col space-y-2">
        {task.metadata?.system_prompt && (
          <div className="flex justify-start">
            <div className="flex flex-col">
              <div className="text-muted-foreground ml-4 text-xs">
                System Prompt:
              </div>
              <div className="bg-primary text-secondary min-w-[200px] rounded-lg px-2 py-1 mx-2 whitespace-pre-wrap">
                <ReactMarkdown className="m-1">
                  {task.metadata.system_prompt}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        )}
        <div className="flex justify-start">
          <div className="flex flex-col">
            <div className="text-muted-foreground ml-4 text-xs">User:</div>
            <div className="bg-green-500 text-secondary min-w-[200px] rounded-lg px-2 py-1 mx-2 whitespace-pre-wrap">
              {task.input && (
                <ReactMarkdown className="m-1">{task.input}</ReactMarkdown>
              )}
            </div>
          </div>
        </div>
        {task.output && (
          <div className="flex justify-start">
            <div className="flex flex-col">
              <div className="text-muted-foreground ml-4 text-xs">
                Assistant:
              </div>
              <div className="bg-secondary min-w-[200px] rounded-lg px-2 py-1 mx-2 whitespace-pre-wrap">
                <ReactMarkdown className="m-1">{task.output}</ReactMarkdown>
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
              ([key1], [key2]) => {
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
              if (typeof value === "string" || typeof value === "number") {
                // If it's a string larger than 50 characters, display only the
                // first 50 characters
                const shortValue =
                  typeof value === "string" && value.length > 50
                    ? value.substring(0, 50) + "..."
                    : value;
                return (
                  <Badge
                    variant="outline"
                    className="mx-2 text-xs font-normal"
                    key={"button-" + key}
                  >
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
