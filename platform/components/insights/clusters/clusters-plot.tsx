import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { Data } from "plotly.js";
import { Suspense, lazy, useCallback, useEffect, useState } from "react";
import useSWR from "swr";

const Plot = lazy(() => import("react-plotly.js"));

export function CustomPlot({
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
  const [isAnimating, setIsAnimating] = useState(true);

  const { data } = useSWR(
    project_id
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

  const defaultLayout = {
    height: Math.max(window.innerHeight * 0.6, 300),
    // set it to be the size of the current div in pixel
    width: Math.max(
      document.getElementsByClassName("custom-plot")[0]?.clientWidth ??
        window.innerWidth * 0.8,
      640,
    ),
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
    console.log("frame", frame);
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

  if (!data) {
    return <></>;
  }

  return (
    <>
      <Suspense fallback={<></>}>
        <div onClick={() => setIsAnimating(false)}>
          <Plot
            data={[data]}
            config={{ displayModeBar: true, responsive: true }}
            layout={layout}
            onClick={(data) => {
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
        </div>
      </Suspense>
    </>
  );
}
