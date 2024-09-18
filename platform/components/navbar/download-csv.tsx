import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Download } from "lucide-react";
import React from "react";

import { DropdownMenuItem } from "../ui/dropdown-menu";

const ExportDataButton: React.FC = () => {
  // PropelAuth
  const project_id = navigationStateStore((state) => state.project_id);

  const { user, accessToken } = useUser();
  const { toast } = useToast();

  if (!user) {
    return <></>;
  }

  const handleButtonClick = async () => {
    try {
      const response = await fetch(`/api/projects/${project_id}/tasks/email`, {
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
    <DropdownMenuItem onClick={handleButtonClick}>
      <Download className="mr-1 h-4 w-4" />
      Export data
    </DropdownMenuItem>
  );
};

export { ExportDataButton };
