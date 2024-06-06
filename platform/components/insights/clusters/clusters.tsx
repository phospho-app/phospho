"use client";

import { Spinner } from "@/components/small-spinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Play } from "lucide-react";
import React from "react";
import useSWR from "swr";

import { ClustersTable } from "./clusters-table";

const Clusters: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const { toast } = useToast();

  const { data: clusteringsData, mutate: mutateClusterings } = useSWR(
    project_id ? [`/api/explore/${project_id}/clusterings`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
    },
  );
  let latestClustering = undefined;
  if (clusteringsData) {
    latestClustering = clusteringsData?.clusterings[0];
  }

  const maxCreatedAt = latestClustering?.created_at;

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
              <CardDescription>
                <p className="text-muted-foreground">
                  Detect recurring topics, trends, and outliers using
                  unsupervized machine learning.
                </p>
              </CardDescription>
            </div>
            <div className="flex flex-col space-y-1 justify-center items-center">
              <Button
                variant="default"
                onClick={async () => {
                  mutateClusterings((data: any) => {
                    // Add a new clustering to the list
                    const newClustering: Clustering = {
                      id: "",
                      clustering_id: "",
                      project_id: project_id,
                      org_id: "",
                      created_at: Date.now() / 1000,
                      status: "started",
                      clusters_ids: [],
                    };
                    const newData = {
                      clusterings: [newClustering, ...data?.clusterings],
                    };
                    return newData;
                  });
                  try {
                    await fetch(`/api/explore/${project_id}/detect-clusters`, {
                      method: "POST",
                      headers: {
                        Authorization: "Bearer " + accessToken,
                      },
                    }).then((response) => {
                      if (response.status == 200) {
                        toast({
                          title: "Cluster detection started",
                          description: "This may take a few minutes.",
                        });
                      } else {
                        toast({
                          title: "Error when starting detection",
                          description: response.text(),
                        });
                      }
                    });
                  } catch (e) {
                    toast({
                      title: "Error when starting detection",
                      description: JSON.stringify(e),
                    });
                  }
                }}
                disabled={
                  latestClustering?.status !== "completed" &&
                  latestClustering?.status !== null &&
                  latestClustering?.status !== undefined
                }
              >
                {(latestClustering?.status === "completed" ||
                  latestClustering?.status === null ||
                  latestClustering?.status === undefined) && (
                  <>
                    <Play className="w-4 h-4 mr-2 text-green-500" /> Run cluster
                    detection
                  </>
                )}
                {latestClustering &&
                  latestClustering?.status !== "completed" &&
                  latestClustering?.status !== null &&
                  latestClustering?.status !== undefined && (
                    <>
                      <Spinner className="mr-1" />
                      Detection in progress: {latestClustering?.status}...
                    </>
                  )}
              </Button>
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
