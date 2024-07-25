import { Button } from "@/components/ui/button";
import { CardHeader } from "@/components/ui/card";
import Icons from "@/components/ui/icons";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import { useState } from "react";

const CreateNewABTestButton = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const handleIdEdit = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setABButtonClicked(false);
  };

  const handleButtonClick = () => {
    setABButtonClicked(true);
    // Call the API to create
    const updateSettings = async () => {
      await fetch(`/api/projects/${project_id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          settings: {
            ab_version_id: currentId,
          },
        }),
      }).then(() => {
        toast({
          title: "Settings updated",
          description: "Your next logs will be updated with the new version id",
        });
      });
    };
    updateSettings();
    // Reset the button
    setABButtonClicked(false);
  };

  const [date, setDate] = useState(new Date());
  const [currentId, setCurrentId] = useState(date.toLocaleString() ?? "");
  const [aBButtonClicked, setABButtonClicked] = useState(false);

  return (
    <>
      <Popover>
        <PopoverTrigger>
          <Button>Create New AB Test</Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-96 h-120">
          <CardHeader>
            <div>
              <Textarea
                id="description"
                placeholder={`Create a custom ID for your next AB test.`}
                value={currentId}
                onChange={handleIdEdit}
              />
            </div>
            {aBButtonClicked ? (
              <Icons.spinner className="mr-1 h-4 w-4 animate-spin" />
            ) : (
              <Button
                className="hover:bg-green-600"
                onClick={handleButtonClick}
              >
                Start new AB test
              </Button>
            )}
          </CardHeader>
        </PopoverContent>
      </Popover>
    </>
  );
};

export default CreateNewABTestButton;
