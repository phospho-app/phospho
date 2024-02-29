"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface UsageLast7DaysProps {
  project_id: string;
}

const UsageLast30m: React.FC<UsageLast7DaysProps> = ({ project_id }) => {
  const { accessToken } = useUser();

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [thirtyMinData, setThirtyMinData] = useState<any[]>([]);

  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      const headers = {
        "Content-Type": "application/json",
        Authorization: "Bearer " + accessToken || "",
      };
      const response = await fetch(`/api/explore/${project_id}/aggregated`, {
        method: "POST",
        headers: headers,
        body: JSON.stringify({
          index: ["minutes"],
          count_of: "tasks",
          timerange: "last_30_minutes",
        }),
      });
      const response_json = await response.json();
      // Format the "minutes" field from "2024-01-12T15:27:00" (UTC) to local time
      response_json?.forEach((item: any) => {
        item.name = new Date(item.minutes).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      });
      setThirtyMinData(response_json);
      setIsLoading(false);
    })();
  }, [project_id]);

  console.log("thirtyMinData :", thirtyMinData);

  // Display the data or "Loading..."
  return (
    <div>
      {isLoading ? (
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
