"use client";

import { Skeleton } from "@/components/ui/skeleton";
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
  const uniqueEventNames = dataStateStore((state) => state.uniqueEventNames);
  const setUniqueEventNames = dataStateStore(
    (state) => state.setUniqueEventNames,
  );

  const [eventLastSevenDays, setEventLastSevenDays] = useState<
    DailyEvents[] | null
  >(null);

  useEffect(() => {
    // Fetch aggregated metrics from the API
    (async () => {
      fetch(`/api/explore/${project_id}/dashboard`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + accessToken || "",
        },
        body: JSON.stringify({
          graph_name: ["events_per_day"],
        }),
      }).then(async (response) => {
        const response_json = await response.json();
        console.log("events_per_day", response_json);
        let events_per_day = response_json?.events_per_day;
        // Format the "days" field from "2024-01-12" (UTC) to local time "Jan 12"
        events_per_day?.data.forEach((item: any) => {
          item.formated_date = new Date(item.date).toLocaleDateString([], {
            month: "short",
            day: "numeric",
          });
        });
        const unique_event_names = events_per_day?.unique_event_names;
        setEventLastSevenDays(events_per_day?.data);
        setUniqueEventNames(unique_event_names);
      });
    })();
  }, [project_id, loading]);

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
