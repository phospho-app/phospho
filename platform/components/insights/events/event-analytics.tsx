import ComingSoon from "@/components/coming-soon";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { Project } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { Tag } from "lucide-react";
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
    <>
      <div>
        <h4 className="text-xl font-bold">Event : "{event?.event_name}"</h4>
      </div>
      {/* if the score type is not confidence, we display a coming soon message */}
      {event?.score_range_settings?.score_type != "confidence" && (
        <div>
          <ComingSoon />
        </div>
      )}
      {/* if the score type is confidence but there is not enough data to compute the scores, we display a not enough feedback message */}
      {(!F1Score?.f1_score) && (event?.score_range_settings?.score_type == "confidence") && (
        <>
          <Card className="bg-secondary">
            <CardHeader>
              <div className="flex">
                <Tag className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />

                <div className="flex flex-grow justify-between items-center">
                  <div>
                    <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                      <div className="flex flex-row place-items-center">
                        Unlock event metrics !
                      </div>
                    </CardTitle>
                    <CardDescription className="flex justify-between flex-col text-muted-foreground space-y-0.5">
                      <p>
                        Give us more feedback to compute the F1-score, Precision and Recall.
                      </p>
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
          </Card></>
      )}
      {/* In any case we display the Total number of descriptions card */}
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
          {/* If we have enough data to compute the scores, we display the F1-score, Precision and Recall cards */}
          {event?.score_range_settings?.score_type == "confidence" && (
            <>
              <Card>
                <CardHeader>
                  <CardDescription>F1-score</CardDescription>
                </CardHeader>
                <CardContent>
                  {(F1Score?.f1_score && (
                    <p className="text-xl">
                      {F1Score?.f1_score.toFixed(2)}
                    </p>
                  )) || (!F1Score?.f1_score && (
                    <p className="text-xl"> ... </p>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>Precision</CardDescription>
                </CardHeader>
                <CardContent>
                  {(F1Score?.f1_score && (
                    <p className="text-xl">
                      {F1Score?.precision.toFixed(2)}
                    </p>
                  )) || (!F1Score?.f1_score && (
                    <p className="text-xl">
                      ...
                    </p>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>Recall</CardDescription>
                </CardHeader>
                <CardContent>
                  {(F1Score?.f1_score && (
                    <p className="text-xl">
                      {F1Score?.recall.toFixed(2)}
                    </p>
                  )) || (!F1Score?.f1_score && (
                    <p className="text-xl">
                      ...
                    </p>
                  ))}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>


    </>
  );
}

export default EventAnalytics;
