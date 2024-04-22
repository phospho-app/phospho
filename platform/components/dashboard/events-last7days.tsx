"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { authFetcher } from "@/lib/fetcher";
import { Event } from "@/models/models";
import { dataStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import React, { useEffect, useState } from "react";
import {
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

interface EventColorMapping {
  [key: string]: string;
}

interface DailyEvents {
  [key: string]: number[] | string[];
  unique_event_names: string[];
  date: string[];
  formated_date: string[];
  total: number[];
}

const EventsLast7Days = ({ project_id }: { project_id: string }) => {
  const { loading, accessToken } = useUser();

  let uniqueEventNames: string[] = [];
  const { data: uniqueEvents } = useSWR(
    project_id
      ? [`/api/projects/${project_id}/unique-events`, accessToken]
      : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
    },
  );
  if (project_id && uniqueEvents?.events) {
    uniqueEventNames = Array.from(
      new Set(
        uniqueEvents.events.map((event: Event) => event.event_name as string),
      ),
    );
  }

  const { data: eventLastSevenDays } = useSWR(
    project_id
      ? [
          `/api/explore/${project_id}/dashboard`,
          accessToken,
          JSON.stringify({
            graph_name: ["events_per_day"],
          }),
        ]
      : null,
    ([url, accessToken, body]) =>
      authFetcher(url, accessToken, "POST", {
        graph_name: ["events_per_day"],
      }).then((data) => {
        let events_per_day = data?.events_per_day;
        events_per_day?.data.forEach((item: any) => {
          item.formated_date = new Date(item.date).toLocaleDateString([], {
            month: "short",
            day: "numeric",
          });
        });
        return events_per_day?.data;
      }),
    {
      keepPreviousData: true,
    },
  );

  const predefinedColors = ["#00C389", "#00A376", "#008C6F", "#007A68"];
  let colorIndex = 0;

  // Function to generate a random color
  const getRandomColor = () => {
    const letters = "0123456789ABCDEF";
    let color = "#";
    for (let i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  };

  // Assign a random color to each event name
  const eventColors: EventColorMapping = uniqueEventNames?.reduce(
    (acc, eventName) => {
      colorIndex++;
      acc[eventName] = predefinedColors[colorIndex] || getRandomColor();
      return acc;
    },
    {} as EventColorMapping,
  );

  // Customize the tooltipe to display the event names
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload) {
      return (
        <div>
          <p className="label">{`${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={`value-${index}`} style={{ color: entry.color }}>
              {`${entry.name} : ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }

    return null;
  };

  console.log("eventLastSevenDays :", eventLastSevenDays);

  return (
    <div>
      {!eventLastSevenDays ? (
        <Skeleton className="h-[250px]" />
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <LineChart
            width={500}
            height={400}
            data={eventLastSevenDays}
            margin={{
              top: 10,
              right: 30,
              left: 0,
              bottom: 0,
            }}
          >
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="total"
              stroke="#737373"
              dot={false}
            />

            {uniqueEventNames?.map((eventName, index) => (
              <Line
                key={index}
                type="monotone"
                dataKey={eventName}
                stroke={eventColors[eventName]}
                dot={false}
                name={eventName}
              />
            ))}
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default EventsLast7Days;
