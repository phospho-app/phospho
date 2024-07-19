import ComingSoon from "@/components/coming-soon";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import useSWR from "swr";

function EventAnalytics({ eventId }: { eventId: string }) {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  const eventFilters = {
    // created_at_start: dateRange?.created_at_start,
    // created_at_end: dateRange?.created_at_end,
  };

  const { data: totalNbDetections } = useSWR(
    project_id
      ? [
        `/api/explore/${encodeURI(project_id)}/aggregated/events/${encodeURI(eventId)}`,
        accessToken,
        "total_nb_events",
        JSON.stringify(eventFilters),
      ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_events"],
        filters: eventFilters,
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: F1Score } = useSWR(
    project_id
      ? [
        `/api/explore/${encodeURI(project_id)}/aggregated/events/${encodeURI(eventId)}`,
        accessToken,
        "f1_score",
        JSON.stringify(eventFilters),
      ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["f1_score"],
        filters: eventFilters,
      }),
    {
      keepPreviousData: true,
    },
  );

  if (!project_id || !selectedProject) {
    return <></>;
  }

  // In the Record, find the event with the same id as the one passed in the props
  const eventsAsArray = Object.entries(selectedProject.settings?.events || {});
  const event = eventsAsArray.find(([, event]) => event.id === eventId)?.[1];

  console.log(totalNbDetections);

  return (
    <div className="space-y-2">
      <ComingSoon />
      <div className="mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Total Nb of detections</CardDescription>
              </CardHeader>
              <CardContent>
                {(totalNbDetections?.total_nb_events === undefined && (
                  <p>...</p>
                )) || (
                    <p className="text-xl">
                      {totalNbDetections?.total_nb_events}
                    </p>
                  )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>F1-score</CardDescription>
              </CardHeader>
              <CardContent>
                {(F1Score?.f1_score === undefined && (
                  <p>...</p>
                )) || (
                    <p className="text-xl">
                      {F1Score?.f1_score}
                    </p>
                  )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardDescription>Precision</CardDescription>
              </CardHeader>
              <CardContent>
                {(F1Score?.precision === undefined && (
                  <p>...</p>
                )) || (
                    <p className="text-xl">
                      {F1Score?.precision}
                    </p>
                  )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardDescription>Recall</CardDescription>
              </CardHeader>
              <CardContent>
                {(F1Score?.recall === undefined && (
                  <p>...</p>
                )) || (
                    <p className="text-xl">
                      {F1Score?.recall}
                    </p>
                  )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EventAnalytics;
