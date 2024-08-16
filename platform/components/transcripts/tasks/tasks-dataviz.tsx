import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
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
import GenericDataviz from "@/components/dataviz/generic-dataviz";

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

  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const project_id = navigationStateStore((state) => state.project_id);

  // Fetch the has session
  const { data: hasSessionData } = useSWR(
    project_id
      ? [`/api/explore/${project_id}/has-sessions`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasSessions: boolean = hasSessionData?.has_sessions;

  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "total_nb_tasks",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        filters: dataFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;

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

  const { data: globalSuccessRateData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      "global_success_rate",
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["global_success_rate"],
        filters: dataFilters,
      }),
    {
      keepPreviousData: true,
    },
  );
  const globalSuccessRate: number | null | undefined = Math.round(
    (globalSuccessRateData?.global_success_rate * 10000) / 100,
  );

  const CustomTooltipSuccessRate = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{`Success rate after ${label == 1 ? label + " task" : label + " tasks"}`}</p>
          <p className="text-green-500">{`${payload[0].value.toFixed(2)}% success rate`}</p>
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
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["success_rate_per_task_position"],
        filters: dataFilters,
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

  // Build the dataviz components
  const DailyTasksDataviz = () => {
    const analyticsQuery = {
      project_id: project_id,
      collection: "tasks",
      aggregation_operation: "count",
      dimensions: ["day"],
      filters: {
        created_at_start: Math.floor(Date.now() / 1000) - 60 * 60 * 24 * 7, // Last 7 days
      },
    };

    return (
      <GenericDataviz
        analyticsQuery={analyticsQuery}
        asFilledTimeSeries={true}
        xField="day"
        yFields={["value"]}
        chartType="stackedBar"
      />
    );
  };

  const ForPieDataviz = () => {
    const analyticsQuery = {
      project_id: project_id,
      collection: "events",
      aggregation_operation: "count",
      dimensions: ["event_name"],
      sort: { nb_events: -1 },
    };

    return (
      <GenericDataviz
        analyticsQuery={analyticsQuery}
        xField="event_name"
        yFields={["value"]}
        chartType="pie"
      />
    );
  };

  const LangPieDataviz = () => {
    const analyticsQuery = {
      project_id: project_id,
      collection: "tasks",
      aggregation_operation: "count",
      dimensions: ["language"],
      sort: { nb_events: -1 },
    };

    return (
      <GenericDataviz
        analyticsQuery={analyticsQuery}
        xField="language"
        yFields={["value"]}
        chartType="pie"
      />
    );
  };

  // Clustering dataviz

  return (
    <div>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Card>
              <CardHeader>
                <CardDescription>Total number of user messages</CardDescription>
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
                <CardDescription>Most detected event</CardDescription>
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
                <CardDescription>
                  Average Evaluation Success Rate
                </CardDescription>
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
            <h3 className="text-slate-500 mb-2">Messages per day</h3>
            <div className="max-h-[150px]">
              <DailyTasksDataviz />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">Top events</h3>
            <div className="max-h-[150px]">
              <ForPieDataviz />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-slate-500 mb-2">
              Language
            </h3>
            <LangPieDataviz />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TasksDataviz;
