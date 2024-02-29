"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePathname, useRouter } from "next/navigation";

const Insights = ({ children }: { children: React.ReactNode }) => {
  const router = useRouter();
  const pathName = usePathname();
  const currentTab = pathName.split("/")[3];
  return (
    <div className="w-full h-full flex flex-col space-y-4 md:flex">
      <Tabs defaultValue={currentTab} value={currentTab}>
        <TabsList>
          <TabsTrigger
            value="tasks"
            onClick={() => {
              router.push("/org/transcripts/tasks");
            }}
          >
            Tasks
          </TabsTrigger>
          <TabsTrigger
            value="sessions"
            onClick={() => {
              router.push("/org/transcripts/sessions");
            }}
          >
            Sessions
          </TabsTrigger>
          <TabsTrigger
            value="dashboard"
            onClick={() => {
              router.push("/org/transcripts/dashboard");
            }}
          >
            Dashboard
          </TabsTrigger>
        </TabsList>
      </Tabs>
      <div className="pb-10 space-y-4">{children}</div>
    </div>
  );
};

export default Insights;
