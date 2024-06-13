"use client";

import RunClusters from "@/components/insights/clusters/clusters-sheet";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import useSWR from "swr";

import { ClustersTable } from "./clusters-table";

const Clusters: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const { accessToken } = useUser();

  const [clusteringUnavailable, setClusteringUnavailable] =
    React.useState(true);

  const { data: clusteringsData, mutate: mutateClusterings } = useSWR(
    project_id ? [`/api/explore/${project_id}/clusterings`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
      revalidateIfStale: false,
      refreshInterval: 10,
    },
  );
  let latestClustering = undefined;
  if (clusteringsData) {
    latestClustering = clusteringsData?.clusterings[0];
  }

  React.useEffect(() => {
    if (latestClustering?.status === "completed") {
      setClusteringUnavailable(false);
    }
    if (latestClustering?.status === undefined) {
      setClusteringUnavailable(false);
    }
  }, [latestClustering?.status]);

  const maxCreatedAt = latestClustering?.created_at;
  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(dataFilters),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: { ...dataFilters },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <Card className="bg-secondary">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                Automatic cluster detection
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Detect recurring topics, trends, and outliers using unsupervized
                machine learning.
              </CardDescription>
            </div>
            <div className="flex flex-col space-y-1 justify-center items-center">
              <RunClusters
                totalNbTasks={totalNbTasks}
                mutateClusterings={mutateClusterings}
                clusteringUnavailable={clusteringUnavailable}
              />
              <div className="text-muted-foreground text-xs">
                Last update:{" "}
                {maxCreatedAt
                  ? formatUnixTimestampToLiteralDatetime(maxCreatedAt)
                  : "Never"}
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>
      <div className="h-full flex-1 flex-col space-y-2 md:flex ">
        <ClustersTable clusterings={clusteringsData?.clusterings} />
      </div>
    </>
  );
};

export default Clusters;
