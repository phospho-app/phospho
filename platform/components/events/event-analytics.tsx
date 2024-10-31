import { TasksTable } from "@/components/tasks/tasks-table";
import { Button } from "@/components/ui/button";
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
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import React from "react";
import useSWR from "swr";

function EventAnalytics({ eventId }: { eventId: string }) {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const { data: selectedProject }: { data: Project | undefined } = useSWR(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );

  // In the Record, find the event with the same id as the one passed in the props
  const eventsAsArray = Object.entries(selectedProject?.settings?.events || {});
  const event = eventsAsArray.find(([, event]) => event.id === eventId)?.[1];

  const { data: totalNbDetections } = useSWR(
    project_id
      ? [
          `/api/explore/${encodeURI(project_id)}/aggregated/events/${encodeURI(eventId)}`,
          accessToken,
          "total_nb_events",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_events"],
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: binaryMetrics } = useSWR(
    project_id && event?.score_range_settings?.score_type === "confidence"
      ? [
          `/api/explore/${encodeURI(project_id)}/aggregated/events/${encodeURI(eventId)}`,
          accessToken,
          "f1_score_binary",
          "precision_binary",
          "recall_binary",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["f1_score_binary", "precision_binary", "recall_binary"],
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: classificationMetrics } = useSWR(
    project_id && event?.score_range_settings?.score_type === "category"
      ? [
          `/api/explore/${encodeURI(project_id)}/aggregated/events/${encodeURI(eventId)}`,
          accessToken,
          "f1_score_multiclass",
          "precision_multiclass",
          "recall_multiclass",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: [
          "f1_score_multiclass",
          "precision_multiclass",
          "recall_multiclass",
        ],
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: regressionMetrics } = useSWR(
    project_id && event?.score_range_settings?.score_type === "range"
      ? [
          `/api/explore/${encodeURI(project_id)}/aggregated/events/${encodeURI(eventId)}`,
          accessToken,
          "mean_squared_error",
          "r_squared",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["mean_squared_error", "r_squared"],
      }),
    {
      keepPreviousData: true,
    },
  );

  if (!project_id || !selectedProject) {
    return <></>;
  }

  return (
    <div className="flex flex-col space-y-4 mt-4">
      <div>
        <h4 className="text-xl font-bold">
          Event : &quot;{event?.event_name}&quot;
        </h4>
      </div>
      {/* if the score type is range but there is not enough data to compute the scores, we display a not enough feedback message */}
      {!regressionMetrics?.mean_squared_error &&
        event?.score_range_settings?.score_type == "range" && (
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
                          Give us more feedback to compute the Mean Squared
                          Error and the R-squared.
                        </p>
                      </CardDescription>
                    </div>

                    <Link href="/org/transcripts/sessions">
                      <Button variant="default">
                        Give feedback
                        <ChevronRight className="ml-2" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </>
        )}
      {/* if the score type is confidence or category but there is not enough data to compute the scores, we display a not enough feedback message */}
      {!classificationMetrics?.f1_score_multiclass &&
        event?.score_range_settings?.score_type === "category" && (
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
                          Label more data to compute the F1-score, Precision and
                          Recall.
                        </p>
                      </CardDescription>
                    </div>

                    <Link href="/org/transcripts/sessions">
                      <Button variant="default">
                        Label data
                        <ChevronRight className="ml-2" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </>
        )}
      {!binaryMetrics?.f1_score_binary &&
        event?.score_range_settings?.score_type === "confidence" && (
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
                          Label more data to compute the F1-score, Precision and
                          Recall.
                        </p>
                      </CardDescription>
                    </div>

                    <Link href="/org/transcripts/sessions">
                      <Button variant="default">
                        Label data
                        <ChevronRight className="ml-2" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </>
        )}
      {/* In any case we display the Total number of descriptions card */}
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardDescription>Total Nb of detections</CardDescription>
            </CardHeader>
            <CardContent>
              {totalNbDetections?.total_nb_events && (
                <p className="text-xl">{totalNbDetections?.total_nb_events}</p>
              )}
              {totalNbDetections?.total_nb_events === undefined && <p>...</p>}
            </CardContent>
          </Card>
          {/* If we have enough data to compute the scores, we display the F1-score, Precision and Recall cards */}
          {event?.score_range_settings?.score_type === "category" && (
            <>
              <Card>
                <CardHeader>
                  <CardDescription>F1-score</CardDescription>
                </CardHeader>
                <CardContent>
                  {classificationMetrics?.f1_score_multiclass && (
                    <p className="text-xl">
                      {classificationMetrics?.f1_score_multiclass.toFixed(2)}
                    </p>
                  )}
                  {classificationMetrics?.f1_score_multiclass === undefined && (
                    <p className="text-xl"> ... </p>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>Precision</CardDescription>
                </CardHeader>
                <CardContent>
                  {classificationMetrics?.f1_score_multiclass && (
                    <p className="text-xl">
                      {classificationMetrics?.precision_multiclass.toFixed(2)}
                    </p>
                  )}
                  {classificationMetrics?.f1_score_multiclass === undefined && (
                    <p className="text-xl">...</p>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>Recall</CardDescription>
                </CardHeader>
                <CardContent>
                  {classificationMetrics?.f1_score_multiclass && (
                    <p className="text-xl">
                      {classificationMetrics?.recall_multiclass.toFixed(2)}
                    </p>
                  )}
                  {classificationMetrics?.f1_score_multiclass === undefined && (
                    <p className="text-xl">...</p>
                  )}
                </CardContent>
              </Card>
            </>
          )}
          {event?.score_range_settings?.score_type === "confidence" && (
            <>
              <Card>
                <CardHeader>
                  <CardDescription>F1-score</CardDescription>
                </CardHeader>
                <CardContent>
                  {binaryMetrics?.f1_score_binary && (
                    <p className="text-xl">
                      {binaryMetrics?.f1_score_binary.toFixed(2)}
                    </p>
                  )}
                  {binaryMetrics?.f1_score_binary === undefined && (
                    <p className="text-xl"> ... </p>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>Precision</CardDescription>
                </CardHeader>
                <CardContent>
                  {binaryMetrics?.f1_score_binary && (
                    <p className="text-xl">
                      {binaryMetrics?.precision_binary.toFixed(2)}
                    </p>
                  )}
                  {binaryMetrics?.f1_score_binary === undefined && (
                    <p className="text-xl">...</p>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>Recall</CardDescription>
                </CardHeader>
                <CardContent>
                  {binaryMetrics?.f1_score_binary && (
                    <p className="text-xl">
                      {binaryMetrics?.recall_binary.toFixed(2)}
                    </p>
                  )}
                  {binaryMetrics?.f1_score_binary === undefined && (
                    <p className="text-xl">...</p>
                  )}
                </CardContent>
              </Card>
            </>
          )}
          {/* If we have enough data to compute the scores, we display the Mean Square Error and the R-squared */}
          {event?.score_range_settings?.score_type == "range" && (
            <>
              <Card>
                <CardHeader>
                  <CardDescription>Mean Squared Error</CardDescription>
                </CardHeader>
                <CardContent>
                  {regressionMetrics?.mean_squared_error && (
                    <p className="text-xl">
                      {regressionMetrics?.mean_squared_error.toFixed(2)}
                    </p>
                  )}
                  {regressionMetrics?.mean_squared_error === undefined && (
                    <p className="text-xl">...</p>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardDescription>R-squared</CardDescription>
                </CardHeader>
                <CardContent>
                  {regressionMetrics?.mean_squared_error && (
                    <p className="text-xl">
                      {regressionMetrics?.r_squared.toFixed(2)}
                    </p>
                  )}
                  {regressionMetrics?.mean_squared_error === undefined && (
                    <p className="text-xl">...</p>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
      {event && (
        <TasksTable forcedDataFilters={{ event_name: [event.event_name] }} />
      )}
    </div>
  );
}

export default EventAnalytics;
