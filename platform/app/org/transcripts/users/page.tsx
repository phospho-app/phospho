"use client";

import { UsersTable } from "@/components/transcripts/users/users-table";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
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
import { ChevronRight, HeartHandshake } from "lucide-react";
import Link from "next/link";
import React from "react";
import { Bar, BarChart, Label, Pie, PieChart, XAxis, YAxis } from "recharts";
import useSWR from "swr";

// TODO : Add graph colors like in tasks-dataviz.tsx

const chartConfig: ChartConfig = {};

interface JobTitles {
  category: string;
  count: number;
}

interface Industry {
  category: string;
  count: number;
}

const UsersDataviz = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  // Fetch all users
  const { data: usersData } = useSWR(
    project_id ? [`/api/projects/${project_id}/users`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const usersMetadata = usersData?.users;

  // Fetch graph data
  const { data: userCountData, error: fetchUserCountError } = useSWR(
    [`/api/metadata/${project_id}/count/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userCount = userCountData?.value;

  const { data: userAverageData, error: fetchUserAverageError } = useSWR(
    [`/api/metadata/${project_id}/average/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userAverage = Math.round(userAverageData?.value * 100) / 100;

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
          jobTitles.forEach((dataPoint: any, index: number) => {
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
          userIndustry.forEach((dataPoint: any, index: number) => {
            dataPoint.fill = graphColors[index % graphColors.length];
          });
          return userIndustry;
        }),
      {
        keepPreviousData: true,
      },
    );

  console.log("userIndustry", userIndustry);

  const CustomTooltip = ({ active, payload, label }: any) => {
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
                {((userCount === null || userCount === undefined) && (
                  <p>...</p>
                )) || <p className="text-2xl font-bold">{userCount}</p>}
              </CardContent>
            </Card>
            <Card className="flex-grow">
              <CardHeader>
                <CardDescription>
                  Average number of messages sent per user
                </CardDescription>
              </CardHeader>
              <CardContent>
                {((userAverage === null || userAverage === undefined) && (
                  <p>...</p>
                )) || (
                  <p className="text-2xl font-bold">{userAverage.toString()}</p>
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
                                  {React.useMemo(() => {
                                    return userJobTitles?.reduce(
                                      (acc, _) => acc + 1,
                                      0,
                                    );
                                  }, [])?.toLocaleString()}
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
                                  {React.useMemo(() => {
                                    return userIndustry?.reduce(
                                      (acc, _) => acc + 1,
                                      0,
                                    );
                                  }, [])?.toLocaleString()}
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

const Users = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: userCountData, error: fetchUserCountError } = useSWR(
    [`/api/metadata/${project_id}/count/tasks/user_id`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  const userCount = userCountData?.value;

  return (
    <>
      {userCount === 0 && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex">
              <HeartHandshake className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="flex flex-row text-2xl font-bold tracking-tight items-center">
                    Analyze user activity
                  </CardTitle>
                  <CardDescription>
                    Group messages by user by adding a <code>user_id</code> in
                    metadata when logging.
                  </CardDescription>
                </div>
                <Link
                  href="https://docs.phospho.ai/guides/sessions-and-users#users"
                  target="_blank"
                >
                  <Button variant="default">Set up user tracking</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}
      <UsersDataviz />
      <UsersTable />
    </>
  );
};

export default Users;
