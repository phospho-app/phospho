import ShareButton from "@/components/share-button";
import { Spinner } from "@/components/small-spinner";
import { Progress } from "@/components/ui/progress";
import { authFetcher } from "@/lib/fetcher";
import { Clustering } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { useEffect } from "react";

function ClusteringLoading({
  selectedClustering,
  setSelectedClustering,
}: {
  selectedClustering: Clustering;
  setSelectedClustering: (clustering: Clustering) => void;
}) {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();
  const selectedClusteringJSON = JSON.stringify(selectedClustering);

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
        // Update the selectedClustering with the new status
        setSelectedClustering({
          ...selectedClustering,
          ...response,
        });
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [
    selectedClusteringJSON,
    project_id,
    accessToken,
    selectedClustering,
    setSelectedClustering,
  ]);

  const statusToDescription: Record<string, string> = {
    started: "Starting clustering",
    summaries: "Summarizing data",
    loading_existing_embeddings: "Loading existing embeddings",
    generate_clusters: "Generating clusters",
    generating_new_embeddings: "Generating new embeddings",
    generate_clusters_description_and_title:
      "Generating cluster descriptions and titles",
    merging_similar_clusters: "Merging similar clusters",
    saving_clusters: "Saving clusters",
  };

  return (
    <div className="w-full flex flex-col items-center">
      {selectedClustering.status !== "completed" && (
        <Progress
          value={Math.max(selectedClustering.percent_of_completion ?? 0, 1)}
          className="w-[100%] transition-all duration-500 ease-in-out mb-4 h-4"
        />
      )}
      {
        <div className="flex flex-row items-center text-muted-foreground text-sm">
          <Spinner className="mr-1" />
          {statusToDescription[selectedClustering.status ?? "started"]}
        </div>
      }
      <div className="flex flex-col text-muted-foreground text-sm space-y-2 pt-8">
        <div>
          While this is running, why not invite your team to the project?
        </div>
        <ShareButton variant="secondary" />
      </div>
    </div>
  );
}

export { ClusteringLoading };
