import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Download } from "lucide-react";
import React from "react";

import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "../ui/hover-card";

const ExportUsersButton: React.FC = () => {
  // PropelAuth
  const project_id = navigationStateStore((state) => state.project_id);

  const { user, accessToken } = useUser();
  const { toast } = useToast();

  if (!user) {
    return <></>;
  }

  const handleButtonClick = async () => {
    try {
      const response = await fetch(`/api/projects/${project_id}/users/email`, {
        method: "GET",
        headers: {
          Authorization: "Bearer " + accessToken,
        },
      });

      const data = await response.json();
      if (data.error) {
        toast({
          title: "Error exporting data",
          description: data.error,
        });
      }
      if (data.exception_empty_data) {
        toast({
          title: "No users to export",
          description: "There are no users to export.",
        });
      } else {
        toast({
          // Add a mail emoji
          title: "✉️ Your data is on the way!",
          description: `After processing, we'll send the files to ${user.email}`,
        });
      }
    } catch (error) {
      toast({
        title: "Error exporting data",
        description: `${error}`,
      });
    }
  };

  return (
    <HoverCard openDelay={0} closeDelay={0}>
      <HoverCardTrigger asChild>
        <Button size="icon" variant="ghost" onClick={handleButtonClick}>
          <Download className="size-4" />
        </Button>
      </HoverCardTrigger>
      <HoverCardContent className="text-xs">Download as CSV</HoverCardContent>
    </HoverCard>
  );
};

export { ExportUsersButton };
