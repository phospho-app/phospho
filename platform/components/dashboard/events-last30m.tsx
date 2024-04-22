"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { getCountsPerEvent } from "@/lib/events_data";
import { authFetcher } from "@/lib/fetcher";
import { Event } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";
import useSWR from "swr";

interface EventsLast7DaysProps {
  project_id: string;
}

const EventsLast30m: React.FC<EventsLast7DaysProps> = ({ project_id }) => {
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

  // Fetch events from the API
  const { data: eventsLast30mData } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/events`,
          accessToken,
          JSON.stringify({
            created_at_start: Math.floor(Date.now() / 1000) - 30 * 60,
          }),
        ]
      : null,
    ([url, accessToken, body]) =>
      authFetcher(url, accessToken, "POST", {
        created_at_start: Math.floor(Date.now() / 1000) - 30 * 60,
      }),
    {
      keepPreviousData: true,
    },
  );
  const eventsLast30m = eventsLast30mData?.events;

  const countPerEvent = getCountsPerEvent(
    eventsLast30m,
    uniqueEventNamesInData,
  );

  return (
    <div>
      {eventsLast30m ? (
        <Skeleton className="h-[250px]" />
      ) : (
        <div>
          {countPerEvent.map((eventCount) => (
            <div
              className="flex justify-between mx-4"
              key={eventCount.event_name}
            >
              <p>{eventCount.event_name}</p>
              <p>{eventCount.total}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EventsLast30m;
