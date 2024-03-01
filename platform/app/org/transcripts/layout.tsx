"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { usePathname } from "next/navigation";

const Insights = ({ children }: { children: React.ReactNode }) => {
  const pathName = usePathname();
  const currentTab = pathName.split("/")[3];
  return (
    <div className="w-full h-full flex flex-col space-y-4 md:flex">
      <Tabs defaultValue={currentTab} value={currentTab}>
        <TabsList>
          <Link href="/org/transcripts/tasks">
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
          </Link>
          <Link href="/org/transcripts/sessions">
            <TabsTrigger value="sessions">Sessions</TabsTrigger>
          </Link>
          <Link href="/org/transcripts/dashboard">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          </Link>
        </TabsList>
      </Tabs>
      <div className="pb-10 space-y-4">{children}</div>
    </div>
  );
};

export default Insights;
