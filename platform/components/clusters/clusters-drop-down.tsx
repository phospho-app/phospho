import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Clustering } from "@/models/models";

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
  return (
    <div className="flex flex-row gap-x-2 items-center">
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
          selectedClustering ? selectedClustering.id : "no-clustering"
        }
      >
        <SelectTrigger className="min-w-[20rem]">
          <div>
            {selectedClusteringName && <span>{selectedClusteringName}</span>}
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
                    formatUnixTimestampToLiteralDatetime(clustering.created_at)}
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
  );
}
