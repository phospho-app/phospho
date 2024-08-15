"use client"

import { useState, useEffect, useMemo } from 'react';
import React from 'react';
import { ResponsiveContainer, Pie, PieChart, Line, LineChart, BarChart, XAxis, YAxis, Tooltip, Bar, CartesianGrid } from 'recharts';
import { useUser } from "@propelauth/nextjs/client";

import { ChartConfig, ChartContainer } from "@/components/ui/chart"
import { ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton";
import {
  AnalyticsQuery,
} from "@/models/models";
import { authFetcher } from "@/lib/fetcher";
import useSWR from 'swr';


type DatavizParams = {
  analyticsQuery: AnalyticsQuery;
  asFilledTimeSeries?: boolean; // If true, the chart will be displayed as a filled time serie
  xField: string; // Field to be used on the x-axis
  yFields: string[]; // Fields to be used on the y-axis
  chartType: string; // line, bar, pie, etc.
  // showTotal: boolean; // Show total value in the chart
};

const CustomTooltipNbrTasks = () => {
  // Implement your custom tooltip component here
  return null;
};

const colors = ["#22c55e", "#f66d9b", "#f6ad55", "#10b759", "#6c5ce7", "#ff6b6b", "#48dbfb", "#feca57"];

const BarChartViz: React.FC<{ data: any[], xField: string, keys: string[] }> = ({ data, xField, keys }) => {
  // Generate the colors for the chart
  // pass it to the config
  const config = {
    desktop: {
    }
  } satisfies ChartConfig
  return (
    <ChartContainer config={config} className="w-full h-full">
      <BarChart accessibilityLayer data={data}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey={xField}
          tick={false}
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

const LineChartViz: React.FC<{ data: any[], xField: string, keys: string[] }> = ({ data, xField, keys }) => {
  // pass it to the config
  const config = {
    desktop: {
    }
  } satisfies ChartConfig
  return (
    <ChartContainer config={config} className="w-full h-full">
      <LineChart accessibilityLayer data={data}>
        <CartesianGrid vertical={false} />
        <XAxis
          dataKey={xField}
          tickLine={false}
          tick={false}
          tickMargin={10}
          axisLine={false}
          tickFormatter={(value) => value.slice(0, 3)}
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        {keys.map((key, index) => (
          <Line
            dataKey={key}
            type="monotone"
            stroke={colors[index % colors.length]}
            strokeWidth={2}
            dot={false} />
        ))}
      </LineChart>
    </ChartContainer>
  );
};

const PieChartViz: React.FC<{ data: any[], xField: string, yField: string }> = ({ data, xField, yField }) => {

  // pass it to the config
  const config = {
    desktop: {
    }
  } satisfies ChartConfig

  // Generate a chartData object by addding the fill var to the data
  // Example
  // const chartData = [
  //   { browser: "chrome", visitors: 275, fill: "var(--color-chrome)" },
  //   { browser: "safari", visitors: 200, fill: "var(--color-safari)" },
  //   { browser: "firefox", visitors: 187, fill: "var(--color-firefox)" },
  //   { browser: "edge", visitors: 173, fill: "var(--color-edge)" },
  //   { browser: "other", visitors: 90, fill: "var(--color-other)" },
  // ];

  // We add a field fill to the data with a random color
  const dataWithFill = data.map((item, index) => {
    return {
      ...item,
      fill: colors[index % colors.length]
    }
  });

  return (

    <ChartContainer
      config={config}
      className="w-full h-full"
    >
      <PieChart>
        <ChartTooltip
          cursor={false}
          content={<ChartTooltipContent hideLabel />}
        />
        <Pie
          data={dataWithFill}
          dataKey={yField}
          nameKey={xField}
          innerRadius="50%"
          outerRadius="70%"
        />
      </PieChart>
    </ChartContainer >
  );
};

const GenericDataviz: React.FC<DatavizParams> = ({ analyticsQuery, asFilledTimeSeries, xField, yFields, chartType }) => {
  const [oldData, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const { accessToken } = useUser();

  const chartConfig = {
    desktop: {
      label: yFields[0],
      color: "#FFFFFF",
    }
  } satisfies ChartConfig

  const queryParams = asFilledTimeSeries ? '?asFilledTimeSeries=True' : '';
  const url = `/api/explore/analytics-query${queryParams}`;

  const { data, error } = useSWR(
    accessToken ? [url, accessToken, analyticsQuery] : null,
    ([url, token, query]) => authFetcher(url, token, "POST", query)
  );

  const keys = useMemo(() => {
    if (!data?.result || data.result.length === 0) return [];
    return Object.keys(data.result[0]).filter((key) => key !== 'day');
  }, [data]);

  if (error) return <div className='text-muted'>error</div>;
  if (!data) return <Skeleton className="w-full" />;

  const chartData = data.result;

  return (
    <div>
      {chartType === "stackedBar" ? (
        <ResponsiveContainer width="100%" height="100%">
          <BarChartViz data={chartData} xField={xField} keys={keys} />
        </ResponsiveContainer>
      ) : chartType === "line" ? (
        <ResponsiveContainer width="100%" height="100%">
          <LineChartViz data={chartData} xField={xField} keys={keys} />
        </ResponsiveContainer>
      ) : chartType === "pie" ? (
        <ResponsiveContainer width="100%" height="100%">
          <PieChartViz data={chartData} xField={xField} yField={yFields[0]} />
        </ResponsiveContainer>
      ) : null}
    </div >
  );
}

export default GenericDataviz;