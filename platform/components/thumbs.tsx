"use client";

// Models
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { Task } from "@/models/models";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { PenSquare, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";
import { useEffect } from "react";

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
  const { user, accessToken } = useUser();
  const [notes, setNotes] = useState("");
  const [currentNotes, setCurrentNotes] = useState("");
  const [, setSaveNoteButtonClicked] = useState(false);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (task?.notes) {
      setNotes(task.notes);
      setCurrentNotes(task.notes);
    }
  }, [task]);

  const noteButtonColor = notes ? "bg-green-500" : "bg-secondary";

  const flagTask = async (newFlag: string) => {
    if (!user || !task || !accessToken) return;

    try {
      const response = await fetch(`/api/tasks/${task.id}/human-eval`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ human_eval: newFlag }),
      });

      if (!response.ok) throw new Error("Failed to flag task");

      const responseBody = await response.json();
      setTask({
        ...task,
        flag: responseBody.flag,
        last_eval: responseBody.last_eval,
      });
      setFlag(responseBody.flag);
    } catch (error) {
      console.error("Error flagging task:", error);
      toast({
        title: "Error",
        description: "Failed to flag the task",
      });
    }
  };

  const handleNoteEdit = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCurrentNotes(event.target.value);
  };

  const handleSaveButton = async () => {
    if (!user || !task || !accessToken) return;
    setSaveNoteButtonClicked(true);
    setPopoverOpen(false);

    try {
      const response = await fetch(`/api/tasks/${task.id}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ notes: currentNotes }),
      });

      if (!response.ok) throw new Error("Failed to save notes");

      const responseBody = await response.json();
      setTask({ ...task, notes: responseBody.notes });
      setNotes(responseBody.notes);
      toast({
        title: "Notes saved",
        description: "Your notes have been saved",
      });
    } catch (error) {
      console.error("Error saving notes:", error);
      toast({
        title: "Error",
        description: "An error occurred while saving your notes",
      });
    } finally {
      setSaveNoteButtonClicked(false);
    }
  };

  if (!task) return null;

  const successByUser = (
    <>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("failure")}
        className="bg-secondary mr-1"
      >
        <ThumbsDown className="size-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-green-400 mr-1"
      >
        <ThumbsUp className="size-4" fill="#4ade80" />
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
        <ThumbsDown className="size-4" fill="red" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="size-4" />
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
        <ThumbsDown className="size-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="size-4" fill="#4ade80" />
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
        <ThumbsDown className="size-4" fill="red" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="size-4" />
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
        <ThumbsDown className="size-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        onClick={() => flagTask("success")}
        className="bg-secondary mr-1"
      >
        <ThumbsUp className="size-4" />
      </Button>
    </>
  );

  return (
    <Popover key={key} open={popoverOpen} onOpenChange={setPopoverOpen}>
      <div className="flex justify-end align-top">
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

        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className={`mr-1 ${noteButtonColor}`}
          >
            <PenSquare className="size-4" />
          </Button>
        </PopoverTrigger>
      </div>
      <PopoverContent align="end" className="w-96 h-120">
        <CardHeader>
          <Textarea
            id="description"
            placeholder={`Write a custom note for this message.\nWhen your users give you feedback, you see it here.`}
            value={currentNotes}
            onChange={handleNoteEdit}
          />
          <Button className="hover:bg-green-600" onClick={handleSaveButton}>
            Save
          </Button>
        </CardHeader>
      </PopoverContent>
    </Popover>
  );
};

export default ThumbsUpAndDown;
