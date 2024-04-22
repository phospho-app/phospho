import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import Link from "next/link";
import React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

interface NbDailyTasks {
  day: string;
  date: string;
  nb_tasks: number;
}

interface EventsRanking {
  event_name: string;
  nb_events: number;
}

interface SuccessRate {
  day: string;
  date: string;
  success_rate: number;
}

interface SuccessRateByPosition {
  task_position: number;
  success_rate: number;
}

interface TasksMetrics {
  total_nb_tasks: number;
  global_success_rate: number;
  most_detected_event: string;
  nb_daily_tasks: NbDailyTasks[];
  events_ranking: EventsRanking[];
  daily_success_rate: SuccessRate[];
  success_rate_per_task_position: SuccessRateByPosition[] | null;
}

const TasksDataviz: React.FC = () => {
  const { accessToken } = useUser();

  const tasksColumnsFilters = navigationStateStore(
    (state) => state.tasksColumnsFilters,
  );
  const hasSessions = dataStateStore((state) => state.hasSessions);
  const project_id = navigationStateStore((state) => state.project_id);
  const dateRange = navigationStateStore((state) => state.dateRange);

  let flagFilter: string | null = null;
  let eventFilter: string | null = null;
  for (let filter of tasksColumnsFilters) {
    if (
      filter.id === "flag" &&
      (typeof filter?.value === "string" || filter?.value === null)
    ) {
      flagFilter = filter?.value;
    }
    if (
      filter.id === "events" &&
      (typeof filter?.value === "string" || filter?.value === null)
    ) {
      eventFilter = filter?.value;
    }
  }

  const tasksFilters = {
    flag: flagFilter,
    event_name: eventFilter,
    created_at_start: dateRange?.created_at_start,
    created_at_end: dateRange?.created_at_end,
  };

  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "total_nb_tasks",
      JSON.stringify(tasksFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        tasks_filter: tasksFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;
  console.log("totalNbTasksData", totalNbTasksData);

  const { data: mostDetectedEventData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "most_detected_event",
      JSON.stringify(tasksFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["most_detected_event"],
        tasks_filter: tasksFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const mostDetectedEvent: string | null | undefined =
    mostDetectedEventData?.most_detected_event;
  console.log("mostDetectedEventData", mostDetectedEventData);

  const { data: globalSuccessRateData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "global_success_rate",
      JSON.stringify(tasksFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["global_success_rate"],
        tasks_filter: tasksFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const globalSuccessRate: number | null | undefined = Math.round(
    (globalSuccessRateData?.global_success_rate * 10000) / 100,
  );

  const { data: nbDailyTasks }: { data: NbDailyTasks[] | null | undefined } =
    useSWR(
      [
        `/api/explore/${project_id}/aggregated/tasks`,
        accessToken,

        "nb_daily_tasks",
        JSON.stringify(tasksFilters),
      ],
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          metrics: ["nb_daily_tasks"],
          tasks_filter: tasksFilters,
        }).then((data) => {
          if (!data?.nb_daily_tasks) {
            return null;
          }
          return data?.nb_daily_tasks?.map((nb_daily_task: NbDailyTasks) => {
            const date = new Date(nb_daily_task.date);
            nb_daily_task.day = date.toLocaleDateString("en-US", {
              weekday: "short",
            });
            return nb_daily_task;
          });
        }),
      {
        keepPreviousData: true,
      },
    );

  const { data: eventsRanking }: { data: EventsRanking[] | null | undefined } =
    useSWR(
      [
        `/api/explore/${project_id}/aggregated/tasks`,
        accessToken,
        "events_ranking",
        JSON.stringify(tasksFilters),
      ],
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          metrics: ["events_ranking"],
          tasks_filter: tasksFilters,
        }).then((data) => {
          if (!data?.events_ranking) {
            return null;
          }
          data?.events_ranking?.sort(
            (a: EventsRanking, b: EventsRanking) => b.nb_events - a.nb_events,
          );
          return data?.events_ranking;
        }),
      {
        keepPreviousData: true,
      },
    );

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{`${label}`}</p>
          <p className="text-green-500">
            {`${payload[0].value.toFixed(2)}% success rate`}
          </p>
        </div>
      );
    }

    return null;
  };

  const {
    data: successRatePerTaskPosition,
  }: {
    data: SuccessRateByPosition[] | null | undefined;
  } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "success_rate_per_task_position",
      JSON.stringify(tasksFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["success_rate_per_task_position"],
        tasks_filter: tasksFilters,
      }).then((data) => {
        if (!data?.success_rate_per_task_position) {
          return null;
        }
        return data?.success_rate_per_task_position?.map(
          (success_rate: SuccessRateByPosition) => {
            success_rate.success_rate =
              Math.round(success_rate.success_rate * 10000) / 100;
            return success_rate;
          },
        );
      }),
    {
      keepPreviousData: true,
    },
  );

  if (!project_id) {
    return <></>;
  }

  return (
    <div>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Total Nb of Tasks</CardDescription>
              </CardHeader>
              <CardContent>
                {((totalNbTasks === null || totalNbTasks === undefined) && (
                  <p>...</p>
                )) || <p className="text-xl">{totalNbTasks}</p>}
              </CardContent>
            </Card>
          </div>
          <div className="ml-4 mr-4">
            <Card className="overflow-hidden">
              <CardHeader>
                <CardDescription>Most Detected Event</CardDescription>
              </CardHeader>
              <CardContent>
                {(!mostDetectedEvent && <p>...</p>) || (
                  <p className="text-xl">{mostDetectedEvent}</p>
                )}
              </CardContent>
            </Card>
          </div>
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Average Task Success Rate</CardDescription>
              </CardHeader>
              <CardContent>
                {((globalSuccessRate === null ||
                  globalSuccessRate === undefined) && <p>...</p>) || (
                  <p className="text-xl">{globalSuccessRate} %</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      <div className="container mx-auto mt-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">
              Nb of tasks per day (last 7d)
            </h3>
            {(!nbDailyTasks && <Skeleton className="w-[100%] h-[150px]" />) ||
              (nbDailyTasks && (
                <ResponsiveContainer width="100%" height={150}>
                  <BarChart
                    width={300}
                    height={250}
                    data={nbDailyTasks}
                    barGap={0}
                    barCategoryGap={0}
                  >
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip content={CustomTooltip} />
                    <Bar
                      dataKey="nb_tasks"
                      fill="#22c55e"
                      radius={[4, 4, 0, 0]}
                      barSize={20}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ))}
          </div>
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">Top events (last 7d)</h3>
            {(!eventsRanking && <Skeleton className="w-[100%] h-[150px]" />) ||
              (eventsRanking && (
                <ResponsiveContainer className="flex justify-end" height={150}>
                  <BarChart
                    // width={300}
                    height={250}
                    data={eventsRanking}
                    barGap={0}
                    barCategoryGap={0}
                    layout="horizontal"
                  >
                    <YAxis type="number" />
                    <XAxis
                      dataKey="event_name"
                      type="category"
                      fontSize={12}
                      overflow={"visible"}
                      // angle={-45} // Rotate the labels by 45 degrees
                    />
                    <Tooltip content={CustomTooltip} />
                    <Bar
                      dataKey="nb_events"
                      fill="#22c55e"
                      radius={[4, 4, 0, 0]}
                      barSize={20}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ))}
          </div>
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">
              Success Rate per task position
            </h3>
            {hasSessions && !successRatePerTaskPosition && (
              <Skeleton className="w-[100%] h-[150px]" />
            )}
            {!hasSessions && !successRatePerTaskPosition && (
              // Add a button in the center with a CTA "setup session tracking"
              <div className="flex flex-col text-center items-center h-full">
                <p className="text-gray-500 mb-2 text-sm pt-6">
                  Only available with session tracking
                </p>
                <Link
                  href="https://docs.phospho.ai/guides/sessions-and-users#sessions"
                  target="_blank"
                >
                  <Button variant="outline">Setup session tracking</Button>
                </Link>
              </div>
            )}
            {successRatePerTaskPosition && (
              <ResponsiveContainer width="100%" height={150}>
                <AreaChart
                  width={730}
                  height={250}
                  data={successRatePerTaskPosition}
                  // margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorUv" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="task_position" className="text-slate-500" />
                  <YAxis unit="%" />
                  <Tooltip content={CustomTooltip} />
                  <Area
                    type="monotone"
                    dataKey="success_rate"
                    stroke="#22c55e"
                    fillOpacity={1}
                    fill="url(#colorUv)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TasksDataviz;
