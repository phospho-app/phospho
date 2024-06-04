"use client";

import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronDown } from "lucide-react";
import Link from "next/link";
import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

const MetadataForm: React.FC<{}> = ({}) => {
  // create a page with 2 dropdowns :
  // 1. Metric: count of tasks, avg session length, sum of a metadata field,
  // 2. Groupby field : None ; metadataField (user_id, version_id, etc. ) ; event_name ; flag

  // The data is fetched and then displayed as a bar chart or a table

  const { toast } = useToast();

  const { accessToken, loading } = useUser();
  const hasTasks = dataStateStore((state) => state.hasTasks);
  const project_id = navigationStateStore((state) => state.project_id);

  const selectedMetric = navigationStateStore((state) => state.selectedMetric);
  const selectedMetricMetadata = navigationStateStore(
    (state) => state.selectedMetricMetadata,
  );
  const selectedGroupBy = navigationStateStore(
    (state) => state.selectedGroupBy,
  );
  const setSelectedMetric = navigationStateStore(
    (state) => state.setSelectedMetric,
  );
  const setSelectedMetricMetadata = navigationStateStore(
    (state) => state.setSelectedMetricMetadata,
  );
  const setSelectedGroupBy = navigationStateStore(
    (state) => state.setSelectedGroupBy,
  );

  const dataFilters = navigationStateStore((state) => state.dataFilters);

  // Fetch metadata unique metadata fields from the API
  const { data } = useSWR(
    [`/api/metadata/${project_id}/fields`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      revalidateIfStale: false,
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );
  const numberMetadataFields: string[] | undefined = data?.number;
  const categoryMetadataFields: string[] | undefined = data?.string;

  // Fetch aggregated metrics from the API
  const { data: pivotData, isLoading: pivotLoading } = useSWR(
    [
      `/api/metadata/${project_id}/pivot/`,
      accessToken,
      selectedMetric,
      selectedMetricMetadata,
      selectedGroupBy,
      numberMetadataFields,
      categoryMetadataFields,
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metric: selectedMetric,
        metric_metadata: selectedMetricMetadata,
        breakdown_by: selectedGroupBy,
        number_metadata_fields: numberMetadataFields,
        category_metadata_fields: categoryMetadataFields,
        filters: dataFilters,
      }).then((response) => {
        return response?.pivot_table;
      }),
    {
      keepPreviousData: true,
    },
  );

  return (
    <>
      <div className="flex flex-col space-y-2">
        <div className="flex flex-row space-x-2 items-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Metric: {selectedMetric} {selectedMetricMetadata ?? ""}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Nb tasks");
                  setSelectedMetricMetadata(null);
                }}
              >
                Nb tasks
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Avg session length");
                  setSelectedMetricMetadata(null);
                }}
              >
                Avg session length
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Avg Success rate");
                  setSelectedMetricMetadata(null);
                }}
              >
                Success rate
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>Avg of metadata</DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {numberMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No numeric metadata found
                      </DropdownMenuItem>
                    )}
                    {numberMetadataFields?.map((field) => (
                      // TODO : Add a way to indicate this is a sum
                      <DropdownMenuItem
                        key={field}
                        onClick={() => {
                          setSelectedMetric("Avg");
                          setSelectedMetricMetadata(field);
                        }}
                      >
                        {`${field}_avg`}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>Sum of metadata</DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {numberMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No numeric metadata found
                      </DropdownMenuItem>
                    )}
                    {numberMetadataFields?.map((field) => (
                      // TODO : Add a way to indicate this is a sum
                      <DropdownMenuItem
                        onClick={() => {
                          setSelectedMetric("Sum");
                          setSelectedMetricMetadata(field);
                        }}
                        key={`${field}_sum`}
                      >
                        {field}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Breakdown by: {selectedGroupBy}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("None");
                }}
              >
                None
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("event_name");
                }}
              >
                event_name
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("flag");
                }}
              >
                flag
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("task_position");
                }}
              >
                task_position
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>metadata</DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {categoryMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No categorical metadata found
                      </DropdownMenuItem>
                    )}
                    {categoryMetadataFields?.map((field) => (
                      <DropdownMenuItem
                        onClick={() => setSelectedGroupBy(field)}
                        key={`${field}_metadata`}
                      >
                        {field}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <div className="flex flex-row space-x-2 items-center">
          <DatePickerWithRange />
          <FilterComponent variant="tasks" />
        </div>
      </div>
      <div className="w-full h-screen max-h-3/4">
        {!pivotData && pivotLoading && <p>Loading...</p>}
        {(pivotData === null || pivotData?.length == 0) && (
          <p>No data matching your query</p>
        )}
        {pivotData?.length == 1 && (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-light tracking-tight">
                  Breakdown by {selectedGroupBy}:{" "}
                  {pivotData[selectedGroupBy] ?? "None"}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-extrabold">
                <p>
                  {Math.round(
                    pivotData[0][
                      `${selectedMetric}${selectedMetricMetadata ?? ""}`
                    ] * 10000,
                  ) / 10000}
                </p>
              </CardContent>
            </Card>
          </>
        )}
        {pivotData?.length > 1 && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={pivotData}
              layout="vertical"
              margin={{
                top: 20,
                right: 100,
                bottom: 20,
                left: 100,
              }}
            >
              <CartesianGrid />
              <YAxis
                dataKey={selectedGroupBy}
                stroke="#888888"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                type="category"
                tickFormatter={(value: any) => {
                  // if value is a string and is too long, truncate it
                  if (typeof value === "string" && value.length > 30) {
                    return value.slice(0, 30) + "...";
                  }
                  return value;
                }}
                width={150}
              />
              <XAxis
                stroke="#888888"
                fontSize={12}
                type="number"
                domain={[0, "dataMax + 1"]}
                // tickLine={false}
                // axisLine={false}
                tickFormatter={(value) => `${Math.round(value * 100) / 100}`}
              />
              <Bar
                dataKey={`${selectedMetric}${selectedMetricMetadata ?? ""}`}
                fill="#22c55e"
                radius={[0, 20, 20, 0]}
                onClick={(data) => {
                  // Copy the Y value to the clipboard
                  navigator.clipboard.writeText(data[selectedGroupBy]);
                  toast({
                    title: "Copied to clipboard",
                    description: data[selectedGroupBy],
                  });
                }}
              />
              <Tooltip
                formatter={(value) => {
                  if (typeof value === "string") return value;
                  if (typeof value === "number")
                    return `${Math.round(value * 100) / 100}`;
                }}
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const formatedValue =
                      typeof payload[0].value === "number"
                        ? Math.round(payload[0].value * 1000) / 1000
                        : payload[0].value;
                    return (
                      <div className="bg-primary shadow-md p-2 rounded-md">
                        <p className="text-secondary font-semibold">{`${label}`}</p>
                        <p className="text-green-500">
                          {payload.map((item: any) => {
                            return (
                              <p key={item.name}>
                                {item.name}: {formatedValue}
                              </p>
                            );
                          })}
                        </p>
                      </div>
                    );
                  }
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {hasTasks === false && (
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl font-bold tracking-tight">
              Here is where you'd analyze your tasks. If you logged some.
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Start logging tasks to get the most out of Phospho. Pass metadata
              to get custom insights.
            </p>
            <div className="flex flex-col justify-center items-center m-2">
              <Link
                href="https://docs.phospho.ai/getting-started"
                target="_blank"
              >
                <Button variant="default">Get started</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
};

export default MetadataForm;
