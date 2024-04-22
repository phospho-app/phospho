import { authFetcher } from "@/lib/fetcher";
import { Event, UserMetadata } from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronDown,
  ChevronRight,
  FilterX,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import useSWR from "swr";

import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";

export function getColumns() {
  const router = useRouter();

  let uniqueEventNamesInData: string[] = [];
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const { data: uniqueEvents } = useSWR(
    project_id
      ? [`/api/projects/${project_id}/unique-events`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  if (project_id && uniqueEvents?.events) {
    uniqueEventNamesInData = Array.from(
      new Set(
        uniqueEvents.events.map((event: Event) => event.event_name as string),
      ),
    );
  }

  // Create the columns for the data table
  const columns: ColumnDef<UserMetadata>[] = [
    // id
    {
      filterFn: (row, id, filterValue) => {
        // if is in the filtervalue
        if (filterValue === null) return true;
        return filterValue.includes(row.original.user_id);
      },
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            User ID
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "user_id",
      cell: ({ row }) => {
        return row.original.user_id;
      },
      // enableHiding: true,
    },
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Nb tasks
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "nb_tasks",
      cell: (row) => {
        const output = row.getValue();
        return output;
      },
    },
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Avg Success Rate
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "avg_success_rate",
      cell: (row) => {
        const output = Math.round((row.getValue() as number) * 100) / 100;
        return output;
      },
    },
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Avg Session Length
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "avg_session_length",
      cell: (row) => {
        const output = row.getValue();
        return output;
      },
    },
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Nb Tokens
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "total_tokens",
      cell: (row) => {
        const output = row.getValue();
        return output;
      },
    },
    {
      filterFn: (row, id, filterValue) => {
        if (filterValue === null) return true;
        // If the filter value is not null, return whether
        // the filterValue is in [event.event_name] array
        return (row.original.events as Event[]).some(
          (event) => event.event_name === filterValue,
        );
      },
      header: ({ column }) => {
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                onClick={() =>
                  column.toggleSorting(column.getIsSorted() === "asc")
                }
              >
                <Sparkles className="h-4 w-4 mr-1 text-green-500" />
                Events
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              {uniqueEventNamesInData.map((eventName) => (
                <DropdownMenuItem
                  key={eventName}
                  onClick={() => column.setFilterValue(eventName)}
                >
                  {eventName}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                key="event_clear"
                onClick={() => column.setFilterValue(null)}
              >
                <FilterX className="h-4 w-4 mr-1" />
                Clear
              </DropdownMenuItem>
            </DropdownMenuContent>
            <DropdownMenu />
          </DropdownMenu>
        );
      },
      accessorKey: "events",
      cell: (row) => (
        <span>
          {(row.getValue() as Event[]).map((event: Event) => (
            <Badge
              key={event.id}
              variant="secondary"
              className="ml-2 mt-1 mb-1"
            >
              {event.event_name as string}
            </Badge>
          ))}
        </span>
      ),
    },
    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const user_id = row.original.user_id;
        // Match the task object with this key
        // Handle undefined edge case
        if (!user_id) return <></>;
        return (
          <Link href={`/org/users/${encodeURIComponent(user_id)}`}>
            <ChevronRight />
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
