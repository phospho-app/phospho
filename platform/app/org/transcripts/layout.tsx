"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import UpgradeButton from "@/components/upgrade-button";
import { dataStateStore } from "@/store/store";
import { Sparkles, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const HobbyPlanWarning = () => {
  return (
    <Card className="bg-secondary">
      <CardHeader>
        <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
          <div className="flex items-center">
            Finish setup by adding a payment method
          </div>
        </CardTitle>
        <CardDescription className="flex justify-between">
          <div>
            <div className="flex font-semibold  items-center">
              <X className="h-6 w-6 text-red-500" />
              Automatic evaluation and event detection are currently disabled
            </div>
            <div className="text-gray-500">
              Your tasks are saved and we temporarily enabled event detection to
              help you get started.
            </div>
            <div>
              To continue using this feature, please provide a payment method.
            </div>
          </div>
          <UpgradeButton tagline="Add payment method" enlarge={false} />
        </CardDescription>
      </CardHeader>
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
