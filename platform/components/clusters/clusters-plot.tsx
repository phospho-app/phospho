"use client";

import { SendDataAlertDialog } from "@/components/callouts/import-data";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Check, ChevronRight, Plus } from "lucide-react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import {
  //  Config,
  Data, //  Layout
} from "plotly.js";
import {
  Suspense, // forwardRef, // lazy,
  useCallback,
  useEffect, // useId,
  // useImperativeHandle,
  useRef,
  useState,
} from "react";
import useSWR from "swr";

// interface PlotProps {
//   id?: string;
//   className?: string;
//   data: Data[];
//   layout?: Partial<Layout>;
//   config?: Partial<Config>;
//   // eslint-disable-next-line @typescript-eslint/no-explicit-any
//   onClick?: (displayedDataPoints: any) => void;
// }

// export const Plot = dynamic(
//   () =>
//     // @ts-expect-error This module is a dynamic import installed with react-plotly
//     // See https://dev.to/composite/how-to-integrate-plotlyjs-on-nextjs-14-with-app-router-1loj
//     import("plotly.js/dist/plotly.js").then(({ newPlot, purge }) => {
//       const Plotly = forwardRef<HTMLDivElement, PlotProps>(
//         ({ id, className, data, layout, config }, ref) => {
//           const originId = useId();
//           const realId = id || originId;
//           const originRef = useRef<HTMLDivElement | null>(null);
//           const [handle, setHandle] = useState<
//             Plotly.PlotlyHTMLElement | undefined
//           >(undefined);

//           useEffect(() => {
//             let instance: Plotly.PlotlyHTMLElement | undefined;
//             if (originRef.current) {
//               newPlot(originRef.current!, data, layout, config).then(
//                 (ref: Plotly.PlotlyHTMLElement) => setHandle((instance = ref)),
//               );
//             }
//             return () => {
//               if (instance) {
//                 purge(instance);
//               }
//             };
//           }, [data, layout, config]);

//           useImperativeHandle(
//             ref,
//             () =>
//               (handle as unknown as HTMLDivElement) ??
//               originRef.current ??
//               document.createElement("div"),
//             [handle],
//           );

//           return <div id={realId} ref={originRef} className={className}></div>;
//         },
//       );
//       Plotly.displayName = "Plotly";
//       return Plotly;
//     }),
//   { ssr: false },
// );
export const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });
// const Plot = lazy(() => import("react-plotly.js"));

function generateDummyData({ displayCTA = false }: { displayCTA?: boolean }) {
  // Generate placeholder data for the plot
  // Generate four clusters of nearby points with the same color
  const numPoints = 50;
  const x = new Array(numPoints * 4);
  const y = new Array(numPoints * 4);
  const z = new Array(numPoints * 4);
  const colors = new Array(numPoints * 4);
  const clusterNames = new Array(numPoints * 4);

  for (let i = 0; i < numPoints; i++) {
    x[i] = Math.random() * 0.4 - 0.1;
    y[i] = Math.random() * 0.2;
    z[i] = Math.random() * 0.2 - 0.1;
    colors[i] = graphColors[0];
    clusterNames[i] = "Question about the products";
  }

  for (let i = numPoints; i < numPoints * 2; i++) {
    x[i] = Math.random() * 0.6;
    y[i] = Math.random() * 0.2 + 0.2;
    z[i] = Math.random() * 0.15 + 0.1;
    colors[i] = graphColors[1];
    clusterNames[i] = "Asking for help";
  }

  for (let i = numPoints * 2; i < numPoints * 3; i++) {
    x[i] = Math.random() * 0.2 + 0.1;
    y[i] = Math.random() * 0.2 - 0.1;
    z[i] = Math.random() * 0.1 + 0.1;
    colors[i] = graphColors[2];
    clusterNames[i] = "Feedback";
  }

  for (let i = numPoints * 3; i < numPoints * 4; i++) {
    x[i] = Math.random() * 0.2 + 0.1;
    y[i] = Math.random() * 0.2 + 0.1;
    z[i] = Math.random() * 0.1 + 0.1;
    colors[i] = graphColors[3];
    clusterNames[i] = "Bug report";
  }

  return {
    x,
    y,
    z,
    mode: "markers",
    type: "scatter3d",
    marker: {
      size: 6,
      color: colors,
      opacity: displayCTA ? 0.5 : 0.8,
    },
    hoverinfo: "text",
    hovertext: clusterNames,
  } as Data;
}

export function CustomPlot({
  selected_clustering_id,
  selectedClustering,
  dummyData = false,
  displayCTA = false,
  setSheetClusterOpen,
}: {
  selected_clustering_id?: string;
  selectedClustering?: Clustering;
  dummyData?: boolean;
  displayCTA?: boolean;
  setSheetClusterOpen?: (value: boolean) => void;
}) {
  const project_id = navigationStateStore((state) => state.project_id);
  const [refreshKey, setRefreshKey] = useState(0);
  const router = useRouter();
  const { accessToken } = useUser();
  const [isAnimating, setIsAnimating] = useState(true);
  const [displayedData, setDisplayedData] = useState<Data | null | undefined>(
    undefined,
  );
  const [open, setOpen] = useState(false);
  const frameRef = useRef(0);

  let width = 640;
  let height = 300;
  // For SSR, we need to check if document is defined
  if (typeof document !== "undefined") {
    width =
      Math.round(
        Math.max(
          document?.getElementsByClassName("custom-plot")[0]?.clientWidth ??
            window.innerWidth * 0.8,
          640,
        ) / 10,
      ) * 10;
  }
  if (typeof window !== "undefined") {
    height = Math.round(Math.max(window.innerHeight * 0.6, 300) / 10) * 10;
  }
  // Skeleton style is used to set the width and height of the plot
  // And to load the skeleton with the correct size
  const skeletonStyle = `w-[${width}px] h-[${height}px]`;

  useEffect(() => {
    setRefreshKey((r) => r + 1);
  }, [skeletonStyle]);

  const { data } = useSWR(
    project_id && !dummyData
      ? [
          `/api/explore/${project_id}/data-cloud`,
          accessToken,
          JSON.stringify(selectedClustering),
          refreshKey, // Add refreshKey to the dependency array
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        clustering_id: selected_clustering_id,
        type: "pca",
      }).then((res) => {
        if (res === undefined) return undefined;
        // if res is {}, return undefined
        if (Object.keys(res).length === 0) {
          // TODO : return something else than null
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
          clusterIdToColor.set(
            cluster_id,
            graphColors[index % graphColors.length],
          );
        });
        const colors: string[] = res.clusters_ids.map((cluster_id: string) => {
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
    if (dummyData) {
      setDisplayedData(generateDummyData({ displayCTA }));
    } else {
      setDisplayedData(data);
    }
  }, [data, dummyData]); // eslint-disable-line react-hooks/exhaustive-deps

  const [layout, setLayout] = useState(() => ({
    height: height,
    width: width,
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
  }));

  const handleResize = useCallback(() => {
    setLayout((prevLayout) => ({
      ...prevLayout,
      height: Math.max(window.innerHeight * 0.6, 300),
      width: Math.max(
        document.getElementsByClassName("custom-plot")[0]?.clientWidth ??
          window.innerWidth * 0.8,
        640,
      ),
    }));
    setRefreshKey((prev) => prev + 1); // Increment refreshKey to trigger a re-fetch
  }, []);

  useEffect(() => {
    handleResize(); // Initial resize
    window.addEventListener("resize", handleResize);
    window.addEventListener("orientationchange", handleResize);
    // Clean up the event listener when the component is unmounted
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("orientationchange", handleResize);
    };
  }, [handleResize]);

  useEffect(() => {
    setIsAnimating(true);
    setRefreshKey((prev) => prev + 1); // Trigger a refresh when project_id or selected_clustering_id changes
  }, [project_id, selected_clustering_id]);

  // The total nb of task is used to personalize the tooltip
  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
      }),
    {
      keepPreviousData: true,
    },
  );

  const totalFrames = 3600;
  const zoomCycles = 2; // Number of zoom in/out cycles per full rotation

  const animate = useCallback(() => {
    if (!isAnimating) return;

    const t = frameRef.current / totalFrames;
    const zoomT = (Math.sin(2 * Math.PI * zoomCycles * t) + 1) / 2; // Oscillates between 0 and 1
    const zoom = 1 + zoomT * 0.3; // Zoom factor oscillates between 1.25 and 1.75

    const newEye = {
      x: zoom * Math.cos(2 * Math.PI * t),
      y: zoom * Math.sin(2 * Math.PI * t),
      z: 0 + zoomT * 0.1, // Slight vertical oscillation
    };

    setLayout((prevLayout) => ({
      ...prevLayout,
      scene: {
        ...prevLayout.scene,
        camera: { eye: newEye },
      },
    }));

    frameRef.current = (frameRef.current + 1) % totalFrames;
    // requestAnimationFrame(animate);
  }, [isAnimating, totalFrames, zoomCycles]);

  if (typeof window !== "undefined") {
    requestAnimationFrame(animate);
  }

  if (!displayedData) {
    return <></>;
  }

  return (
    <AlertDialog open={open}>
      <SendDataAlertDialog setOpen={setOpen} key="ab_testing" />
      <div
        onClick={() => {
          if (!dummyData) {
            setIsAnimating(false);
          }
        }}
      >
        <div className={`relative ${skeletonStyle}`}>
          <Suspense fallback={<Skeleton className={skeletonStyle} />}>
            <Plot
              data={[displayedData]}
              config={{ displayModeBar: !dummyData, responsive: true }}
              layout={layout}
              onClick={(displayedDataPoints) => {
                console.log("displayedDataPoints", displayedDataPoints);
                if (
                  displayedDataPoints.points.length === 1 &&
                  displayedDataPoints.points[0].text
                ) {
                  if (selectedClustering?.scope === "sessions") {
                    router.push(
                      `/org/transcripts/sessions/${encodeURIComponent(
                        displayedDataPoints.points[0].text,
                      )}`,
                    );
                  } else if (selectedClustering?.scope === "messages") {
                    router.push(
                      `/org/transcripts/tasks/${encodeURIComponent(displayedDataPoints.points[0].text)}`,
                    );
                  }
                }
              }}
            />
          </Suspense>
          {displayCTA && (
            // display a gradient background from green to purple
            <div className="absolute top-0 left-0 bottom-0 right-0 flex justify-center items-center ">
              <div className="bg-secondary p-4 rounded-lg flex flex-col justify-center space-y-4">
                <div className="flex flex-col justify-center">
                  <p className="text-muted-foreground text-sm mb-2">
                    1 - Start sending data
                  </p>
                  {!totalNbTasksData?.total_nb_tasks && (
                    <Button variant="outline" onClick={() => setOpen(true)}>
                      Import data
                      <ChevronRight className="ml-2" />
                    </Button>
                  )}
                  {totalNbTasksData?.total_nb_tasks > 0 && (
                    // Display a "Done"
                    <Button variant="outline" disabled>
                      <Check className="w-4 h-4 mr-1" />
                      Done
                    </Button>
                  )}
                </div>
                <div className="flex flex-col justify-center">
                  <p className="text-muted-foreground text-sm mb-2">
                    2 - Create a new clustering
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => {
                      if (setSheetClusterOpen) {
                        setSheetClusterOpen(true);
                      }
                    }}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    New clustering
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AlertDialog>
  );
}
