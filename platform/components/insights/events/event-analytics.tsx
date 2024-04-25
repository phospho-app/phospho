import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import useSWR from "swr";

interface EventAnalyticsProps {
  eventId: string;
}

const EventAnalytics: React.FC<EventAnalyticsProps> = (event) => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const sessionsColumnsFilters = navigationStateStore(
    (state) => state.sessionsColumnsFilters,
  );
  const dateRange = navigationStateStore((state) => state.dateRange);

  let eventFilter: string | null = null;
  for (let filter of sessionsColumnsFilters) {
    if (
      filter.id === "events" &&
      (typeof filter.value === "string" || filter.value === null)
    ) {
      eventFilter = filter.value;
    }
  }

  const sessionsFilters = {
    event_name: eventFilter,
    created_at_start: dateRange?.created_at_start,
    created_at_end: dateRange?.created_at_end,
  };

  if (!project_id) {
    return <></>;
  }

  const { data: totalNbSessionsData } = useSWR(
    [
      `/api/explore/${encodeURI(project_id)}/${encodeURI(event.eventId)}/aggregated/detections`,
      accessToken,
      "total_nb_events",
      JSON.stringify(sessionsFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_events"],
        sessions_filter: sessionsFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  console.log(totalNbSessionsData);
  const NbEventsDetected = totalNbSessionsData?.total_nb_events;

  return (
    <div>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Total Nb of detections</CardDescription>
              </CardHeader>
              <CardContent>
                {(!NbEventsDetected && <p>...</p>) || (
                  <p className="text-xl">{NbEventsDetected}</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventAnalytics;
