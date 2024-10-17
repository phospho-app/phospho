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
import { Column, ColumnDef } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import useSWR from "swr";

function GenericHeader({
  columnName,
  column,
}: {
  columnName: string;
  column: Column<UserMetadata, unknown>;
}) {
  return (
    <div className="flex flex-row gap-x-2 items-center">
      {columnName}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        {column.getIsSorted() === false && <ArrowUpDown className="size-4" />}
        {column.getIsSorted() === "asc" && <ArrowUp className="size-4" />}
        {column.getIsSorted() === "desc" && <ArrowDown className="size-4" />}
      </Button>
    </div>
  );
}

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
      accessorKey: "nb_tasks",
      header: ({ column }) => {
        return <GenericHeader column={column} columnName="Nb tasks" />;
      },
      cell: (row) => {
        const output = row.getValue();
        return output;
      },
    },
    {
      accessorKey: "avg_success_rate",
      header: ({ column }) => {
        return <GenericHeader column={column} columnName="Avg. success rate" />;
      },
      cell: (row) => {
        const output = Math.round((row.getValue() as number) * 100) / 100;
        return output;
      },
    },
    {
      accessorKey: "avg_session_length",
      header: ({ column }) => {
        return (
          <GenericHeader column={column} columnName="Avg. session length" />
        );
      },
      cell: (row) => {
        const output = row.getValue() as number;
        const roundedOutput = Math.round(output * 100) / 100;
        return roundedOutput;
      },
    },
    {
      accessorKey: "total_tokens",
      header: ({ column }) => {
        return (
          <GenericHeader column={column} columnName="Total tokens earned" />
        );
      },
      cell: (row) => {
        const output = row.getValue();
        return output;
      },
    },
    {
      accessorKey: "first_message_ts",
      header: ({ column }) => {
        return <GenericHeader column={column} columnName="First message" />;
      },
      cell: (row) => {
        const value = row.getValue();
        if (typeof value !== "number") return <></>;
        return <InteractiveDatetime timestamp={value} />;
      },
    },
    {
      accessorKey: "last_message_ts",
      header: ({ column }) => {
        return <GenericHeader column={column} columnName="Last message" />;
      },
      cell: (row) => {
        const value = row.getValue();
        if (typeof value !== "number") return <></>;
        return <InteractiveDatetime timestamp={value} />;
      },
    },
    {
      accessorKey: "events",
      header: () => {
        return (
          <div className="flex flex-row gap-x-2 items-center">
            <Sparkles className="h-4 w-4 text-green-500" />
            Events
          </div>
        );
      },
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
