"use client";

import ThumbsUpAndDown from "@/components/thumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { getLanguageLabel } from "@/lib/utils";
import { Task, TaskWithEvents } from "@/models/models";
import Link from "next/link";
import React from "react";
import ReactMarkdown from "react-markdown";

import { InteractiveDatetime } from "./interactive-datetime";
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
    <Card className="flex flex-col space-y-2 rounded-md p-2">
      <div className="flex justify-between align-top">
        <div className="gap-x-0.5 gap-y-0.5 flex flex-wrap items-center">
          <InteractiveDatetime
            timestamp={task.created_at}
            className="text-xs mx-1"
          />
          {task?.language != null && (
            <Badge variant="outline">
              User language: {getLanguageLabel(task?.language)}
            </Badge>
          )}
          {task?.sentiment?.label != null && (
            <Badge variant="outline">Sentiment: {task?.sentiment?.label}</Badge>
          )}
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
                System Prompt
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
            <div className="text-muted-foreground ml-4 text-xs">
              {task.metadata?.user_id ? (
                <HoverCard>
                  <HoverCardTrigger asChild>
                    <Link
                      href={`/org/transcripts/users/${encodeURIComponent(task.metadata.user_id)}`}
                      className="underline cursor-pointer"
                    >
                      User
                    </Link>
                  </HoverCardTrigger>
                  <HoverCardContent>
                    See all messages from user
                  </HoverCardContent>
                </HoverCard>
              ) : (
                <>User</>
              )}
            </div>
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
                Assistant
              </div>
              <div className="bg-secondary min-w-[200px] rounded-lg px-2 py-1 mx-2 whitespace-pre-wrap">
                <ReactMarkdown className="m-1">{task.output}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
      <Collapsible>
        <CollapsibleTrigger asChild>
          <Button variant="link">{">"}Raw Task Data</Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <pre className="whitespace-pre-wrap mx-2 bg-secondary p-2 text-xs">
            {JSON.stringify(task, null, 2)}
          </pre>
        </CollapsibleContent>
      </Collapsible>
      <div className="flex flex-wrap gap-x-0.5 gap-y-0.5">
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
                    className="text-xs font-normal"
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
    </Card>
  );
};

export default TaskBox;
export { TaskBox };
