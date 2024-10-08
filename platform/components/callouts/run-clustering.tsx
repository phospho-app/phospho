import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { OrgMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Boxes, ChevronRight } from "lucide-react";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

export function RunClusteringCallout() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);

  const { data: selectedOrgMetadata }: { data: OrgMetadata } = useSWR(
    selectedOrgId
      ? [`/api/organizations/${selectedOrgId}/metadata`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  return (
    <>
      {hasTasks === true &&
        (selectedOrgMetadata?.plan === "pro" ||
          selectedOrgMetadata?.plan === "usage_based") && (
          <Card className="bg-secondary">
            <CardHeader>
              <div className="flex">
                <Boxes className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
                <div className="flex flex-grow justify-between items-center">
                  <div>
                    <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                      <div className="flex flex-row place-items-center">
                        Discover patterns in your data with clustering
                      </div>
                    </CardTitle>
                    <CardDescription className="flex justify-between flex-col text-muted-foreground space-y-0.5">
                      <p>
                        The clustering tool groups your data based on similar
                        features.
                      </p>
                    </CardDescription>
                  </div>
                  <Link href="/org/insights/clusters">
                    <Button variant="default">
                      Cluster data
                      <ChevronRight className="ml-2" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardHeader>
          </Card>
        )}
    </>
  );
}
