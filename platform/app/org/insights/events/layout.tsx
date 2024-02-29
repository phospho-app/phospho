"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePathname, useRouter } from "next/navigation";

export default function EventsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const currentTab = pathname.split("/").pop();
  return (
    <>
      <div className="space-x-0.5 color-black">
        <Tabs defaultValue={currentTab} value={currentTab}>
          <TabsList>
            <TabsTrigger
              value="explore"
              onClick={() => {
                router.push("/org/insights/events/explore");
              }}
            >
              Explore
            </TabsTrigger>
            <TabsTrigger
              value="manage"
              onClick={() => {
                router.push("/org/insights/events/manage");
              }}
            >
              Manage
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="w-full h-full flex-1 flex-col space-y-8 p-8 md:flex">
        {children}
      </div>
    </>
  );
}
