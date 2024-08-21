import { SendDataAlertDialog } from "@/components/callouts/import-data";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { AlertDialog } from "@radix-ui/react-alert-dialog";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import React from "react";
import { Bar, BarChart, Label, Pie, PieChart, XAxis, YAxis } from "recharts";
import useSWR from "swr";

interface NbSessions {
  day: string;
  date: string;
  nb_sessions: number;
}

interface LastClusteringComposition {
  name: string;
  description: string;
  size: number;
}

interface EventsRanking {
  event_name: string;
  nb_events: number;
}

interface SessionLengthHist {
  session_length: number;
  nb_sessions: number;
}

const chartConfig: ChartConfig = {};

const SessionsDataviz: React.FC = () => {
  const { accessToken } = useUser();

  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

  const [open, setOpen] = React.useState(false);

  const { data: totalNbSessionsData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/sessions`,
      accessToken,
      "total_nb_sessions",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_sessions"],
        filters: dataFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbSessions = totalNbSessionsData?.total_nb_sessions;

  const {
    data: nbSessionsPerDay,
  }: {
    data: NbSessions[] | undefined;
  } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/sessions`,
      accessToken,
      "nb_sessions_per_day",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["nb_sessions_per_day"],
        filters: dataFilters,
      }).then((data) => {
        if (!data.nb_sessions_per_day) {
          return [];
        }
        return data.nb_sessions_per_day?.map((element: NbSessions) => {
          const date = new Date(element.date);
          const date_array = date.toDateString().split(" ");
          const day = date_array[1] + " " + date_array[2];
          element.day = day;
          return element;
        });
      }),
    {
      keepPreviousData: true,
    },
  );

  const {
    data: lastClusteringComposition,
  }: { data: LastClusteringComposition[] | null | undefined } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "last_clustering_composition",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["last_clustering_composition"],
        filters: dataFilters,
      }).then((data) => {
        if (!data?.last_clustering_composition) {
          return null;
        }
        data?.last_clustering_composition?.sort(
          (a: LastClusteringComposition, b: LastClusteringComposition) =>
            b.size - a.size,
        );
        data?.last_clustering_composition?.forEach(
          (clustering: any, index: number) => {
            clustering.fill = graphColors[index % graphColors.length];
          },
        );
        return data?.last_clustering_composition;
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: dateLastClustering } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "date_last_clustering_timestamp",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["date_last_clustering_timestamp"],
        filters: dataFilters,
      }).then((data) => {
        if (!data?.date_last_clustering_timestamp) {
          return null;
        }
        console.log("dateLastClustering", data?.date_last_clustering_timestamp);
        const date_last_clustering = new Date(
          data?.date_last_clustering_timestamp * 1000,
        );
        console.log("dateLastClustering", date_last_clustering);
        return date_last_clustering.toDateString();
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: mostDetectedEventData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "most_detected_event",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["most_detected_event"],
        filters: dataFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const mostDetectedEvent: string | null | undefined =
    mostDetectedEventData?.most_detected_event;

  const { data: eventsRanking }: { data: EventsRanking[] | null | undefined } =
    useSWR(
      [
        `/api/explore/${project_id}/aggregated/tasks`,
        accessToken,
        "events_ranking",
        JSON.stringify(dataFilters),
      ],
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          metrics: ["events_ranking"],
          filters: dataFilters,
        }).then((data) => {
          if (!data?.events_ranking) {
            return null;
          }
          data?.events_ranking?.sort(
            (a: EventsRanking, b: EventsRanking) => b.nb_events - a.nb_events,
          );
          data?.events_ranking?.forEach((event: any, index: number) => {
            event.fill = graphColors[index % graphColors.length];
          });
          return data?.events_ranking;
        }),
      {
        keepPreviousData: true,
      },
    );

  const CustomTooltipEvent = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{`${payload[0].name}`}</p>
          <p className="text-green-500">{`${payload[0].value == 1 ? payload[0].value + " tag detected" : payload[0].value + " tags detected"}`}</p>
        </div>
      );
    }
    return null;
  };

  const CustomTooltipClustering = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{`Cluster ${payload[0].name}`}</p>
          <p className="text-secondary">{`Description: ${payload[0].payload.description}`}</p>
          <p className="text-green-500">{`${payload[0].value.toFixed(0)} messages in cluster`}</p>
        </div>
      );
    }
  };

  const CustomTooltipNbrSessions = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{`${label}`}</p>
          <p className="text-green-500">{`${payload[0].value === 1 ? payload[0].value + " session" : payload[0].value.toFixed(0) + " sessions"}`}</p>
        </div>
      );
    }
    return null;
  };

  if (!project_id) {
    return <></>;
  }

  return (
    <div>
      <AlertDialog open={open}>
        <SendDataAlertDialog setOpen={setOpen} />
      </AlertDialog>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Total number of Sessions</CardDescription>
              </CardHeader>
              <CardContent>
                {(!totalNbSessions && <p>...</p>) || (
                  <p className="text-xl">{totalNbSessions}</p>
                )}
              </CardContent>
            </Card>
          </div>
          <div className="ml-4 mr-4">
            <Card>
              <CardHeader>
                <CardDescription>Date of last clustering</CardDescription>
              </CardHeader>
              <CardContent>
                {((dateLastClustering === null ||
                  dateLastClustering === undefined) && <p>...</p>) || (
                  <p className="text-xl">{dateLastClustering}</p>
                )}
              </CardContent>
            </Card>
          </div>
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Most detected tagger</CardDescription>
              </CardHeader>
              <CardContent>
                {(!mostDetectedEvent && <p>...</p>) || (
                  <p className="text-xl">{mostDetectedEvent}</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      <div className="container mx-auto mt-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">Number of sessions</h3>
            {!totalNbSessions && (
              <div className="flex flex-col text-center items-center h-full">
                <p className="text-muted-foreground mb-2 text-sm pt-6">
                  Start sending data to get more insights
                </p>
                <Button variant="outline" onClick={() => setOpen(true)}>
                  Import data
                  <ChevronRight className="ml-2" />
                </Button>
              </div>
            )}
            {totalNbSessions && (
              <ChartContainer
                config={chartConfig}
                className="w-[100%] h-[10rem]"
              >
                <BarChart data={nbSessionsPerDay} barGap={0} barCategoryGap={0}>
                  <XAxis dataKey="day" />
                  <YAxis />
                  <ChartTooltip content={CustomTooltipNbrSessions} />
                  <Bar
                    dataKey="nb_sessions"
                    fill="#22c55e"
                    radius={[4, 4, 0, 0]}
                    barSize={20}
                  />
                </BarChart>
              </ChartContainer>
            )}
          </div>
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">Composition of last cluster</h3>
            {!lastClusteringComposition && (
              // Add a button in the center with a CTA "setup session tracking"
              <div className="flex flex-col text-center items-center h-full">
                <p className="text-muted-foreground mb-2 text-sm pt-6">
                  Cluster your data to get more insights
                </p>
                <Link href="/org/insights/clusters">
                  <Button variant="outline">
                    Cluster data
                    <ChevronRight className="ml-2" />
                  </Button>
                </Link>
              </div>
            )}
            {lastClusteringComposition && (
              <ChartContainer
                config={chartConfig}
                className="w-[100%] h-[10rem]"
              >
                <PieChart className="w-[100%] h-[10rem]">
                  <ChartTooltip content={CustomTooltipClustering} />
                  <Pie
                    data={lastClusteringComposition}
                    dataKey="size"
                    nameKey="name"
                    labelLine={false}
                    innerRadius={50}
                    outerRadius={70}
                  >
                    <Label
                      content={({ viewBox }) => {
                        if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                          return (
                            <text
                              x={viewBox.cx}
                              y={viewBox.cy}
                              textAnchor="middle"
                              dominantBaseline="middle"
                            >
                              <tspan
                                x={viewBox.cx}
                                y={(viewBox.cy || 0) - 3}
                                className="fill-foreground text-3xl font-bold"
                              >
                                {React.useMemo(() => {
                                  return lastClusteringComposition?.reduce(
                                    (acc, _) => acc + 1,
                                    0,
                                  );
                                }, [])?.toLocaleString()}
                              </tspan>
                              <tspan
                                x={viewBox.cx}
                                y={(viewBox.cy || 0) + 15}
                                className="fill-muted-foreground"
                              >
                                clusters
                              </tspan>
                            </text>
                          );
                        }
                      }}
                    />
                  </Pie>
                </PieChart>
              </ChartContainer>
            )}
          </div>
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">Top taggers</h3>
            {!eventsRanking && (
              // Add a button in the center with a CTA "setup analytics"
              <div className="flex flex-col text-center items-center h-full">
                <p className="text-muted-foreground mb-2 text-sm pt-6">
                  Setup analytics to get more insights
                </p>
                <Link href="/org/insights/events">
                  <Button variant="outline">
                    Setup analytics
                    <ChevronRight className="ml-2" />
                  </Button>
                </Link>
              </div>
            )}
            {eventsRanking && (
              <ChartContainer
                config={chartConfig}
                className="w-[100%] h-[10rem]"
              >
                <PieChart className="w-[100%] h-[10rem]">
                  <ChartTooltip content={CustomTooltipEvent} />
                  <Pie
                    data={eventsRanking}
                    dataKey="nb_events"
                    nameKey="event_name"
                    labelLine={false}
                    innerRadius={50}
                    outerRadius={70}
                  >
                    <Label
                      content={({ viewBox }) => {
                        if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                          return (
                            <text
                              x={viewBox.cx}
                              y={viewBox.cy}
                              textAnchor="middle"
                              dominantBaseline="middle"
                            >
                              <tspan
                                x={viewBox.cx}
                                y={(viewBox.cy || 0) - 3}
                                className="fill-foreground text-3xl font-bold"
                              >
                                {React.useMemo(() => {
                                  return eventsRanking?.reduce(
                                    (acc, curr) => acc + curr.nb_events,
                                    0,
                                  );
                                }, [])?.toLocaleString()}
                              </tspan>
                              <tspan
                                x={viewBox.cx}
                                y={(viewBox.cy || 0) + 15}
                                className="fill-muted-foreground"
                              >
                                tags
                              </tspan>
                            </text>
                          );
                        }
                      }}
                    />
                  </Pie>
                </PieChart>
              </ChartContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionsDataviz;
