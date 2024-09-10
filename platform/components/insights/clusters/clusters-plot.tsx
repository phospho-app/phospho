import { SendDataAlertDialog } from "@/components/callouts/import-data";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { set } from "date-fns";
import { ChevronRight, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { Data } from "plotly.js";
import { Suspense, lazy, use, useCallback, useEffect, useState } from "react";
import useSWR from "swr";

const Plot = lazy(() => import("react-plotly.js"));

function generateDummyData() {
  // Generate placeholder data for the plot
  // Generate four clusters of nearby points with the same color
  const numPoints = 50;
  const x = new Array(numPoints * 4);
  const y = new Array(numPoints * 4);
  const z = new Array(numPoints * 4);
  const colors = new Array(numPoints * 4);

  for (let i = 0; i < numPoints; i++) {
    x[i] = Math.random() * 0.4 - 0.1;
    y[i] = Math.random() * 0.2;
    z[i] = Math.random() * 0.2 - 0.1;
    colors[i] = graphColors[0];
  }

  for (let i = numPoints; i < numPoints * 2; i++) {
    x[i] = Math.random() * 0.6;
    y[i] = Math.random() * 0.2 + 0.2;
    z[i] = Math.random() * 0.15 + 0.1;
    colors[i] = graphColors[1];
  }

  for (let i = numPoints * 2; i < numPoints * 3; i++) {
    x[i] = Math.random() * 0.2 + 0.1;
    y[i] = Math.random() * 0.2 - 0.1;
    z[i] = Math.random() * 0.1 + 0.1;
    colors[i] = graphColors[2];
  }

  for (let i = numPoints * 3; i < numPoints * 4; i++) {
    x[i] = Math.random() * 0.2 + 0.1;
    y[i] = Math.random() * 0.2 + 0.1;
    z[i] = Math.random() * 0.1 + 0.1;
    colors[i] = graphColors[3];
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
      opacity: 0.4,
    },
  } as Data;
}

export function CustomPlot({
  selected_clustering_id,
  selectedClustering,
  dummyData = false,
  setSheetClusterOpen,
}: {
  selected_clustering_id?: string;
  selectedClustering?: Clustering;
  dummyData?: boolean;
  setSheetClusterOpen?: (value: boolean) => void;
}) {
  const project_id = navigationStateStore((state) => state.project_id);
  const [refresh, setRefresh] = useState(false);
  const router = useRouter();
  const { accessToken } = useUser();
  const [isAnimating, setIsAnimating] = useState(true);
  const [displayedData, setDisplayedData] = useState<Data | null | undefined>(
    undefined,
  );
  const [open, setOpen] = useState(false);

  const width =
    Math.round(
      Math.max(
        document.getElementsByClassName("custom-plot")[0]?.clientWidth ??
          window.innerWidth * 0.8,
        640,
      ) / 10,
    ) * 10;
  const height = Math.round(Math.max(window.innerHeight * 0.6, 300) / 10) * 10;
  // Skeleton style is used to set the width and height of the plot
  // And to load the skeleton with the correct size
  const skeletonStyle = `w-[${width}px] h-[${height}px]`;

  useEffect(() => {
    setRefresh(!refresh);
  }, [skeletonStyle]);

  const { data } = useSWR(
    project_id && !dummyData
      ? [
          `/api/explore/${project_id}/data-cloud`,
          accessToken,
          JSON.stringify(selectedClustering),
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
    if (dummyData) {
      setDisplayedData(generateDummyData());
    } else {
      setDisplayedData(data);
    }
  }, [data, dummyData]);

  const defaultLayout = {
    height: height,
    width: width,
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
  };

  const [layout, setLayout] = useState(defaultLayout);

  // Animation
  let frame = 0;
  const totalFrames = 3600;
  const zoomCycles = 2; // Number of zoom in/out cycles per full rotation

  const animate = useCallback(() => {
    if (!isAnimating) return;
    const t = frame / totalFrames;
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

    // frame = (frame + 1) % totalFrames;
    frame = (frame + 1) % totalFrames;
  }, [isAnimating]);
  requestAnimationFrame(animate);

  useEffect(() => {
    // When the project_id changes, force a refresh to resize the plot
    setRefresh(!refresh);
    setIsAnimating(true);
  }, [project_id, selected_clustering_id]);

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

  if (!displayedData) {
    return <></>;
  }

  return (
    <AlertDialog open={open}>
      <SendDataAlertDialog setOpen={setOpen} key="ab_testing" />
      <div
        className={`relative ${skeletonStyle}`}
        onClick={() => {
          if (!dummyData) {
            setIsAnimating(false);
          }
        }}
      >
        <Suspense fallback={<div className={skeletonStyle} />}>
          <Plot
            data={[displayedData]}
            config={{ displayModeBar: !dummyData, responsive: true }}
            layout={layout}
            onClick={(displayedData) => {
              if (displayedData.points.length !== 1) {
                return;
              }
              if (displayedData.points[0].text) {
                router.push(
                  `/org/transcripts/tasks/${encodeURIComponent(displayedData.points[0].text)}`,
                );
              }
            }}
          />
        </Suspense>
        {dummyData && (
          // display a gradient background from green to purple
          <div className="absolute top-0 left-0 bottom-0 right-0 flex justify-center items-center ">
            <div className="bg-secondary p-4 rounded-lg flex flex-col justify-center space-y-4">
              <div className="flex flex-col justify-center">
                <p className="text-muted-foreground text-sm mb-2">
                  1 - Start sending data
                </p>
                <Button variant="outline" onClick={() => setOpen(true)}>
                  Import data
                  <ChevronRight className="ml-2" />
                </Button>
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
    </AlertDialog>
  );
}
