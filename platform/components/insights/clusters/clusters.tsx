"use client";

import RunClusters from "@/components/insights/clusters/clusters-sheet";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useEffect, useState } from "react";
import useSWR from "swr";

import { ClustersCards } from "./clusters-cards";
import { ClusteringDropDown } from "./clusters-drop-down";
import { CustomPlot } from "./clusters-plot";

const Clusters: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const [sheetClusterOpen, setSheetClusterOpen] = useState(false);
  const [selectedClustering, setSelectedClustering] = useState<
    Clustering | undefined
  >(undefined);

  const { data: clusteringsData } = useSWR(
    project_id ? [`/api/explore/${project_id}/clusterings`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST").then((res) => {
        if (!res?.clusterings) return undefined;
        return res;
      }),
    {
      keepPreviousData: true,
    },
  );
  const clusterings = clusteringsData
    ? (clusteringsData.clusterings.sort(
        (a: Clustering, b: Clustering) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ) as Clustering[])
    : undefined;

  let selectedClusteringName = selectedClustering?.name;
  if (selectedClustering && !selectedClusteringName) {
    selectedClusteringName = formatUnixTimestampToLiteralDatetime(
      selectedClustering.created_at,
    );
  }

  useEffect(() => {
    if (clusterings === undefined) {
      setSelectedClustering(undefined);
      return;
    }
    if (clusterings.length === 0) {
      setSelectedClustering(undefined);
      return;
    }
    const latestClustering = clusterings[0];
    setSelectedClustering(latestClustering);
  }, [JSON.stringify(clusterings), project_id]);

  // Add a useEffect triggered every few seconds to update the clustering status
  useEffect(() => {
    if (selectedClustering && selectedClustering?.status !== "completed") {
      const interval = setInterval(async () => {
        // Use the fetch function to update the clustering status
        const response = await authFetcher(
          `/api/explore/${project_id}/clusterings/${selectedClustering?.id}`,
          accessToken,
          "POST",
        );
        console.log("Updating clustering status", response);
        // Update the selectedClustering with the new status
        setSelectedClustering({
          ...selectedClustering,
          ...response,
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [JSON.stringify(selectedClustering), project_id]);

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
                sheetOpen={sheetClusterOpen}
                setSheetOpen={setSheetClusterOpen}
                setSelectedClustering={setSelectedClustering}
              />
            </div>
          </div>
        </CardHeader>
      </Card>
      <div>
        <ClusteringDropDown
          selectedClustering={selectedClustering}
          setSelectedClustering={setSelectedClustering}
          clusterings={clusterings}
          selectedClusteringName={selectedClusteringName}
        />
        <div className="flex-col space-y-2 md:flex pb-10">
          {!selectedClustering && (
            <div className="w-full text-muted-foreground flex justify-center text-sm h-20">
              Run a clustering to see clusters here.
            </div>
          )}
          {selectedClustering && selectedClustering.status !== "completed" && (
            <div className="w-full flex flex-col items-center">
              {selectedClustering.percent_of_completion && (
                <Progress
                  value={selectedClustering.percent_of_completion}
                  className="w-[30%] transition-all duration-500 ease-in-out mb-4 h-4"
                />
              )}
              {selectedClustering.status === "started" && (
                <div className="text-muted-foreground text-sm h-20">
                  Computing embeddings...
                </div>
              )}
              {selectedClustering.status === "summaries" && (
                <div className="text-muted-foreground text-sm h-20">
                  Generating summaries...
                </div>
              )}
            </div>
          )}
          {selectedClustering !== undefined && selectedClustering !== null && (
            <CustomPlot
              selected_clustering_id={selectedClustering.id}
              selectedClustering={selectedClustering}
            />
          )}
          <ClustersCards
            setSheetClusterOpen={setSheetClusterOpen}
            selected_clustering_id={selectedClustering?.id}
            selectedClustering={selectedClustering}
          />
        </div>
      </div>
    </>
  );
};

export default Clusters;
