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
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useEffect, useState } from "react";
import useSWR from "swr";

import { ClustersCards } from "./clusters-cards";

const Clusters: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const { accessToken } = useUser();

  const [clusteringUnavailable, setClusteringUnavailable] = useState(true);
  const [sheetClusterOpen, setSheetClusterOpen] = useState(false);

  const { data: clusteringsData, mutate: mutateClusterings } = useSWR(
    project_id ? [`/api/explore/${project_id}/clusterings`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
      revalidateIfStale: false,
    },
  );
  let latestClustering: Clustering | undefined = undefined;
  if (clusteringsData) {
    latestClustering = clusteringsData?.clusterings[0];
  }

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
    totalNbTasksData?.total_nb_tasks ?? 0;

  const { data: totalNbSessionsData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/sessions`,
      accessToken,
      JSON.stringify(dataFilters),
      "total_nb_sessions",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_sessions"],
        filters: { ...dataFilters },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbSessions: number | null | undefined =
    totalNbSessionsData?.total_nb_sessions ?? 0;

  useEffect(() => {
    if (latestClustering?.status === "completed") {
      setClusteringUnavailable(false);
    }
    if (latestClustering?.status === undefined) {
      setClusteringUnavailable(false);
    }
  }, [latestClustering?.status]);

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
                totalNbSessions={totalNbSessions}
                mutateClusterings={mutateClusterings}
                clusteringUnavailable={clusteringUnavailable}
                sheetOpen={sheetClusterOpen}
                setSheetOpen={setSheetClusterOpen}
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
      <div className="flex-col space-y-2 md:flex pb-10">
        <ClustersCards setSheetClusterOpen={setSheetClusterOpen} />
      </div>
    </>
  );
};

export default Clusters;
