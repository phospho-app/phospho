"use client";

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
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronDown } from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";
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

  const { accessToken, loading } = useUser();
  const hasTasks = dataStateStore((state) => state.hasTasks);
  const project_id = navigationStateStore((state) => state.project_id);

  const [selectedMetric, setSelectedMetric] = useState<string>("Nb tasks");
  const [selectedMetricMetadata, setSelectedMetricMetadata] = useState<
    string | null
  >(null);
  const [selectedGroupBy, setSelectedGroupBy] = useState<string>("flag");

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
  const { data: pivotData } = useSWR(
    [
      `/api/metadata/${project_id}/pivot/`,
      accessToken,
      selectedMetric,
      selectedMetricMetadata,
      selectedGroupBy,
      numberMetadataFields,
      categoryMetadataFields,
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metric: selectedMetric,
        metric_metadata: selectedMetricMetadata,
        breakdown_by: selectedGroupBy,
        number_metadata_fields: numberMetadataFields,
        category_metadata_fields: categoryMetadataFields,
      }).then((response) => {
        return response?.pivot_table;
      }),
    {
      keepPreviousData: true,
    },
    // {
    //   revalidateIfStale: false,
    //   revalidateOnFocus: false,
    //   revalidateOnReconnect: false,
    // }
  );

  return (
    <>
      <div className="flex flex-row space-x-2 items-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>
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
                      onClick={() => {
                        setSelectedMetric("Avg");
                        setSelectedMetricMetadata(field);
                      }}
                    >
                      {field}
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
            <Button>
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
                    <DropdownMenuItem onClick={() => setSelectedGroupBy(field)}>
                      {field}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuSubContent>
              </DropdownMenuPortal>
            </DropdownMenuSub>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div>
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
          <ResponsiveContainer width="100%" height={500}>
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
                        ? Math.round(payload[0].value * 10000) / 10000
                        : payload[0].value;
                    return (
                      <div className="bg-black text-white p-1">
                        <p>{`${selectedMetric} ${
                          selectedMetricMetadata ?? ""
                        } : ${formatedValue}`}</p>
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
            <p className="text-gray-500">
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
