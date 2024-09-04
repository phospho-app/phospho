import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";
import { useEffect, useState } from "react";

export function ClusteringDropDown({
  selectedClustering,
  setSelectedClustering,
  clusterings,
  selectedClusteringName,
}: {
  selectedClustering: Clustering | undefined;
  setSelectedClustering: (value: Clustering | undefined) => void;
  clusterings: Clustering[] | undefined;
  selectedClusteringName: string | undefined;
}) {
  const [refresh, setRefresh] = useState(false);

  useEffect(() => {
    setRefresh(!refresh);
  }, [JSON.stringify(clusterings)]);

  return (
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
              ? formatUnixTimestampToLiteralDatetime(clusterings[0].created_at)
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
                (refresh || !refresh) &&
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
  );
}
