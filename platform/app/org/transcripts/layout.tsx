"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import UpgradeButton from "@/components/upgrade-button";
import { dataStateStore } from "@/store/store";
import { Sparkles, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const HobbyPlanWarning = () => {
  return (
    <Card className="mb-4">
      <CardHeader className="text-2xl font-bold tracking-tight">
        <div className="flex items-center">
          <Sparkles className="h-8 w-8 text-green-500 mr-2" />
          You successfully logged tasks! Now, one last thing...
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex font-semibold  items-center">
          <X className="h-6 w-6 text-red-500" />
          Automatic evaluation and event detection are currently{" "}
          <div className=" ml-1">disabled.</div>
        </div>
        <div className="text-gray-500">
          To enable these features, please update your payment method.
        </div>
        <div className="flex flex-col justify-center items-center m-2">
          <UpgradeButton tagline="Complete setup" enlarge={false} />
        </div>
      </CardContent>
    </Card>
  );
};

const Insights = ({ children }: { children: React.ReactNode }) => {
  const pathName = usePathname();
  const currentTab = pathName.split("/")[3];

  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );
  const hasTasks = dataStateStore((state) => state.hasTasks);

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
      {selectedOrgMetadata?.plan === "hobby" && hasTasks && (
        <HobbyPlanWarning />
      )}
      <div className="pb-10 space-y-4">{children}</div>
    </div>
  );
};

export default Insights;
