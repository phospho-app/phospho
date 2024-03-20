import { Button } from "@/components/ui/button";
import { navigationStateStore } from "@/store/store";
// PropelAuth
import { useUser } from "@propelauth/nextjs/client";
import { Download } from "lucide-react";
import React, { useState } from "react";

interface DownloadButtonProps {}
const EmailTasksButton: React.FC<DownloadButtonProps> = () => {
  // PropelAuth
  const { user, loading, accessToken } = useUser();

  const [isSent, setIsSent] = useState(false);
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
        setIsSent(true); // Set isSent to true after successful operation
      }
    } catch (error) {
      console.error("Error in making the request:", error);
    }
  };

  return (
    <Button variant="secondary" onClick={handleButtonClick} disabled={isSent}>
      {/* <Mail className="mr-2 h-4 w-4" /> */}
      <Download className="mr-1 h-4 w-4" />
      {isSent ? `Data sent to ${user.email}!` : "Export"}
    </Button>
  );
};

export default EmailTasksButton;
