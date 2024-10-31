"use client";

import { Spinner } from "@/components/small-spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { authFetcher } from "@/lib/fetcher";
import { graphColors } from "@/lib/utils";
import { DatavizSorting, Project, ProjectDataFilters } from "@/models/models";
import { navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import { ChevronRight, Download } from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";
import {
  Bar,
  BarChart,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CategoricalChartState } from "recharts/types/chart/types";
import {
  NameType,
  ValueType,
} from "recharts/types/component/DefaultTooltipContent";
import { Payload } from "recharts/types/component/DefaultTooltipContent";
import useSWRImmutable from "swr/immutable";

import DatavizTaggerGraph from "./dataviz-tagger";
import { Button } from "./ui/button";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "./ui/hover-card";

export interface PivotTableElement {
  breakdown_by: string;
  stack?: Record<string, string | number | null>;
  [key: string]:
    | string
    | number
    | null
    | Record<string, string | number | null>
    | undefined;
}

function pivotDataToCSV(pivotData: PivotTableElement[]) {
  console.log("pivotData", JSON.stringify(pivotData));

  const flattenedData = pivotData.map((row) => {
    // if the row is a stack, unnest it : {stack: {"Up-sell": 1}} => {"Up-sell": 1}
    if (row.stack && typeof row.stack === "object") {
      const stack = row.stack;
      const newRow = {
        ...row,
        ...(stack as Record<string, string | number | null>),
      };
      delete newRow.stack;
      return newRow;
    }
    return row;
  });

  // Create the CSV string
  // First, get the headers. Since we have stacks, we need to get all the keys of the stacks
  const headers = Array.from(
    new Set(
      flattenedData.reduce<string[]>((acc, row) => {
        const keys = Object.keys(row);
        return acc.concat(keys);
      }, []),
    ),
  );

  // Then, create the rows
  const rows = flattenedData.map((row) => {
    return headers.map((header) => {
      return row[header];
    });
  });

  // Create the CSV string
  let csv = headers.join(",") + "\n";
  csv += rows.map((row) => row.join(",")).join("\n");

  console.log("csv", csv);

  return csv;
}

const DatavizGraph = ({
  metric,
  metadata_metric,
  breakdown_by,
  scorer_id,
  sorting,
  filters,
}: {
  metric: string;
  metadata_metric?: string | null;
  breakdown_by: string;
  scorer_id: string | null;
  sorting?: DatavizSorting;
  filters?: ProjectDataFilters;
}) => {
  if (sorting === undefined) {
    sorting = {
      id: "breakdown_by",
      desc: false,
    };
  }

  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const dataFilters = navigationStateStore((state) => state.dataFilters);
  const router = useRouter();

  // TODO : Instead, the Filter component should delete keys when removing the filter
  // Right now, it sets the value to null. This is a workaround, but it should be fixed.
  const nonNullDataFilters = Object.fromEntries(
    Object.entries(dataFilters).filter(([, value]) => value !== null),
  );

  const mergedFilters = { ...filters, ...nonNullDataFilters };

  const { data: selectedProject }: { data: Project } = useSWRImmutable(
    project_id ? [`/api/projects/${project_id}`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "GET"),
    {
      keepPreviousData: true,
      refreshInterval: 0,
      refreshWhenHidden: false,
      revalidateOnReconnect: true,
      revalidateOnFocus: false,
      revalidateOnMount: true,
      refreshWhenOffline: false,
    },
  );

  if (!metadata_metric) {
    metadata_metric = "";
  }

  const { data } = useSWRImmutable(
    [`/api/metadata/${project_id}/fields`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      keepPreviousData: true,
      refreshInterval: 0,
      refreshWhenHidden: false,
      revalidateOnReconnect: true,
      revalidateOnFocus: false,
      revalidateOnMount: true,
      refreshWhenOffline: false,
    },
  );
  const numberMetadataFields: string[] | undefined = data?.number;
  const categoryMetadataFields: string[] | undefined = data?.string;

  const { data: pivotData, isLoading: pivotLoading } = useSWRImmutable(
    [
      `/api/metadata/${project_id}/pivot/`,
      accessToken,
      metric,
      metadata_metric,
      breakdown_by,
      scorer_id,
      JSON.stringify(mergedFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metric: metric.toLowerCase(),
        metric_metadata: metadata_metric?.toLowerCase(),
        breakdown_by:
          breakdown_by !== "None" ? breakdown_by.toLowerCase() : null,
        scorer_id: scorer_id,
        filters: mergedFilters,
      }).then((response) => {
        const pivotTable = response?.pivot_table as PivotTableElement[] | null;
        if (!pivotTable) {
          return [];
        }
        // Replace "breakdown_by": null with "breakdown_by": "None"
        pivotTable.forEach((element: PivotTableElement) => {
          if (element.breakdown_by === null) {
            element.breakdown_by = "None";
          }
        });

        return pivotTable;
      }),
    {
      keepPreviousData: true,
      refreshInterval: 0,
      refreshWhenHidden: false,
      revalidateOnReconnect: true,
      revalidateOnFocus: false,
      revalidateOnMount: true,
      refreshWhenOffline: false,
    },
  );

  const isStacked =
    pivotData && pivotData?.length > 1 && "stack" in pivotData[0];

  if (!numberMetadataFields || !categoryMetadataFields) {
    return <></>;
  }

  if (
    breakdown_by === "language" &&
    !categoryMetadataFields.includes("language")
  ) {
    return <></>;
  }

  if (
    metadata_metric === "sentiment_score" &&
    !numberMetadataFields.includes("sentiment_score")
  ) {
    return <></>;
  }

  if (pivotLoading) {
    return <Spinner className="my-40 mx-60" />;
  }

  const supportedDeepDives = [
    "language",
    "tagger_name",
    "scorer_value",
    "flag",
    "version_id",
    "session_id",
    "task_id",
    "user_id",
  ];

  const onChartClick = (nextState: CategoricalChartState) => {
    if (!nextState?.activeLabel) return;
    const formatedBreakdownBy = encodeURIComponent(nextState.activeLabel);
    if (breakdown_by === "language") {
      router.push(`/org/transcripts/tasks?language=${formatedBreakdownBy}`);
    }
    if (breakdown_by === "tagger_name") {
      router.push(`/org/transcripts/tasks?event_name=${formatedBreakdownBy}`);
    }
    if (breakdown_by === "flag") {
      router.push(`/org/transcripts/tasks?flag=${formatedBreakdownBy}`);
    }
    if (breakdown_by === "version_id") {
      router.push(`/org/ab-testing/${formatedBreakdownBy}`);
    }
    if (breakdown_by === "session_id") {
      router.push(`/org/transcripts/sessions/${formatedBreakdownBy}`);
    }
    if (breakdown_by === "task_id") {
      router.push(`/org/transcripts/tasks/${formatedBreakdownBy}`);
    }
    if (breakdown_by === "user_id") {
      router.push(`/org/transcripts/users/${formatedBreakdownBy}`);
    }
  };

  const timeChart = ["day", "week", "month"].includes(breakdown_by);

  // Sort the pivot table according to the sorting
  if (pivotData) {
    if (sorting !== undefined && sorting.id === "breakdown_by") {
      pivotData.sort((a, b) => {
        if (sorting === undefined) return -1;
        if (sorting.desc) {
          return a.breakdown_by > b.breakdown_by ? -1 : 1;
        } else {
          return a.breakdown_by < b.breakdown_by ? -1 : 1;
        }
      });
    }
    if (sorting !== undefined && sorting.id === "metric") {
      pivotData.sort((a, b) => {
        if (sorting === undefined) return -1;
        if (a?.metric === null) return -1;
        if (b?.metric === null) return -1;
        if (sorting.desc) {
          return (a.metric as number) > (b.metric as number) ? -1 : 1;
        } else {
          return (a.metric as number) < (b.metric as number) ? -1 : 1;
        }
      });
    }
  }

  return (
    <>
      {pivotData && (
        <div className="w-full flex justify-end mb-2">
          <HoverCard openDelay={0} closeDelay={0}>
            <HoverCardTrigger asChild>
              <Button
                size="icon"
                variant="ghost"
                onClick={() => {
                  const csv = pivotDataToCSV(pivotData);
                  const blob = new Blob([csv], { type: "text/csv" });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "data.csv";
                  a.click();
                }}
              >
                <Download className="size-4" />
              </Button>
            </HoverCardTrigger>
            <HoverCardContent className="text-xs">
              Download as CSV
            </HoverCardContent>
          </HoverCard>
        </div>
      )}
      {(pivotData === null || pivotData?.length == 0) && <>No data</>}
      {pivotData?.length == 1 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl font-light tracking-tight">
                {pivotData[0]["breakdown_by"] !== "None" && (
                  <p>
                    {breakdown_by}: {pivotData[0]["breakdown_by"]}
                  </p>
                )}
                {pivotData[0]["breakdown_by"] === "None" && <p>No breakdown</p>}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xl font-extrabold">
              {typeof pivotData[0].metric === "number" && (
                <span>{Math.round(pivotData[0].metric * 10000) / 10000}</span>
              )}
            </CardContent>
          </Card>
        </>
      )}
      {pivotData && pivotData?.length > 1 && (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={pivotData}
            layout={timeChart ? "horizontal" : "vertical"}
            margin={{
              top: 0,
              right: 0,
              bottom: 0,
              left: 0,
            }}
            onClick={onChartClick}
          >
            <Tooltip
              formatter={(value) => {
                if (typeof value === "string") return value;
                if (typeof value === "number")
                  return `${Math.round(value * 100) / 100}`;
              }}
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-primary shadow-md p-2 rounded-md space-y-1">
                      <div className="text-secondary font-semibold">{`${breakdown_by}: ${label}`}</div>
                      <div>
                        {payload.map((item: Payload<ValueType, NameType>) => {
                          const itemName =
                            item.name && item.name.toString().split(".")[1]
                              ? item.name.toString().split(".")[1]
                              : item.name;
                          const formatedValue =
                            typeof item.value === "number"
                              ? Math.round(item.value * 1000) / 1000
                              : item.value;

                          // Get the color of the bar
                          let index = 0;
                          if (isStacked) {
                            // use Object.keys(selectedProject?.settings?.events to get the index color
                            index = Object.keys(
                              selectedProject?.settings?.events ?? {},
                            ).indexOf(
                              item.name?.toString().split(".")[1] ?? "",
                            );
                          }
                          const color = graphColors[index % graphColors.length];

                          return (
                            <div key={item.name}>
                              <div className="flex flex-row space-x-2 items-center">
                                {/* A small square with the color of the bar (legend)*/}
                                <div
                                  className="w-4 h-4"
                                  style={{ backgroundColor: color }}
                                ></div>

                                {/* The name of the item and its value */}
                                <div className="text-secondary">
                                  {itemName}: {formatedValue}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                        {breakdown_by === "tagger_name" && (
                          <DatavizTaggerGraph
                            tagger_name={label}
                            metric={metric}
                            metadata_metric={metadata_metric}
                            breakdown_by={breakdown_by}
                            scorer_id={scorer_id}
                          />
                        )}
                        <div className="pt-4">
                          {supportedDeepDives.includes(breakdown_by) && (
                            <div className="flex flex-row items-center text-xs text-secondary">
                              <ChevronRight className="size-4" />
                              Click to see all
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                }
              }}
            />
            {!timeChart && (
              <>
                <YAxis
                  dataKey={"breakdown_by"}
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  type="category"
                  tickFormatter={(value: string) => {
                    // if value is a string and is too long, truncate it
                    if (value.length > 30) {
                      return value.slice(0, 30) + "...";
                    }
                    return value;
                  }}
                  width={100}
                />
                <XAxis
                  fontSize={12}
                  type="number"
                  domain={[0, "dataMax + 1"]}
                  tickFormatter={(value) => `${Math.round(value * 100) / 100}`}
                />
              </>
            )}
            {timeChart && (
              <>
                <XAxis
                  dataKey={"breakdown_by"}
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  type="category"
                  tickFormatter={(value: string) => {
                    // if value is a string and is too long, truncate it
                    if (value.length > 30) {
                      return value.slice(0, 30) + "...";
                    }
                    return value;
                  }}
                  width={100}
                />
                <YAxis
                  fontSize={12}
                  type="number"
                  domain={[0, "dataMax + 1"]}
                  tickFormatter={(value) => `${Math.round(value * 100) / 100}`}
                />
              </>
            )}
            {!isStacked && (
              <Bar
                dataKey={"metric"}
                fill="#22c55e"
                stackId="a"
                // radius={[0, 20, 20, 0]}
              >
                <LabelList
                  dataKey="metric"
                  position="right"
                  className="text-secondary"
                  fontSize={12}
                  formatter={(value: number) => {
                    return value;
                  }}
                />
              </Bar>
            )}
            {isStacked &&
              // Loop over the keys of the dict and create a bar for each key
              Object.keys(selectedProject?.settings?.events ?? {}).map(
                (key, index) => {
                  return (
                    <Bar
                      key={key}
                      dataKey={`stack.${key}`}
                      fill={graphColors[index % graphColors.length]}
                      stackId="a"
                      // radius={[0, 20, 20, 0]}
                    />
                  );
                },
              )}
          </BarChart>
        </ResponsiveContainer>
      )}
    </>
  );
};

export default DatavizGraph;
