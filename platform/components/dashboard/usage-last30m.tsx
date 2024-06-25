"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React from "react";
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import useSWR from "swr";

const UsageLast30m: React.FC = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: thirtyMinData } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/aggregated`,
          accessToken,
          JSON.stringify({
            index: ["minutes"],
            count_of: "tasks",
            timerange: "last_30_minutes",
          }),
        ]
      : null,
    ([url, accessToken, body]) =>
      authFetcher(url, accessToken, "POST", {
        index: ["minutes"],
        count_of: "tasks",
        timerange: "last_30_minutes",
      })?.then((data) => {
        return data?.forEach((item: any) => {
          item.name = new Date(item.minutes).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          });
        });
      }),
    {
      keepPreviousData: true,
    },
  );

  console.log("thirtyMinData :", thirtyMinData);

  // Display the data or "Loading..."
  return (
    <div>
      {thirtyMinData === undefined || thirtyMinData === null ? (
        <Skeleton className="h-[250px]" />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={thirtyMinData}>
            <XAxis
              dataKey="name"
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={true}
            />
            <YAxis
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
            />
            <Bar dataKey="id" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default UsageLast30m;
