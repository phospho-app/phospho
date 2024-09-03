"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { graphColors } from "@/lib/utils";
import { Cluster, Clustering, EventDefinition } from "@/models/models";
import { Project } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, Pickaxe, PlusIcon } from "lucide-react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { Data } from "plotly.js";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

import CreateEvent from "../events/create-event";
import "./style.css";

// Dynamically import the Plotly component
// https://github.com/plotly/react-plotly.js/issues/272
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

function ClusterCard({
  cluster,
  setSheetClusterOpen,
}: {
  cluster: Cluster;
  setSheetClusterOpen: (value: boolean) => void;
}) {
  /* This is a single cluster card */
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const router = useRouter();
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const setDataFilters = navigationStateStore((state) => state.setDataFilters);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);

  const [sheetEventOpen, setSheetEventOpen] = useState(false);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const events = selectedProject?.settings?.events || {};

  // Max number of events depends on the plan
  const max_nb_events = orgMetadata?.plan === "pro" ? 100 : 10;
  const current_nb_events = Object.keys(events).length;
  let isDisabled = max_nb_events && current_nb_events >= max_nb_events;

  const eventToEdit = {
    project_id: project_id,
    org_id: selectedProject.org_id,
    event_name: cluster.name,
    description: cluster.description,
    score_range_settings: {
      min: 0,
      max: 1,
      score_type: "confidence",
    },
  } as EventDefinition;

  return (
    <Card
      key={cluster.id}
      className="rounded-lg shadow-md p-4 flex flex-col justify-between h-full"
    >
      <HoverCard openDelay={0} closeDelay={0}>
        <div className="flex justify-between items-start space-x-2 mb-2">
          <h3 className="text-lg font-semibold text-center">{cluster.name}</h3>
          <HoverCardTrigger asChild>
            <div className="text-xl bg-primary text-secondary rounded-tr-lg px-3">
              {cluster.size}
            </div>
          </HoverCardTrigger>
        </div>
        <HoverCardContent className="text-secondary bg-primary text-xs">
          <p>Cluster size</p>
        </HoverCardContent>
      </HoverCard>
      <p className="text-sm text-muted-foreground mb-4">
        {cluster.description}
      </p>
      <div className="mt-auto pt-2 flex justify-end space-x-2">
        <Sheet
          open={sheetEventOpen}
          onOpenChange={setSheetEventOpen}
          key={cluster.id}
        >
          <SheetTrigger asChild>
            <Button disabled={isDisabled} size="sm" variant="outline">
              <PlusIcon className="h-4 w-4 mr-1" />
              Add tagger
            </Button>
          </SheetTrigger>
          <SheetContent className="md:w-1/2 overflow-auto">
            <CreateEvent
              setOpen={setSheetEventOpen}
              eventToEdit={eventToEdit}
            />
          </SheetContent>
        </Sheet>
        {cluster.size > 5 && (
          <Button
            className="pickaxe-button"
            variant="outline"
            size="sm"
            onClick={(mouseEvent) => {
              mouseEvent.stopPropagation();
              setSheetClusterOpen(true);
              setDataFilters({
                ...dataFilters,
                clustering_id: cluster.clustering_id,
                clusters_ids: [cluster.id],
              });
            }}
          >
            Break down
            <Pickaxe className="w-6 h-6 ml-1 pickaxe-animation" />
          </Button>
        )}
        <Button
          variant="secondary"
          size="sm"
          onClick={(mouseEvent) => {
            mouseEvent.stopPropagation();
            setDataFilters({
              ...dataFilters,
              clustering_id: cluster.clustering_id,
              clusters_ids: [cluster.id],
            });
            router.push(
              `/org/insights/clusters/${encodeURIComponent(cluster.id)}`,
            );
          }}
        >
          Explore
          <ChevronRight className="w-4 h-4 ml-1" />
        </Button>
      </div>
    </Card>
  );
}

// const Animated3DScatterPlot = () => {
//   const plotRef = useRef(null);

//   useEffect(() => {
//     let angle = 0;
//     const radius = 10;
//     const speed = 0.01;

//     const animate = () => {
//       if (plotRef.current) {
//         const eye = {
//           x: radius * Math.cos(angle),
//           y: radius * Math.sin(angle),
//           z: 2,
//         };

//         angle += speed;
//         if (angle > 2 * Math.PI) angle = 0;
//       }
//     };

//     const interval = setInterval(animate, 100);

//     return () => clearInterval(interval); // Clean up on unmount
//   }, []);
// };

function CustomPlot({
  selected_clustering_id,
  selectedClustering,
}: {
  selected_clustering_id: string;
  selectedClustering: Clustering;
}) {
  const project_id = navigationStateStore((state) => state.project_id);
  const [refresh, setRefresh] = useState(false);
  const router = useRouter();
  const { accessToken } = useUser();

  const { data } = useSWR(
    project_id &&
      selected_clustering_id &&
      selectedClustering.status === "completed"
      ? [
          `/api/explore/${project_id}/data-cloud`,
          accessToken,
          JSON.stringify(selected_clustering_id),
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        clustering_id: selected_clustering_id,
        type: "pca",
      }).then((res) => {
        console.log("res is ", res);
        if (res === undefined) return undefined;
        // if res is {}, return undefined
        if (Object.keys(res).length === 0) {
          // TODO : return something else than null
          console.log("res is empty");
          return null;
        }

        // Generate a color for each cluster
        const clusterIdToColor = new Map<string, string>();
        const clusters = res.clusters_ids as string[];
        const uniqueClusterIds: string[] = [];
        clusters.forEach((cluster_id) => {
          if (!uniqueClusterIds.includes(cluster_id)) {
            uniqueClusterIds.push(cluster_id);
          }
        });

        const clusters_names = res.clusters_names as string[];
        uniqueClusterIds.forEach((cluster_id, index) => {
          console.log("index", index);
          clusterIdToColor.set(
            cluster_id,
            graphColors[index % graphColors.length],
          );
        });
        const colors: string[] = res.clusters_ids.map((cluster_id: any) => {
          return clusterIdToColor.get(cluster_id) as string;
        });

        return {
          x: res.x,
          y: res.y,
          z: res.z,
          text: res.ids,
          mode: "markers",
          type: "scatter3d",
          marker: {
            size: 6,
            color: colors,
            opacity: 0.8,
          },
          hoverinfo: "text",
          hovertext: clusters_names,
        } as Data;
      }),
    {
      keepPreviousData: true,
    },
  );

  useEffect(() => {
    // When the project_id changes, force a refresh to resize the plot
    setRefresh(!refresh);
  }, [project_id]);

  useEffect(() => {
    const handleResize = () => {
      // Force a refresh to resize the plot
      setRefresh(!refresh);
    };
    // Set the initial state
    handleResize();
    // Add event listener for window resize
    window.addEventListener("resize", handleResize);
    window.addEventListener("orientationchange", handleResize);
    // Clean up the event listener when the component is unmounted
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  if (!project_id) {
    return <></>;
  }

  if (data === null || data === undefined) {
    return <></>;
  }

  return (
    <Plot
      data={[data]}
      config={{ displayModeBar: true, responsive: true }}
      layout={{
        height: Math.max(window.innerHeight * 0.6, 300),
        // set it to be the size of the current div in pixel
        width: document.getElementsByClassName("custom-plot")[0].clientWidth,
        // autosize: true,
        scene: {
          xaxis: {
            visible: false,
            showgrid: false,
            zeroline: false,
            showline: false,
            showticklabels: false,
            spikesides: false,
            showspikes: false,
          },
          yaxis: {
            visible: false,
            showgrid: false,
            zeroline: false,
            showline: false,
            showticklabels: false,
            spikesides: false,
            showspikes: false,
          },
          zaxis: {
            visible: false,
            showgrid: false,
            zeroline: false,
            showline: false,
            showticklabels: false,
            spikesides: false,
            showspikes: false,
          },
        },
        paper_bgcolor: "rgba(0,0,0,0)", // Fully transparent paper background
        plot_bgcolor: "rgba(0,0,0,0)", // Fully transparent plot background
      }}
      onClick={(data) => {
        // if double click, redirect to the task page
        if (data.points.length !== 1) {
          return;
        }
        if (data.points[0].text) {
          router.push(
            `/org/transcripts/tasks/${encodeURIComponent(data.points[0].text)}`,
          );
        }
      }}
    />
  );
}

export function ClustersCards({
  setSheetClusterOpen: setSheetClusterOpen,
}: {
  setSheetClusterOpen: (value: boolean) => void;
}) {
  /* This is the group of all cluster cards */
  const [selectedClustering, setSelectedClustering] = useState<
    Clustering | undefined
  >(undefined);
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: clusterings } = useSWR(
    project_id ? [`/api/explore/${project_id}/clusterings`, accessToken] : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST").then((res) => {
        if (res === undefined) return undefined;

        const clusterings = (res?.clusterings as Clustering[]) ?? [];
        console.log("clusterings", clusterings);
        return clusterings.sort(
          (a: Clustering, b: Clustering) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
      }),
    {
      keepPreviousData: true,
    },
  );

  let selectedClusteringName = selectedClustering?.name;
  if (selectedClustering && !selectedClusteringName) {
    selectedClusteringName = formatUnixTimestampToLiteralDatetime(
      selectedClustering.created_at,
    );
  }

  useEffect(() => {
    setSelectedClustering(undefined);
  }, [project_id]);

  useEffect(() => {
    if (clusterings === undefined) {
      setSelectedClustering(undefined);
      return;
    }
    const latestClustering = clusterings[0];
    setSelectedClustering(latestClustering);
  }, [JSON.stringify(clusterings), project_id]);

  // Used to fetch rapidly changing data in the clustering (eg: progress)
  // const { data } = useSWR(
  //   project_id && selectedClustering?.id
  //     ? [
  //         `/api/explore/${project_id}/clusterings/${selectedClustering?.id}`,
  //         accessToken,
  //         selectedClustering?.id,
  //       ]
  //     : null,
  //   ([url, accessToken]) =>
  //     authFetcher(url, accessToken, "POST").then((res) => {
  //       if (res === undefined) return undefined;
  //       setSelectedClustering({
  //         ...selectedClustering,
  //         ...res,
  //       });
  //     }),
  //   {
  //     refreshInterval:
  //       selectedClustering?.status === "completed" ? 30000 : 5000,
  //   },
  // );

  // Add a useEffect triggered every few seconds to update the clustering status
  useEffect(() => {
    if (selectedClustering && selectedClustering?.status !== "completed") {
      const interval = setInterval(async () => {
        console.log("refreshing clustering status");
        // Use the fetch function to update the clustering status
        const response = await authFetcher(
          `/api/explore/${project_id}/clusterings/${selectedClustering?.id}`,
          accessToken,
          "POST",
        );
        // Update the selectedClustering with the new status
        setSelectedClustering({
          ...selectedClustering,
          ...response,
        });
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedClustering]);

  console.log("selectedClustering", selectedClustering);
  console.log("selectedClusteringName", selectedClusteringName);

  const {
    data: clustersData,
  }: {
    data: Cluster[] | null | undefined;
  } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/clusters`,
          accessToken,
          selectedClustering?.id,
          project_id,
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        clustering_id: selectedClustering?.id,
        limit: 100,
      }).then((res) => {
        if (res === undefined) return undefined;
        return res?.clusters.sort((a: Cluster, b: Cluster) => b.size - a.size);
      }),
    {
      keepPreviousData: true,
    },
  );

  if (!project_id) {
    return <></>;
  }

  console.log("clustering progress", selectedClustering?.percent_of_completion);
  console.log("clusterings", clusterings);

  return (
    <div>
      <div className="flex flex-row gap-x-2 items-center mb-2 custom-plot w-full">
        <div>
          <Select
            onValueChange={(value: string) => {
              if (value === "no-clustering") {
                setSelectedClustering(undefined);
                return;
              }
              if (clusterings === undefined) {
                return;
              }
              setSelectedClustering(
                clusterings.find((clustering) => clustering.id === value),
              );
            }}
            defaultValue={
              clusterings && clusterings?.length > 0
                ? formatUnixTimestampToLiteralDatetime(
                    clusterings[0].created_at,
                  )
                : ""
            }
          >
            <SelectTrigger>
              <div>
                {clusterings && clusterings?.length > 0 && (
                  <span>{selectedClusteringName}</span>
                )}
                {clusterings?.length === 0 && (
                  <span className="text-muted-foreground">
                    No clustering available
                  </span>
                )}
              </div>
            </SelectTrigger>
            <SelectContent className="overflow-y-auto max-h-[20rem]">
              <SelectGroup>
                {clusterings &&
                  clusterings.length > 0 &&
                  clusterings.map((clustering) => (
                    <SelectItem key={clustering.id} value={clustering.id}>
                      {clustering?.name ??
                        formatUnixTimestampToLiteralDatetime(
                          clustering.created_at,
                        )}
                    </SelectItem>
                  ))}
                {clusterings && clusterings.length === 0 && (
                  <SelectItem value="no-clustering">
                    No clustering available
                  </SelectItem>
                )}
                {clusterings === undefined && (
                  <SelectItem value="no-clustering">Loading...</SelectItem>
                )}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
        <div>
          <Badge>{selectedClustering?.instruction ?? "No instruction"}</Badge>
        </div>
        <div>
          <Badge>{selectedClustering?.nb_clusters ?? "No"} clusters</Badge>
        </div>
      </div>
      {!selectedClustering && (
        <div className="w-full text-muted-foreground flex justify-center text-sm h-20">
          Run a clustering to see clusters here.
        </div>
      )}
      {selectedClustering?.status !== "completed" &&
        selectedClustering &&
        clustersData?.length === 0 && (
          <div className="w-full flex flex-col items-center">
            {selectedClustering?.percent_of_completion && (
              <Progress
                value={selectedClustering.percent_of_completion}
                className="w-[30%] transition-all duration-500 ease-in-out mb-4 h-4"
              />
            )}
            {selectedClustering?.status === "started" && (
              <div className="text-muted-foreground text-sm h-20">
                Computing embeddings...
              </div>
            )}
            {selectedClustering?.status === "summaries" && (
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clustersData?.map((cluster) => {
          return (
            <ClusterCard
              key={cluster.id}
              cluster={cluster}
              setSheetClusterOpen={setSheetClusterOpen}
            />
          );
        })}
      </div>
    </div>
  );
}
