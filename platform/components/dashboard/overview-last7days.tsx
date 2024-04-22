"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { useUser } from "@propelauth/nextjs/client";
// PostHog
import { usePostHog } from "posthog-js/react";
import React, { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

interface DailyDate {
  date: string;
  formated_date: string;
  success: number;
  failure: number;
  undefined: number;
}

const OverviewLast7Days = ({ project_id }: { project_id: string }) => {
  const { accessToken } = useUser();

  const { data: sevenDaysData } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/dashboard`,
          accessToken,
          JSON.stringify({
            graph_name: ["number_of_daily_tasks"],
          }),
        ]
      : null,
    ([url, accessToken, body]) =>
      authFetcher(url, accessToken, "POST", {
        graph_name: ["number_of_daily_tasks"],
      }).then((data) => {
        let number_of_daily_tasks = data?.number_of_daily_tasks;
        number_of_daily_tasks?.forEach((item: any) => {
          item.formated_date = new Date(item.date).toLocaleDateString([], {
            month: "short",
            day: "numeric",
          });
        });
        return number_of_daily_tasks;
      }),
    {
      keepPreviousData: true,
    },
  );

  const CustomToolTip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div>
          <p>{label}</p>
          {payload.map((item: any) => {
            return (
              <p key={item.name}>
                {item.name}: {item.value}
              </p>
            );
          })}
        </div>
      );
    }
    return null;
  };

  console.log("sevenDaysData :", sevenDaysData);

  // Display the data or "Loading..."
  return (
    <div>
      {!sevenDaysData ? (
        <Skeleton className="h-[250px]" />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart
            width={500}
            height={400}
            data={sevenDaysData}
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<CustomToolTip />} />
            <Area
              type="monotone"
              dataKey={`undefined`}
              name="undefined"
              // light grey fill
              stroke="#BDBDBD"
              fill="#BDBDBD"
              stackId="1"
            />
            <Area
              type="monotone"
              dataKey={`success`}
              name="success"
              fillOpacity={1}
              // green fill
              stroke="#22c55e"
              fill="#22c55e"
              stackId="1"
            />
            <Area
              type="monotone"
              dataKey={`failure`}
              name="failure"
              // red fill
              stroke="#F87171"
              fill="#F87171"
              stackId="1"
            />
            <Legend />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default OverviewLast7Days;
