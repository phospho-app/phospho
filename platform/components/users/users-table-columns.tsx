import { InteractiveDatetime } from "@/components/interactive-datetime";
import {
  EventBadge,
  EventDetectionDescription,
} from "@/components/label-events";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { authFetcher } from "@/lib/fetcher";
import { Event, Project, UserMetadata } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown, ChevronRight, Sparkles } from "lucide-react";
import useSWR from "swr";

export function useColumns() {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  // Create the columns for the data table
  const columns: ColumnDef<UserMetadata>[] = [
    // id
    {
      header: () => {
        return <>User ID</>;
      },
      accessorKey: "user_id",
      cell: ({ row }) => {
        return (
          <HoverCard openDelay={0} closeDelay={0}>
            <HoverCardTrigger asChild>
              <div
                className="h-10 flex items-center hover:text-green-500"
                onClick={(event) => {
                  event.stopPropagation();
                  navigator.clipboard.writeText(row.original.user_id);
                }}
              >
                {row.original.user_id}
              </div>
            </HoverCardTrigger>
            <HoverCardContent
              align="start"
              className="text-xs text-muted-foreground"
            >
              Copy
            </HoverCardContent>
          </HoverCard>
        );
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
            Nb messages
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
            Avg. success rate
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
            Avg. session length
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "avg_session_length",
      cell: (row) => {
        const output = row.getValue() as number;
        const roundedOutput = Math.round(output * 100) / 100;
        return roundedOutput;
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
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            First message
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "first_message_ts",
      cell: (row) => {
        const value = row.getValue();
        if (typeof value !== "number") return <></>;
        return <InteractiveDatetime timestamp={value} />;
      },
    },
    {
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Last message
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
      accessorKey: "last_message_ts",
      cell: (row) => {
        const value = row.getValue();
        if (typeof value !== "number") return <></>;
        return <InteractiveDatetime timestamp={value} />;
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
      header: () => {
        return (
          <div className="flex flex-row">
            <Sparkles className="h-4 w-4 mr-1 text-green-500" />
            Events
          </div>
        );
      },
      accessorKey: "events",
      cell: (row) => {
        return (
          <>
            {(row.getValue() as Event[]).map((event: Event) => {
              // Find the event definition for this event based on the event_name and selectedProject.settings.events
              const eventDefinition =
                selectedProject?.settings?.events[event.event_name];

              if (!eventDefinition) return <></>;

              return (
                <HoverCard openDelay={0} closeDelay={0} key={event.id}>
                  <HoverCardTrigger asChild>
                    <EventBadge key={event.id} event={event} />
                  </HoverCardTrigger>
                  <HoverCardContent>
                    <EventDetectionDescription
                      event={event}
                      eventDefinition={eventDefinition}
                    />
                  </HoverCardContent>
                </HoverCard>
              );
            })}
          </>
        );
      },
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
          <Button variant="ghost" size="icon">
            <ChevronRight />
          </Button>
        );
      },
      size: 10,
      minSize: 10,
      maxSize: 10,
    },
  ];

  return columns;
}
