import { useToast } from "@/components/ui/use-toast";
import { navigationStateStore } from "@/store/store";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Download } from "lucide-react";
import React from "react";

interface DownloadButtonProps {}
const EmailTasksButton: React.FC<DownloadButtonProps> = () => {
  // PropelAuth
  const { user, loading, accessToken } = useUser();
  const { toast } = useToast();

  const project_id = navigationStateStore((state) => state.project_id);

  // if no user
  if (!user) {
    return;
  }

  const handleButtonClick = async () => {
    const authorization_header = "Bearer " + accessToken;
    try {
      const response = await fetch(`/api/projects/${project_id}/tasks/email`, {
        method: "GET",
        headers: {
          Authorization: authorization_header,
        },
      });

      const data = await response.json();
      if (data.error) {
        console.error("Error in fetching tasks:", data.error);
      } else {
        console.log("Sent email successfully:", data);
        toast({
          // Add a mail emoji
          title: "✉️ Your tasks are on the way!",
          description: `After processing, we'll send tasks to ${user.email}`,
        });
      }
    } catch (error) {
      console.error("Error in making the request:", error);
    }
  };

  return (
    <div onClick={handleButtonClick} className="flex flex-row items-center">
      <Download className="mr-2 h-6 w-6" />
      Export Data
    </div>
  );
};

export default EmailTasksButton;
