import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useRouter } from "next/navigation";
import { Data } from "plotly.js";
import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
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
  const [refreshKey, setRefreshKey] = useState(0);
  const router = useRouter();
  const { accessToken } = useUser();
  const [isAnimating, setIsAnimating] = useState(true);
  const frameRef = useRef(0);

  const { data } = useSWR(
    project_id
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

  const [layout, setLayout] = useState(() => ({
    height: Math.max(window.innerHeight * 0.6, 300),
    width: Math.max(
      document.getElementsByClassName("custom-plot")[0]?.clientWidth ??
        window.innerWidth * 0.8,
      640,
    ),
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
    requestAnimationFrame(animate);
  }, [isAnimating, totalFrames, zoomCycles]);

  useEffect(() => {
    if (isAnimating) {
      requestAnimationFrame(animate);
    }
  }, [isAnimating, animate]);

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
              if (data.points.length === 1 && data.points[0].text) {
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
