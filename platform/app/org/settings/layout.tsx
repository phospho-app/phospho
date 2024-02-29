"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePathname, useRouter } from "next/navigation";

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const currentTab = pathname.split("/").pop();
  return (
    <>
      <div className="w-full h-full flex flex-col space-y-4 md:flex">
        <Tabs defaultValue={currentTab} value={currentTab}>
          <TabsList>
            <TabsTrigger
              value="project"
              onClick={() => {
                router.push("/org/settings/project");
              }}
            >
              Project
            </TabsTrigger>
            <TabsTrigger
              value="account"
              onClick={() => {
                router.push("/org/settings/account");
              }}
            >
              Account
            </TabsTrigger>
            <TabsTrigger
              value="billing"
              onClick={() => {
                router.push("/org/settings/billing");
              }}
            >
              Billing
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {children}
      </div>
    </>
  );
}
