import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { authFetcher } from "@/lib/fetcher";
import { Event, Topic, UserMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import {
  ArrowUpDown,
  ChevronDown,
  ChevronRight,
  FilterX,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useSWR from "swr";

export function getColumns() {
  const router = useRouter();

  // Create the columns for the data table
  const columns: ColumnDef<Topic>[] = [
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
        const topic_id = row.original.id;
        // Match the task object with this key
        // Handle undefined edge case
        if (!topic_id) return <></>;
        return (
          <Link href={`/org/insights/topics/${encodeURIComponent(topic_id)}`}>
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
