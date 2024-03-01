"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function EventsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const currentTab = pathname.split("/").pop();
  return (
    <>
      <div className="space-x-0.5 color-black">
        <Tabs defaultValue={currentTab} value={currentTab}>
          <TabsList>
            <Link href="/org/insights/events/explore">
              <TabsTrigger value="explore">Explore</TabsTrigger>
            </Link>
            <Link href="/org/insights/events/manage">
              <TabsTrigger value="manage">Manage</TabsTrigger>
            </Link>
          </TabsList>
        </Tabs>
      </div>

      <div className="w-full h-full flex-1 flex-col space-y-8 p-8 md:flex">
        {children}
      </div>
    </>
  );
}
