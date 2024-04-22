import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { Event, SessionWithEvents } from "@/models/models";
import { navigationStateStore } from "@/store/store";
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
import useSWR from "swr";

export function getColumns() {
  const project_id = navigationStateStore((state) => state.project_id);
  const sessionsPagination = navigationStateStore(
    (state) => state.sessionsPagination,
  );
  const setSessionsPagination = navigationStateStore(
    (state) => state.setSessionsPagination,
  );

  const { accessToken } = useUser();
  let uniqueEventNamesInData: string[] = [];

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
  const columns: ColumnDef<SessionWithEvents>[] = [
    // id
    {
      filterFn: (row, id, filterValue) => {
        // if is in the filtervalue
        if (filterValue === null) return true;
        return filterValue.includes(row.original.id);
      },
      header: "",
      accessorKey: "id",
      cell: ({ row }) => {
        row.original.id;
      },
      enableHiding: true,
    },
    // Date
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Date
            {
              // Show the sorting icon based on the current sorting state
              column.getIsSorted() === "desc" ? (
                <ArrowUp className="ml-2 h-4 w-4" />
              ) : (
                <ArrowDown className="ml-2 h-4 w-4" />
              )
            }
          </Button>
        );
      },
      accessorKey: "created_at",
      cell: ({ row }) => (
        <span>
          {formatUnixTimestampToLiteralDatetime(
            Number(row.original.created_at),
          )}
        </span>
      ),
    },
    // Events
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
                  onClick={() => {
                    column.setFilterValue(eventName);
                    // reset the page to 0
                    setSessionsPagination({
                      ...sessionsPagination,
                      pageIndex: 0,
                    });
                  }}
                >
                  {eventName}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                key="event_clear"
                onClick={() => {
                  column.setFilterValue(null);
                  setSessionsPagination({
                    ...sessionsPagination,
                    pageIndex: 0,
                  });
                }}
              >
                <FilterX className="h-4 w-4 mr-1" />
                Clear filter
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
    // Session Length
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Session Length
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "session_length",
      cell: ({ row }) => (
        <span className="flex justify-center">
          {row.original.session_length}
        </span>
      ),
    },
    // Preview
    {
      header: "Preview",
      accessorKey: "preview",
      cell: (row) => {
        const output = row.getValue() as string; // asserting the type as string
        return (
          <span>
            {output
              ? output.length > 50
                ? output.substring(0, 50) + "..."
                : output
              : "-"}
          </span>
        );
      },
    },
    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const session = row.original;
        // Match the task object with this key
        // Handle undefined edge case
        if (!session) return <></>;
        return (
          <Link href={`/org/transcripts/sessions/${session.id}`}>
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
