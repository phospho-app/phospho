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
            value="events"
            onClick={() => {
              router.push("/org/insights/events");
            }}
          >
            Events
          </TabsTrigger>
          <TabsTrigger
            value="topics"
            onClick={() => {
              router.push("/org/insights/topics");
            }}
          >
            Topics
          </TabsTrigger>
          <TabsTrigger
            value="metadata"
            onClick={() => {
              router.push("/org/insights/metadata");
            }}
          >
            Metadata
          </TabsTrigger>
          <TabsTrigger
            value="kpis"
            onClick={() => {
              router.push("/org/insights/kpis");
            }}
          >
            KPIs
          </TabsTrigger>
        </TabsList>
      </Tabs>
      <div className="pb-10 space-y-4">{children}</div>
    </div>
  );
};

export default Insights;
