"use client"

import { useState, useEffect, useMemo } from 'react';
import React from 'react';
import { ResponsiveContainer, BarChart, XAxis, YAxis, Tooltip, Bar, CartesianGrid } from 'recharts';
import { useUser } from "@propelauth/nextjs/client";

import { ChartConfig, ChartContainer } from "@/components/ui/chart"
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import {
  Card,
  CardTitle,
  CardContent,
  CardDescription,
  CardHeader,
  CardFooter,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface AnalyticsQueryFilters {
  created_at_start?: number; // UNIX timestamp in seconds
  created_at_end?: number; // UNIX timestamp in seconds
  raw_filters?: Record<string, any>; // Raw filters to be passed to the MongoDB query
}

type AnalyticsQuery = {
  project_id: string;
  collection: string;
  aggregation_operation: string;
  aggregation_field?: string;
  dimensions?: string[];
  filters?: AnalyticsQueryFilters;
  sort?: Record<string, number>;
  limit?: number;
  filter_out_null_values?: boolean;
  filter_out_null_dimensions?: boolean;
};

type DatavizParams = {
  analyticsQuery: AnalyticsQuery;
  xField: string; // Field to be used on the x-axis
  yFields: string[]; // Fields to be used on the y-axis
  chartType: string; // line, bar, pie, etc.
  title: string;
  subtitle: string;
  // showTotal: boolean; // Show total value in the chart
};

const CustomTooltipNbrTasks = () => {
  // Implement your custom tooltip component here
  return null;
};

const ChartContent: React.FC<{ data: any[], xField: string, keys: string[] }> = ({ data, xField, keys }) => {
  // Generate the colors for the chart
  const colors = ["#2563eb", "#f66d9b", "#f6ad55", "#10b759", "#6c5ce7", "#ff6b6b", "#48dbfb", "#feca57"];
  // pass it to the config
  const config = {
    desktop: {
    }
  } satisfies ChartConfig
  return (
    <ChartContainer config={config} className="min-h-[200px] w-full">
      <BarChart accessibilityLayer data={data}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey={xField}
          tickLine={false}
          tickMargin={10}
          axisLine={false}
          tickFormatter={(value) => value.slice(0, 3)}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        {keys.map((key, index) => (
          <Bar key={key} dataKey={key} stackId="a" fill={colors[index % colors.length]} />
        ))}
      </BarChart>
    </ChartContainer>
  );
};

const GenericDataviz: React.FC<DatavizParams> = ({ analyticsQuery, xField, yFields, chartType, title, subtitle }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const { accessToken } = useUser();

  const chartConfig = {
    desktop: {
      label: yFields[0],
      color: "#2563eb",
    }
  } satisfies ChartConfig

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/explore/analytics-query?asFilledTimeSeries=True", {
          method: "POST",
          headers: {
            Authorization: "Bearer " + accessToken,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(analyticsQuery),
        });
        const data = await response.json();
        setData(data.result);
        setLoading(false);
        console.log("Data fetched:", data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, [analyticsQuery, accessToken]);

  const keys = useMemo(() => {
    if (!data || data.length === 0) return [];
    return Object.keys(data[0]).filter(key => key !== 'day');
  }, [data]);

  console.log('keys', keys);

  return (
    <>
      <Card className='max-w-[500px] mx-auto'>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{subtitle}</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="min-h-[200px] w-full" />
          ) : (
            <ChartContent data={data} xField={xField} keys={keys} />
          )}
        </CardContent>
      </Card>
    </>
  );
}

export default GenericDataviz;