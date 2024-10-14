import { InteractiveDatetime } from "@/components/interactive-datetime";
import {
  AddEventDropdownForSessions,
  InteractiveEventBadgeForSessions,
} from "@/components/label-events";
import { RunEventsSettings } from "@/components/settings/events-settings";
import { SentimentSettings } from "@/components/settings/sentiment-settings";
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
import { getLanguageLabel } from "@/lib/utils";
import { Event, EventDefinition, SessionWithEvents } from "@/models/models";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ColumnDef } from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ChevronRight,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import React from "react";
import { KeyedMutator, useSWRConfig } from "swr";
import useSWR from "swr";
import { ScopedMutator } from "swr/dist/_internal";

async function flagSession({
  session_id,
  flag,
  accessToken,
  project_id,
  mutateSessions,
  mutate,
}: {
  session_id: string;
  flag: string;
  accessToken?: string;
  project_id?: string | null;
  mutateSessions: KeyedMutator<SessionWithEvents[]>;
  mutate: ScopedMutator;
}) {
  if (!accessToken) return;
  if (!project_id) return;

  await fetch(`/api/sessions/${session_id}/human-eval`, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + accessToken,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      human_eval: flag,
    }),
  });
  mutateSessions((data: SessionWithEvents[] | undefined) => {
    if (!data) {
      return data;
    }
    // Edit the Session with the same id
    data = data.map((session: SessionWithEvents) => {
      if (session.id === session_id) {
        session.stats.human_eval = flag;
      }
      return session;
    });
    return data;
  });
  // Invalidate this session
  mutate((key: string[]) => key[0] === `/api/sessions/${session_id}`);
}

export function useColumns({
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
  const { mutate } = useSWRConfig();

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
      cell: ({ row }) => {
        const created_at = row.original.created_at;
        return <InteractiveDatetime timestamp={created_at} />;
      },
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
            <PopoverContent className="text-sm overflow-y-auto max-h-[20rem]">
              {output &&
                output.split("\n").map((line, index) => (
                  <React.Fragment key={index}>
                    {line}
                    <br />
                    <br />
                  </React.Fragment>
                ))}
            </PopoverContent>
          </Popover>
        );
      },
    },
    {
      header: "Human evaluation",
      accessorKey: "stats.human_eval",
      cell: (row) => {
        const human_eval = row.getValue() as string | null; // asserting the type as string
        return (
          <div className="flex justify-center group">
            {human_eval && human_eval === "success" && (
              <ThumbsUp className="h-6 w-6 text-green-500" />
            )}{" "}
            {human_eval && human_eval === "failure" && (
              <ThumbsDown className="h-6 w-6 text-red-500" />
            )}{" "}
            {!human_eval && (
              <div className="flex space-x-2 invisible group group-hover:visible p-6">
                <ThumbsUp
                  className="h-6 w-6 text-green-500 cursor-pointer hover:fill-green-500"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    flagSession({
                      session_id: row.row.original.id,
                      flag: "success",
                      accessToken: accessToken,
                      project_id: project_id,
                      mutateSessions: mutateSessions,
                      mutate: mutate,
                    });
                  }}
                />
                <ThumbsDown
                  className="h-6 w-6 text-red-500 cursor-pointer hover:fill-red-500"
                  onClick={(mouseEvent) => {
                    mouseEvent.stopPropagation();
                    flagSession({
                      session_id: row.row.original.id,
                      flag: "failure",
                      accessToken: accessToken,
                      project_id: project_id,
                      mutateSessions: mutateSessions,
                      mutate: mutate,
                    });
                  }}
                />
              </div>
            )}
          </div>
        );
      },
    },
    // Language
    {
      header: () => {
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
          <div className="flex flex-wrap items-center justify-center w-full">
            {(row.getValue() as Event[]).map((event: Event) => {
              return (
                <InteractiveEventBadgeForSessions
                  key={`${event.event_name}_session_${row.row.original.id}`}
                  event={event}
                  session={row.row.original as SessionWithEvents}
                  setSession={(session: SessionWithEvents) => {
                    // Update the session in the table
                    mutateSessions(
                      (currentSessions: SessionWithEvents[] | undefined) => {
                        if (!currentSessions) return currentSessions;
                        currentSessions = currentSessions.map(
                          (existingSession: SessionWithEvents) => {
                            if (existingSession.id === session.id) {
                              return session;
                            }
                            return existingSession;
                          },
                        );
                        return currentSessions;
                      },
                    );
                    // Invalidate this session
                    mutate((key: string[]) =>
                      key[0].includes(`/api/sessions/${session.id}`),
                    );
                  }}
                />
              );
            })}
            <AddEventDropdownForSessions
              key={`add_event_session_${row.row.original.id}`}
              session={row.row.original as SessionWithEvents}
              setSession={(session: SessionWithEvents) => {
                mutateSessions(
                  (currentSessions: SessionWithEvents[] | undefined) => {
                    if (!currentSessions) return currentSessions;
                    return currentSessions.map((existingSession) => {
                      if (existingSession.id === session.id) {
                        return session;
                      }
                      return existingSession;
                    });
                  },
                );
                // Invalidate this session
                mutate((key: string[]) =>
                  key.includes(`/api/sessions/${session.id}`),
                );
              }}
              setSheetOpen={setSheetOpen}
              setSheetToOpen={setSheetToOpen}
            />
          </div>
        </div>
      ),
    },
    // Sentiment
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
                <span>Automatic sentiment analysis of the Task input</span>
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
            Length
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

    {
      header: "",
      accessorKey: "view",
      cell: ({ row }) => {
        const session = row.original;
        // Match the task object with this key
        // Handle undefined edge case
        if (!session) return <></>;
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
