"use client";

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
import { ProjectDataFilters } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import React, { useMemo } from "react";
import { Label, Pie, PieChart } from "recharts";
import { TooltipProps } from "recharts";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";
import useSWR from "swr";

const chartConfig: ChartConfig = {};

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

const UsersDataviz = ({
  forcedDataFilters,
}: {
  forcedDataFilters?: ProjectDataFilters | null;
}) => {
  // TODO: Implement forcedDataFilters
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);

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

  const CustomTooltip: React.FC<TooltipProps<ValueType, NameType>> = ({
    active,
    payload,
  }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-primary shadow-md p-2 rounded-md">
          <p className="text-secondary font-semibold">{payload[0].name}</p>
          <p className="text-secondary">{payload[0].value} messages</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div>
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex flex-col justify-between space-y-4">
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
          <Card>
            <CardHeader>
              <CardDescription>User job title distribution</CardDescription>
            </CardHeader>
            <CardContent>
              {userJobTitles && (
                <ChartContainer
                  config={chartConfig}
                  className="w-[100%] h-[10rem]"
                >
                  <PieChart className="w-[100%] h-[10rem]">
                    <ChartTooltip content={CustomTooltip} />
                    <Pie
                      data={userJobTitles}
                      dataKey="count"
                      nameKey="category"
                      labelLine={false}
                      innerRadius={60}
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
                                  y={(viewBox.cy || 0) + 5}
                                  className="fill-foreground text-3xl font-bold"
                                >
                                  {totalJobTitles.toLocaleString()}
                                </tspan>
                                <tspan
                                  x={viewBox.cx}
                                  y={(viewBox.cy || 0) + 25}
                                  className="fill-muted-foreground"
                                >
                                  job titles
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
              {userJobTitles === undefined && (
                <Skeleton className="w-[100%] h-[10rem]" />
              )}
              {userJobTitles === null && (
                <div className="flex flex-col text-center items-center h-full">
                  <p className="text-muted-foreground mb-2 text-sm pt-6">
                    Add a classifier named <code>User job title</code>
                    <br /> to get started
                  </p>
                  <Link href="/org/insights/events">
                    <Button variant="outline">
                      Setup analytics
                      <ChevronRight className="ml-2" />
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardDescription>User industry distribution</CardDescription>
            </CardHeader>
            <CardContent>
              {userIndustry && (
                <ChartContainer
                  config={chartConfig}
                  className="w-[100%] h-[10rem]"
                >
                  <PieChart className="w-[100%] h-[10rem]">
                    <ChartTooltip content={CustomTooltip} />
                    <Pie
                      data={userIndustry}
                      dataKey="count"
                      nameKey="category"
                      labelLine={false}
                      innerRadius={60}
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
                                  y={(viewBox.cy || 0) + 5}
                                  className="fill-foreground text-3xl font-bold"
                                >
                                  {totalJobTitles.toLocaleString()}
                                </tspan>
                                <tspan
                                  x={viewBox.cx}
                                  y={(viewBox.cy || 0) + 25}
                                  className="fill-muted-foreground"
                                >
                                  industries
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
              {userIndustry === undefined && (
                <Skeleton className="w-[100%] h-[10rem]" />
              )}
              {userIndustry === null && (
                <div className="flex flex-col text-center items-center h-full">
                  <p className="text-muted-foreground mb-2 text-sm pt-6">
                    Add a classifier named <code>User industry</code>
                    <br /> to get started
                  </p>
                  <Link href="/org/insights/events">
                    <Button variant="outline">
                      Setup analytics
                      <ChevronRight className="ml-2" />
                    </Button>
                  </Link>
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
