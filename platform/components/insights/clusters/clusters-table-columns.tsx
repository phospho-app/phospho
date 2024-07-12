import { Button } from "@/components/ui/button";
import { Cluster } from "@/models/models";
import { ColumnDef } from "@tanstack/react-table";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export function getColumns() {
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

    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const cluster_id = row.original.id;
        // Match the task object with this key
        // Handle undefined edge case
        if (!cluster_id) return <></>;
        return (
          <Link
            href={`/org/insights/clusters/${encodeURIComponent(cluster_id)}`}
          >
            <Button variant="ghost" size="icon">
              <ChevronRight />
            </Button>
          </Link>
        );
      },
      size: 10,
      minSize: 10,
      maxSize: 10,
    },
  ];

  return columns;
}
