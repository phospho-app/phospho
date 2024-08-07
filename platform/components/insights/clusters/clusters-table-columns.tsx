import { Button } from "@/components/ui/button";
import { Cluster } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { ColumnDef } from "@tanstack/react-table";
import { ChevronRight, Pickaxe } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export function getColumns({
  setSheetOpen,
}: {
  setSheetOpen: (value: boolean) => void;
}) {
  const router = useRouter();

  // Create the columns for the data table
  const columns: ColumnDef<Cluster>[] = [
    // id
    {
      header: ({ column }) => {
        return <></>;
      },
      accessorKey: "id",
      cell: ({ row }) => {
        return <></>;
      },
      enableHiding: true,
      size: 10,
      minSize: 10,
      maxSize: 10,
    },
    // size
    {
      header: "Size",
      accessorKey: "size",
      cell: ({ row }) => {
        return <>{row.original.size}</>;
      },
    },
    // name
    {
      header: "Name",
      accessorKey: "name",
      cell: ({ row }) => {
        return <>{row.original.name}</>;
      },
    },
    // description
    {
      header: "Description",
      accessorKey: "description",
      cell: ({ row }) => {
        return <>{row.original.description}</>;
      },
    },
    // view
    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const cluster_id = row.original.id;
        const clustering_id = row.original.clustering_id;
        // Match the task object with this key
        // Handle undefined edge case
        const dataFilters = navigationStateStore((state) => state.dataFilters);
        const setDataFilters = navigationStateStore(
          (state) => state.setDataFilters,
        );

        if (!cluster_id) return <></>;
        return (
          <div>
            <Button
              variant="ghost"
              size="icon"
              onClick={(mouseEvent) => {
                mouseEvent.stopPropagation();
                setSheetOpen(true);
                const currentClustersIds = dataFilters.clusters_ids ?? [];
                setDataFilters({
                  ...dataFilters,
                  clustering_id: clustering_id,
                  clusters_ids: [cluster_id],
                });
              }}
            >
              <Pickaxe className="w-6 h-6" />
            </Button>
            <Link
              href={`/org/insights/clusters/${encodeURIComponent(cluster_id)}`}
            >
              <Button variant="ghost" size="icon">
                <ChevronRight className="w-6 h-6" />
              </Button>
            </Link>
          </div>
        );
      },
      size: 10,
      minSize: 10,
      maxSize: 10,
    },
  ];

  return columns;
}
