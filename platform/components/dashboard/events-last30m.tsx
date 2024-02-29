"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { getCountsPerEvent } from "@/lib/events_data";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";

interface EventsLast7DaysProps {
  project_id: string;
}

const EventsLast30m: React.FC<EventsLast7DaysProps> = ({ project_id }) => {
  const uniqueEventNames = dataStateStore((state) => state.uniqueEventNames);

  const { accessToken } = useUser();
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [eventLastMins, setEventLastMins] = useState<any[]>([]);

  // Fetch events from the API
  useEffect(() => {
    (async () => {
      const authorization_header = "Bearer " + accessToken;
      const headers = {
        Authorization: authorization_header || "", // Use an empty string if authorization_header is null
        "Content-Type": "application/json",
      };
      const response = await fetch(`/api/explore/${project_id}/events`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
          // Generate a UNIX timestamp for the last 30min
          created_at_start: Math.floor(Date.now() / 1000) - 30 * 60,
        }),
      });
      const response_json = await response.json();
      console.log("fetched_events_30_min", response_json.events);
      setEventLastMins(response_json.events);
      setIsLoading(false);
    })();
  }, [project_id]);

  const countPerEvent = getCountsPerEvent(eventLastMins, uniqueEventNames);

  return (
    <div>
      {isLoading ? (
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
