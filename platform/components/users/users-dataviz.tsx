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
  TooltipProps,
  XAxis,
  YAxis,
} from "recharts";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";
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

  const CustomTooltip: React.FC<TooltipProps<ValueType, NameType>> = ({
    active,
    payload,
  }) => {
    if (active && payload && payload.length) {
      const date = new Date(payload[0].payload.date * 1000);
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const lastWeek = new Date();
      lastWeek.setDate(lastWeek.getDate() - 7);

      let dateDisplay;
      if (isDaily) {
        if (date.toDateString() === today.toDateString()) {
          dateDisplay = "Today";
        } else if (date.toDateString() === yesterday.toDateString()) {
          dateDisplay = "Yesterday";
        } else {
          dateDisplay = date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          });
        }
      } else {
        if (isSameWeek(date, today)) {
          dateDisplay = "This week";
        } else if (isSameWeek(date, lastWeek)) {
          dateDisplay = "Last week";
        } else {
          dateDisplay = date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          });
        }
      }

      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{dateDisplay}</p>
          <p className="text-green-500">Retention: {payload[0].value}%</p>
        </div>
      );
    }
    return null;
  };

  const totalJobIndustry = useMemo(() => {
    return userIndustry?.reduce((acc) => acc + 1, 0) || 0;
  }, [userIndustry]);

  const totalJobTitles = useMemo(() => {
    return userJobTitles?.reduce((acc) => acc + 1, 0) || 0;
  }, [userJobTitles]);

  const isDaily = useMemo(() => {
    if (!userRetention?.length) return false;
    return "day" in userRetention[0];
  }, [userRetention]);

  function isSameWeek(date1: Date, date2: Date): boolean {
    const getWeekNumber = (date: Date) => {
      const d = new Date(date);
      d.setHours(0, 0, 0, 0);
      d.setDate(d.getDate() + 4 - (d.getDay() || 7));
      const yearStart = new Date(d.getFullYear(), 0, 1);
      return Math.ceil(
        ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7,
      );
    };

    return (
      date1.getFullYear() === date2.getFullYear() &&
      getWeekNumber(date1) === getWeekNumber(date2)
    );
  }

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
            totalCount={
              selectedMetric === "jobTitles" ? totalJobTitles : totalJobIndustry
            }
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
                      dataKey="date"
                      tickFormatter={(timestamp) => {
                        const date = new Date(timestamp * 1000);
                        const today = new Date();
                        const lastWeek = new Date();
                        lastWeek.setDate(lastWeek.getDate() - 7);

                        // Check if the date matches today or last week
                        if (isDaily) {
                          if (date.toDateString() === today.toDateString()) {
                            return "Today";
                          }
                          return date.toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                          });
                        } else {
                          // For weekly data
                          if (isSameWeek(date, today)) {
                            return "This week";
                          }
                          if (isSameWeek(date, lastWeek)) {
                            return "Last week";
                          }
                          return date.toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                          });
                        }
                      }}
                      fontSize={12}
                    />
                    <YAxis
                      tickFormatter={(value) => `${value}%`}
                      domain={[0, 100]}
                      fontSize={12}
                    />
                    <Tooltip content={CustomTooltip} />
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
