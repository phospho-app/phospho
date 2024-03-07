"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const currentTab = pathname.split("/").pop();
  return (
    <>
      <div className="w-full h-full flex flex-col space-y-4 md:flex">
        <Tabs defaultValue={currentTab} value={currentTab}>
          <TabsList>
            <TabsTrigger value="project">
              <Link href="/org/settings/project">Project</Link>
            </TabsTrigger>

            <TabsTrigger value="account">
              <Link href="/org/settings/account">Account</Link>
            </TabsTrigger>
            <TabsTrigger value="billing">
              <Link href="/org/settings/billing">Billing</Link>
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {children}
      </div>
    </>
  );
}
