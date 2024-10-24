"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PieChartSection } from "@/components/users/user-dataviz-pies";
import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { ProjectDataFilters } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import React, { useMemo, useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

interface JobTitles {
  category: string;
  count: number;
  fill?: string;
}

interface Industry {
  category: string;
  count: number;
  fill?: string;
}

interface RetentionData {
  day?: number;
  week?: number;
  retention: number;
}

const UsersDataviz = ({
  forcedDataFilters,
}: {
  forcedDataFilters?: ProjectDataFilters | null;
}) => {
  // TODO: Implement forcedDataFilters
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const [selectedMetric, setSelectedMetric] = useState<
    "jobTitles" | "industry"
  >("jobTitles");

  const dataFiltersMerged = {
    ...dataFilters,
    ...forcedDataFilters,
  };

  // Fetch graph data
  const { data: usersCount }: { data: number | undefined } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/aggregated/users`,
          accessToken,
          JSON.stringify(dataFiltersMerged),
          "nb_users",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["nb_users"],
        filters: dataFiltersMerged,
      }).then((data) => {
        if (data === undefined) return undefined;
        return data.nb_users;
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: avgNbTasksPerUser } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/aggregated/users`,
          accessToken,
          JSON.stringify(dataFiltersMerged),
          "avg_nb_tasks_per_user",
        ]
      : null,
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["avg_nb_tasks_per_user"],
        filters: dataFiltersMerged,
      }).then((data) => {
        if (data === undefined) return undefined;
        if (!data?.avg_nb_tasks_per_user) return null;
        const roundedOutput = Number(data?.avg_nb_tasks_per_user.toFixed(2));
        return roundedOutput;
      }),
    {
      keepPreviousData: true,
    },
  );

  const { data: userRetention }: { data: RetentionData[] | null | undefined } =
    useSWR(
      project_id
        ? [
            `/api/explore/${project_id}/aggregated/users`,
            accessToken,
            JSON.stringify(dataFiltersMerged),
            "user_retention",
          ]
        : null,
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          metrics: ["user_retention"],
          filters: dataFiltersMerged,
        }).then((data) => {
          if (data === undefined) {
            return undefined;
          }
          if (!data?.user_retention) {
            return null;
          }
          return data.user_retention;
        }),
      {
        keepPreviousData: true,
      },
    );

  const { data: userJobTitles }: { data: JobTitles[] | null | undefined } =
    useSWR(
      project_id
        ? [
            `/api/explore/${project_id}/aggregated/events`,
            accessToken,
            "category_distribution",
            "User job title",
          ]
        : null,
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          metrics: ["category_distribution"],
          filters: {
            event_name: ["User job title"],
          },
        }).then((data) => {
          if (data === undefined) {
            return undefined;
          }
          const jobTitles = data?.category_distribution["User job title"];
          if (!jobTitles) {
            return null;
          }
          jobTitles.forEach((dataPoint: JobTitles, index: number) => {
            dataPoint.fill = graphColors[index % graphColors.length];
          });
          return jobTitles;
        }),
      {
        keepPreviousData: true,
      },
    );

  const { data: userIndustry }: { data: Industry[] | null | undefined } =
    useSWR(
      project_id
        ? [
            `/api/explore/${project_id}/aggregated/events`,
            accessToken,
            "category_distribution",
            "User industry",
          ]
        : null,
      ([url, accessToken]) =>
        authFetcher(url, accessToken, "POST", {
          metrics: ["category_distribution"],
          filters: {
            event_name: ["User industry"],
          },
        }).then((data) => {
          if (data === undefined) {
            return undefined;
          }
          const userIndustry = data?.category_distribution["User industry"];
          if (!userIndustry) {
            return null;
          }
          userIndustry.forEach((dataPoint: Industry, index: number) => {
            dataPoint.fill = graphColors[index % graphColors.length];
          });
          return userIndustry;
        }),
      {
        keepPreviousData: true,
      },
    );

  const totalJobTitles = useMemo(() => {
    return userJobTitles?.reduce((acc) => acc + 1, 0) || 0;
  }, [userJobTitles]);

  const isDaily = useMemo(() => {
    if (!userRetention?.length) return false;
    return "day" in userRetention[0];
  }, [userRetention]);

  const formatPeriod = (value: number) => {
    if (userRetention?.length === undefined) return "";
    if (isDaily) {
      if (value === userRetention?.length - 1) return "Today";
      if (value === userRetention?.length - 2) return "Yesterday";
      return `${userRetention?.length - value} days ago`;
    } else {
      if (value === userRetention?.length - 1) return "This week";
      if (value === userRetention?.length - 2) return "Last week";
      return `${userRetention?.length - value} weeks ago`;
    }
  };

  const getXAxisKey = () => (isDaily ? "day" : "week");

  return (
    <div>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex flex-col justify-between space-y-4">
            {/* First card - User Stats */}

            {/* Top card */}
            <Card className="flex-grow">
              <CardHeader>
                <CardDescription>Number of unique user_id</CardDescription>
              </CardHeader>
              <CardContent>
                {usersCount === undefined && (
                  <p className="text-2xl font-bold">...</p>
                )}
                {usersCount === null && (
                  <p className="text-2xl font-bold">None</p>
                )}
                {usersCount !== undefined && usersCount !== null && (
                  <p className="text-2xl font-bold">{usersCount}</p>
                )}
              </CardContent>
            </Card>

            {/* Bottom card */}
            <Card className="flex-grow">
              <CardHeader>
                <CardDescription>
                  Average number of messages per user
                </CardDescription>
              </CardHeader>
              <CardContent>
                {avgNbTasksPerUser === undefined && (
                  <p className="text-2xl font-bold">...</p>
                )}
                {avgNbTasksPerUser === null && (
                  <p className="text-2xl font-bold">None</p>
                )}
                {avgNbTasksPerUser !== undefined &&
                  avgNbTasksPerUser !== null && (
                    <p className="text-2xl font-bold">{avgNbTasksPerUser}</p>
                  )}
              </CardContent>
            </Card>
          </div>

          {/* Second card - Combined Pie Charts */}

          <PieChartSection
            selectedMetric={selectedMetric}
            setSelectedMetric={setSelectedMetric}
            data={selectedMetric === "jobTitles" ? userJobTitles : userIndustry}
            totalCount={totalJobTitles}
          />

          {/* Third card - Retention Chart */}

          <Card>
            <CardHeader>
              <CardDescription>
                {isDaily ? "Daily" : "Weekly"} User Retention
              </CardDescription>
            </CardHeader>
            <CardContent>
              {userRetention === undefined && (
                <Skeleton className="w-[100%] h-[10rem]" />
              )}
              {userRetention === null && (
                <div className="flex flex-col text-center items-center h-[10rem] justify-center">
                  <Link href="https://docs.phospho.ai/analytics/sessions-and-users">
                    <Button variant="outline" size="sm">
                      Start tracking retention
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              )}
              {userRetention && userRetention.length > 1 && (
                <ResponsiveContainer width="100%" height={160}>
                  <LineChart data={userRetention}>
                    <XAxis
                      dataKey={getXAxisKey()}
                      tickFormatter={formatPeriod}
                      fontSize={12}
                    />
                    <YAxis
                      tickFormatter={(value) => `${value}%`}
                      domain={[0, 100]}
                      fontSize={12}
                    />
                    <Tooltip
                      formatter={(value) => [`${value}%`, "Retention"]}
                      labelFormatter={formatPeriod}
                    />
                    <Line
                      type="linear"
                      dataKey="retention"
                      stroke="#72C464"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
              {userRetention && userRetention.length < 2 && (
                <div className="flex flex-col text-center items-center h-[10rem] justify-center">
                  <p className="text-lg font-bold">Not enough data</p>
                  <p className="text-sm text-gray-500">
                    Need at least 2 data points
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export { UsersDataviz };
