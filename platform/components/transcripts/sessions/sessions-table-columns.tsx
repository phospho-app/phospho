import {
  AddEventDropdownForSessions,
  InteractiveEventBadgeForSessions,
} from "@/components/label-events";
import { EvalSettings } from "@/components/transcripts/settings/eval-settings";
import { RunEventsSettings } from "@/components/transcripts/settings/events-settings";
import { SentimentSettings } from "@/components/transcripts/settings/sentiment-settings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { authFetcher } from "@/lib/fetcher";
import { formatUnixTimestampToLiteralDatetime } from "@/lib/time";
import { getLanguageLabel } from "@/lib/utils";
import { Event, EventDefinition, SessionWithEvents } from "@/models/models";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronRight, Sparkles } from "lucide-react";
import Link from "next/link";
import React from "react";
import { KeyedMutator } from "swr";
import useSWR from "swr";

export function getColumns({
  mutateSessions,
  setSheetOpen,
  setSheetToOpen,
  setEventDefinition,
}: {
  mutateSessions: KeyedMutator<SessionWithEvents[]>;
  setSheetOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setSheetToOpen: React.Dispatch<React.SetStateAction<string | null>>;
  setEventDefinition: React.Dispatch<
    React.SetStateAction<EventDefinition | null>
  >;
}): ColumnDef<SessionWithEvents>[] {
  const project_id = navigationStateStore((state) => state.project_id);
  const { accessToken } = useUser();

  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const events = selectedProject?.settings?.events || {};
  const eventArray = Object.entries(events);

  // Create the columns for the data table
  const columns: ColumnDef<SessionWithEvents>[] = [
    // id
    // {
    //   filterFn: (row, id, filterValue) => {
    //     // if is in the filtervalue
    //     if (filterValue === null) return true;
    //     return filterValue.includes(row.original.id);
    //   },
    //   header: ({ column }) => {
    //     return <></>;
    //   },
    //   accessorKey: "id",
    //   cell: ({ row }) => {
    //     return <></>;
    //   },
    //   enableHiding: true,
    // },
    // Date
    {
      header: ({ column }) => {
        return (
          <div className="flex flex-row items-center justify-between space-x-2">
            Date
            <Button
              variant="ghost"
              size="icon"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
            >
              {
                // Show the sorting icon based on the current sorting state
                column.getIsSorted() === "desc" ? (
                  <ArrowUp className="h-4 w-4" />
                ) : (
                  <ArrowDown className="h-4 w-4" />
                )
              }
            </Button>
          </div>
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
    // Eval
    {
      header: ({ column }) => {
        return (
          <div className="flex items-center space-x-2 justify-between">
            <div className="flex items-center">
              <Sparkles className="h-4 w-4 mr-1 text-green-500" />
              Eval
            </div>
            <EvalSettings />
          </div>
        );
      },
      accessorKey: "stats.most_common_flag",
      cell: (row) => {
        return (
          <div>
            <Badge
              variant={
                (row.getValue() as string) === "success"
                  ? "secondary"
                  : (row.getValue() as string) === "failure"
                    ? "destructive"
                    : "secondary"
              }
              className="hover:border-green-500"
            >
              {row.getValue() as string}
            </Badge>
          </div>
        );
      },
    },
    // Events
    {
      header: () => {
        return (
          <div className="flex items-center space-x-2 justify-between">
            <div className="flex flex-row items-center space-x-1">
              <Sparkles className="h-4 w-4 text-green-500" />
              <div>Events</div>
            </div>
            <RunEventsSettings
              eventArray={eventArray}
              setSheetOpen={setSheetOpen}
              setSheetToOpen={setSheetToOpen}
              setEventDefinition={setEventDefinition}
            />
          </div>
        );
      },
      accessorKey: "events",
      cell: (row) => (
        <div className="group flex items-center justify-between space-y-1">
          <div className="flex flex-wrap items-center justify-center">
            {(row.getValue() as Event[]).map((event: Event) => {
              return (
                <InteractiveEventBadgeForSessions
                  key={`${event.event_name}_session_${row.row.original.id}`}
                  event={event}
                  session={row.row.original as SessionWithEvents}
                  setSession={(session: SessionWithEvents) => {
                    // Update the session in the table
                    mutateSessions((data: any) => {
                      data.sessions = data.sessions.map(
                        (existingSession: SessionWithEvents) => {
                          if (existingSession.id === session.id) {
                            return session;
                          }
                          return existingSession;
                        },
                      );
                      return data;
                    });
                  }}
                />
              );
            })}
            <AddEventDropdownForSessions
              key={`add_event_session_${row.row.original.id}`}
              session={row.row.original as SessionWithEvents}
              setSession={(session: SessionWithEvents) => {
                mutateSessions((data: any) => {
                  data.sessions = data.sessions.map(
                    (existingSession: SessionWithEvents) => {
                      if (existingSession.id === session.id) {
                        return session;
                      }
                      return existingSession;
                    },
                  );
                  return data;
                });
              }}
              setSheetOpen={setSheetOpen}
              setSheetToOpen={setSheetToOpen}
            />
          </div>
        </div>
      ),
    },
    // Language
    {
      header: ({ column }) => {
        return (
          <div className="flex items-center space-x-2 justify-between">
            <div className="flex items-center">
              <Sparkles className="h-4 w-4 mr-1 text-green-500" />
              Language
            </div>
          </div>
        );
      },
      accessorKey: "stats.most_common_language",
      cell: (row) => (
        <HoverCard openDelay={80} closeDelay={30}>
          <HoverCardTrigger>
            <Badge variant={"secondary"}>{row.getValue() as string}</Badge>
          </HoverCardTrigger>
          <HoverCardContent side="top" className="text-sm text-center">
            {getLanguageLabel(row.getValue() as string)}
          </HoverCardContent>
        </HoverCard>
      ),
      maxSize: 10,
    },
    {
      header: () => {
        return (
          <div className="flex justify-between items-center space-x-2">
            <div className="flex flex-row items-center">
              <Sparkles className="h-4 w-4 mr-1 text-green-500" />
              Sentiment
            </div>
            <SentimentSettings />
          </div>
        );
      },
      accessorKey: "stats.most_common_sentiment_label",
      cell: (row) => {
        const sentiment_label = row.getValue() as string;
        return (
          <div>
            <HoverCard openDelay={80} closeDelay={30}>
              <HoverCardTrigger>
                <Badge
                  className={
                    sentiment_label == "positive"
                      ? "border-green-500"
                      : sentiment_label == "negative"
                        ? "border-red-500"
                        : ""
                  }
                  variant={"secondary"}
                >
                  {sentiment_label}
                </Badge>
              </HoverCardTrigger>
              <HoverCardContent side="top" className="text-sm text-left w-50">
                <h2 className="font-bold">Sentiment label</h2>
                <p>Automatic sentiment analysis of the Task input</p>
              </HoverCardContent>
            </HoverCard>
          </div>
        );
      },
      maxSize: 10,
    },
    // Session Length
    {
      header: ({ column }) => {
        return (
          <div className="flex flex-row justify-between space-x-2 items-center">
            Session Length
            <Button
              variant="ghost"
              size="icon"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
            >
              {
                // Show the sorting icon based on the current sorting state
                column.getIsSorted() === "desc" ? (
                  <ArrowUp className="h-4 w-4" />
                ) : (
                  <ArrowDown className="h-4 w-4" />
                )
              }
            </Button>
          </div>
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
          <Popover>
            <PopoverTrigger
              onClick={(mouseEvent) => {
                mouseEvent.stopPropagation();
              }}
              className="text-left"
            >
              {output
                ? output.length > 50
                  ? output.substring(0, 50) + "..."
                  : output
                : "-"}
            </PopoverTrigger>
            <PopoverContent className="text-sm">
              <h1 className="text-m">Latest message in the session:</h1>
              <br></br>
              {output}
            </PopoverContent>
          </Popover>
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
          <Link
            href={`/org/transcripts/sessions/${encodeURIComponent(session.id)}`}
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
