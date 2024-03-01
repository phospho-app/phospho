"use client";

import { Skeleton } from "@/components/ui/skeleton";
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

interface DailyDate {
  date: string;
  formated_date: string;
  success: number;
  failure: number;
  undefined: number;
}

const OverviewLast7Days = ({ project_id }: { project_id: string }) => {
  const { accessToken, loading } = useUser();

  const [sevenDaysData, setSevenDaysData] = useState<DailyDate[] | null>(null);

  const posthog = usePostHog();

  function overviewLast7DaysLoaded(time: number): void {
    posthog.capture("overview_last7days_loaded", {
      request_time: time,
    });
  }

  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const start = performance.now();
      fetch(`/api/explore/${project_id}/dashboard`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + accessToken || "",
        },
        body: JSON.stringify({
          graph_name: ["number_of_daily_tasks"],
        }),
      }).then(async (response) => {
        const response_json = await response.json();
        const number_of_daily_tasks = response_json?.number_of_daily_tasks;
        // Format the "days" field from "2024-01-12" (UTC) to local time "Jan 12"
        number_of_daily_tasks?.forEach((item: any) => {
          item.formated_date = new Date(item.date).toLocaleDateString([], {
            month: "short",
            day: "numeric",
          });
        });
        setSevenDaysData(number_of_daily_tasks);
        const end = performance.now();
        const time = (end - start) / 1000;
        console.log("overviewLast7Days API call took", time, "seconds");
        // Log to PostHog
        overviewLast7DaysLoaded(time);
      });
    })();
  }, [project_id, loading]);

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
