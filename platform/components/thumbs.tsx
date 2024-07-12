"use client";

// Models
import { Button } from "@/components/ui/button";
import Icons from "@/components/ui/icons";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { Task } from "@/models/models";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { PenSquare, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";

import { CardHeader } from "./ui/card";

interface ThumbsUpAndDownProps {
  task: Task;
  setTask: (task: Task) => void;
  flag: string | undefined;
  setFlag: (flag: string) => void;
  key: string;
}

// TODO : Make task and setTask a prop so that this component can be used in the SessionOverview component

const ThumbsUpAndDown: React.FC<ThumbsUpAndDownProps> = ({
  task,
  setTask,
  flag,
  setFlag,
  key,
}) => {
  // If no task, no thumbs
  if (task === null || task === undefined) return <></>;

  // PropelAuth
  const { user, loading, accessToken } = useUser();

  const [notes, setNotes] = useState(task.notes);
  const [currentNotes, setCurrentNotes] = useState(notes ?? "");
  const [saveNoteButtonClicked, setSaveNoteButtonClicked] = useState(false);

  const noteButtonColor =
    notes === null || notes === undefined || notes === ""
      ? "bg-secondary"
      : "bg-green-500";

  // Function to flag a task as succes or failure
  async function flagTask(flag: string) {
    if (user === null || user === undefined) return;
    if (task === null || task === undefined) return;

    const creation_response = await fetch(`/api/tasks/${task.id}/flag`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        flag: flag,
      }),
    });

    const responseBody = await creation_response.json();

    // If no task, don't update
    if (responseBody === null || responseBody === undefined) {
      console.log("Error: no task returned");
      return;
    }

    // Update the task in the state
    let updatedTask = task;
    updatedTask.flag = responseBody.flag;
    updatedTask.last_eval = responseBody.last_eval;
    setTask(updatedTask);
    setFlag(responseBody.flag);
    console.log("Task flagged");
  }

  // Function to update the note
  const handleNoteEdit = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCurrentNotes(event.target.value);
  };

  const handleSaveButton = async () => {
    console.log("Saving notes");
    if (user === null || user === undefined) return;
    if (task === null || task === undefined) return;
    setSaveNoteButtonClicked(true);

    // Create a project object in the database with the URL
    const creation_response = await fetch(`/api/tasks/${task.id}`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        notes: currentNotes,
      }),
    });
    const responseBody = await creation_response.json();

    console.log("responseBody :", responseBody);

    // If no task, don't update
    if (responseBody === null || responseBody === undefined) {
      console.log("Error: no task returned");
      setSaveNoteButtonClicked(false);
      return;
    }

    // Update the task in the state
    let updatedTask = task;
    updatedTask.notes = responseBody.notes;
    setTask(updatedTask);
    setNotes(responseBody.notes);
    setSaveNoteButtonClicked(false);
  };

  const successByUser = (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("failure")}
        className="bg-secondary mr-1"
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-green-400 mr-1"
      >
        <ThumbsUp className="h-4 w-4" fill="#4ade80" />
      </Button>
    </>
  );

  const failureByUser = (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("failure")}
        className="bg-red-500 mr-1"
      >
        <ThumbsDown className="h-4 w-4" fill="red" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>
    </>
  );

  const successByPhospho = (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("failure")}
        className="bg-secondary mr-1"
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="h-4 w-4" fill="#4ade80" />
      </Button>
    </>
  );

  const failureByPhospho = (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("failure")}
        className="bg-secondary mr-1"
      >
        <ThumbsDown className="h-4 w-4" fill="red" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>
    </>
  );

  const noEval = (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("failure")}
        className="bg-secondary mr-1"
      >
        <ThumbsDown className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="h-4 w-4" />
      </Button>
    </>
  );

  return (
    <div className="flex justify-end">
      {flag === "success" && !task.last_eval && successByPhospho}
      {flag === "failure" && !task.last_eval && failureByPhospho}
      {flag === "success" &&
        task.last_eval &&
        task.last_eval.source.startsWith("phospho") &&
        successByPhospho}
      {flag === "failure" &&
        task.last_eval &&
        task.last_eval.source.startsWith("phospho") &&
        failureByPhospho}
      {flag === "success" &&
        task.last_eval &&
        !task.last_eval.source.startsWith("phospho") &&
        successByUser}
      {flag === "failure" &&
        task.last_eval &&
        !task.last_eval.source.startsWith("phospho") &&
        failureByUser}
      {(flag === null || flag === "undefined") && noEval}

      <Popover key={key}>
        <PopoverTrigger>
          <Button
            variant="outline"
            size="icon"
            className={`mr-1 ${noteButtonColor}`}
          >
            <PenSquare className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-96 h-120">
          <CardHeader>
            <div>
              <Textarea
                id="description"
                placeholder={`Write a custom note for this task.\nWhen your users give you feedback, you see it here.`}
                value={currentNotes}
                onChange={handleNoteEdit}
              />
            </div>
            {saveNoteButtonClicked ? (
              <Icons.spinner className="mr-1 h-4 w-4 animate-spin" />
            ) : (
              <Button className="hover:bg-green-600" onClick={handleSaveButton}>
                Save
              </Button>
            )}
          </CardHeader>
        </PopoverContent>
      </Popover>
    </div>
  );
};

export default ThumbsUpAndDown;
